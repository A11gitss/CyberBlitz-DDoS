from faker import Faker
from fake_useragent import UserAgent, FakeUserAgentError
import random
import string
import re
import time
from config import CONFIG, logger

# --- Singleton instance for UserAgent ---
ua_instance = None

def init_user_agent(verify_ssl=True):
    """Initializes the UserAgent instance."""
    global ua_instance
    if ua_instance is None:
        try:
            ua_instance = UserAgent(browsers=["chrome", "firefox", "safari", "edge", "opera"], verify_ssl=verify_ssl)
        except Exception:
            logger.warning("Could not get the latest UserAgent list. Using fallback.")
            ua_instance = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")

# Расширенные профили браузеров с поддержкой более широкого набора устройств и настроек
BROWSER_PROFILES = {
    "Windows": {
        "Chrome": {
            "sec_ch_ua_template": '"Not/A)Brand";v="99", "Google Chrome";v="{major_version}", "Chromium";v="{major_version}"',
            "sec_ch_ua_platform": '"Windows"',
            "mobile": False,
            "weight": 0.45  # 45% market share
        },
        "Firefox": {
            "sec_ch_ua_template": '"Firefox";v="{major_version}"',
            "sec_ch_ua_platform": '"Windows"',
            "mobile": False,
            "weight": 0.25  # 25% market share
        },
        "Edge": {
            "sec_ch_ua_template": '"Microsoft Edge";v="{major_version}", "Chromium";v="{major_version}"',
            "sec_ch_ua_platform": '"Windows"',
            "mobile": False,
            "weight": 0.15  # 15% market share
        }
    },
    "macOS": {
        "Chrome": {
            "sec_ch_ua_template": '"Not/A)Brand";v="99", "Google Chrome";v="{major_version}", "Chromium";v="{major_version}"',
            "sec_ch_ua_platform": '"macOS"',
            "mobile": False,
            "weight": 0.35
        },
        "Safari": {
            "sec_ch_ua_template": '"Safari";v="{major_version}"',
            "sec_ch_ua_platform": '"macOS"',
            "mobile": False,
            "weight": 0.45
        },
        "Firefox": {
            "sec_ch_ua_template": '"Firefox";v="{major_version}"',
            "sec_ch_ua_platform": '"macOS"',
            "mobile": False,
            "weight": 0.20
        }
    },
    "Linux": {
        "Chrome": {
            "sec_ch_ua_template": '"Not/A)Brand";v="99", "Google Chrome";v="{major_version}", "Chromium";v="{major_version}"',
            "sec_ch_ua_platform": '"Linux"',
            "mobile": False,
            "weight": 0.50
        },
        "Firefox": {
            "sec_ch_ua_template": '"Firefox";v="{major_version}"',
            "sec_ch_ua_platform": '"Linux"',
            "mobile": False,
            "weight": 0.45
        }
    },
    "iOS": {
        "Safari": {
            "sec_ch_ua_template": '"Safari";v="{major_version}"',
            "sec_ch_ua_platform": '"iOS"',
            "mobile": True,
            "weight": 0.90
        },
        "Chrome": {
            "sec_ch_ua_template": '"Not/A)Brand";v="99", "Google Chrome";v="{major_version}", "Chromium";v="{major_version}"',
            "sec_ch_ua_platform": '"iOS"',
            "mobile": True,
            "weight": 0.10
        }
    },
    "Android": {
        "Chrome": {
            "sec_ch_ua_template": '"Not/A)Brand";v="99", "Google Chrome";v="{major_version}", "Chromium";v="{major_version}"',
            "sec_ch_ua_platform": '"Android"',
            "mobile": True,
            "weight": 0.70
        },
        "Firefox": {
            "sec_ch_ua_template": '"Firefox";v="{major_version}"',
            "sec_ch_ua_platform": '"Android"',
            "mobile": True,
            "weight": 0.15
        },
        "Samsung": {
            "sec_ch_ua_template": '"Samsung Internet";v="{major_version}"',
            "sec_ch_ua_platform": '"Android"',
            "mobile": True,
            "weight": 0.15
        }
    }
}

class BrowserProfile:
    def __init__(self):
        self.fake = Faker()
        self.ua = ua_instance

        spoof_config = CONFIG.get("spoofing", {})
        
        # Выбор OS и браузера с учетом матрицы и весов
        allowed_combos = []
        weights = []
        
        for os, browsers in spoof_config.get("ua_matrix", {}).items():
            if os not in BROWSER_PROFILES:
                continue
            for browser, allowed in browsers.items():
                if allowed and browser in BROWSER_PROFILES[os]:
                    allowed_combos.append((os, browser))
                    weights.append(BROWSER_PROFILES[os][browser]["weight"])

        if not allowed_combos:
            logger.warning("В матрице User-Agent не выбрано ни одной комбинации. Используется Windows/Chrome по умолчанию.")
            self.os, self.browser = "Windows", "Chrome"
        else:
            # Нормализация весов
            total_weight = sum(weights)
            weights = [w/total_weight for w in weights]
            self.os, self.browser = random.choices(allowed_combos, weights=weights)[0]

        profile_data = BROWSER_PROFILES[self.os][self.browser]
        
        # Генерация User-Agent с помощью fake_useragent
        if self.ua:
            try:
                if self.browser.lower() in ["chrome", "firefox", "safari", "edge", "opera"]:
                    self.user_agent = getattr(self.ua, self.browser.lower())
                else:
                    self.user_agent = self.ua.random
                    
                # Извлечение версии из сгенерированного UA
                version_match = re.search(r"(?:Chrome|Firefox|Safari|Edge|Opera)[/\s](\d+)", self.user_agent)
                self.major_version = version_match.group(1) if version_match else "100"
            except Exception as e:
                logger.warning(f"Ошибка при генерации UA через fake_useragent: {e}")
                self.user_agent = self.ua.random
                self.major_version = "100"
        else:
            # Фоллбэк на базовый User-Agent если не удалось использовать fake_useragent
            self.user_agent = self._generate_fallback_ua()
            self.major_version = "100"

        # Расширенные нас��ройки браузера
        self.language = random.choice(spoof_config.get("language_pool", ["en-US,en;q=0.9", "en-GB,en;q=0.8", "ru-RU,ru;q=0.9"]))
        self.timezone = random.choice(spoof_config.get("timezone_pool", ["America/New_York", "Europe/London", "Europe/Moscow"]))
        
        # Реалистичные разрешения экрана с учетом типа устройства
        if profile_data.get("mobile", False):
            screen_resolutions = ["375x812", "414x896", "360x800", "390x844"]  # Популярные мобильные разрешения
        else:
            screen_resolutions = ["1920x1080", "2560x1440", "1366x768", "1440x900", "3840x2160"]
            
        screen_res = random.choice(spoof_config.get("screen_size_pool", screen_resolutions))
        width, height = map(int, screen_res.split('x'))
        self.screen = {"width": width, "height": height}
        
        # Умная генерация реферера на основе типа браузера
        if spoof_config.get("smart_referer", True):
            self.referer = self._generate_smart_referer()
        else:
            self.referer = random.choice(spoof_config.get("referer_pool", ["https://google.com/"]))

        # Настройки безопасности и совместимости
        self.sec_ch_ua = profile_data.get("sec_ch_ua_template", "").format(major_version=self.major_version)
        self.sec_ch_ua_mobile = "?1" if profile_data.get("mobile", False) else "?0"
        self.sec_ch_ua_platform = profile_data.get("sec_ch_ua_platform", f'"{self.os}"')

    def _generate_fallback_ua(self):
        """Генерация базового User-Agent если fake_useragent недоступен"""
        os_info = {
            "Windows": "Windows NT 10.0; Win64; x64",
            "macOS": "Macintosh; Intel Mac OS X 10_15_7",
            "Linux": "X11; Linux x86_64",
            "iOS": "iPhone; CPU iPhone OS 15_0 like Mac OS X",
            "Android": "Linux; Android 12; SM-G998B"
        }
        
        browser_info = {
            "Chrome": f"Chrome/{random.randint(90, 120)}.0.0.0 Safari/537.36",
            "Firefox": f"Firefox/{random.randint(90, 120)}.0",
            "Safari": "Version/15.0 Safari/605.1.15",
            "Edge": f"Edg/{random.randint(90, 120)}.0.0.0",
            "Samsung": f"SamsungBrowser/{random.randint(15, 20)}.0"
        }
        
        base = f"Mozilla/5.0 ({os_info.get(self.os, os_info['Windows'])})"
        if self.browser in ["Chrome", "Edge"]:
            base += f" AppleWebKit/537.36 (KHTML, like Gecko) {browser_info[self.browser]}"
        elif self.browser == "Firefox":
            base += f" Gecko/20100101 {browser_info[self.browser]}"
        elif self.browser == "Safari":
            base += f" AppleWebKit/605.1.15 (KHTML, like Gecko) {browser_info[self.browser]}"
        
        return base
    
    def _generate_smart_referer(self):
        """Умная генерация реферера на основе контекста"""
        search_engines = [
            "https://www.google.com/search?q=",
            "https://www.bing.com/search?q=",
            "https://duckduckgo.com/?q=",
            "https://yandex.ru/search/?text="
        ]
        social_media = [
            "https://www.facebook.com/",
            "https://twitter.com/",
            "https://www.linkedin.com/",
            "https://www.instagram.com/"
        ]
        news_sites = [
            "https://www.bbc.com/",
            "https://www.cnn.com/",
            "https://www.reuters.com/"
        ]
        
        referer_type = random.choices(
            ["search", "social", "news", "direct"],
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]
        
        if referer_type == "search":
            return random.choice(search_engines) + self.fake.word()
        elif referer_type == "social":
            return random.choice(social_media) + self.fake.user_name()
        elif referer_type == "news":
            return random.choice(news_sites) + self.fake.slug()
        else:
            return ""  # Прямой переход
    
    def _generate_accept_headers(self):
        """Генерация реалистичных accept-заголовков"""
        accept_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": self.language,
            "cache-control": random.choice(["max-age=0", "no-cache", "no-store"]),
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": random.choice(["none", "same-origin", "cross-site"]),
            "sec-fetch-user": "?1"
        }
        
        if random.random() < 0.7:  # 70% шанс добавления DNT
            accept_headers["dnt"] = "1"
            
        return accept_headers
    
    def get_headers(self):
        """Генерация полного набора реалистичных заголовков"""
        spoof_config = CONFIG.get("spoofing", {})
        
        # Базовые заголовки
        headers = {
            "user-agent": self.user_agent,
            **self._generate_accept_headers()
        }
        
        # Референс
        if self.referer:
            headers["referer"] = self.referer
            headers["sec-fetch-site"] = "cross-site"
        
        # Заголовки безопасности для современных браузеров
        if self.browser in ["Chrome", "Edge", "Safari"]:
            headers.update({
                "sec-ch-ua": self.sec_ch_ua,
                "sec-ch-ua-mobile": self.sec_ch_ua_mobile,
                "sec-ch-ua-platform": self.sec_ch_ua_platform,
                "upgrade-insecure-requests": "1"
            })
        
        # Дополнительные заголовки прокси и безопасности
        if spoof_config.get("x_forwarded_for"):
            headers["x-forwarded-for"] = spoof_config["x_forwarded_for"]
            headers["x-real-ip"] = spoof_config["x_forwarded_for"]
            
        if spoof_config.get("auth_token"):
            headers["authorization"] = spoof_config["auth_token"]
        
        # Эмуляция мобильных устройств
        if BROWSER_PROFILES[self.os][self.browser].get("mobile", False):
            headers["x-requested-with"] = "XMLHttpRequest"
            if self.browser == "Chrome":
                headers["chrome-mobile"] = "true"
                
        return headers

    def get_cookies(self):
        """Генерация реалистичных cookies"""
        spoof_config = CONFIG.get("spoofing", {})
        cookies = {}
        
        # Базовые куки для аналитики
        if random.random() < 0.9:  # 90% шанс наличия базовых куки
            cookies.update({
                "_ga": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time() - random.randint(1000000, 9999999))}",
                "_gid": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
                "__cfduid": f"d{self.fake.sha1(raw_output=False)[:27]}",
                "session": self.fake.sha256(raw_output=False)[:32]
            })
        
        # Куки для локализации
        if random.random() < 0.7:  # 70% шанс
            lang = self.language.split(",")[0].replace("-", "_")
            cookies["lang"] = lang
            cookies["locale"] = lang
        
        # Куки для предпочтений темы
        if random.random() < 0.3:  # 30% шанс
            cookies["theme"] = random.choice(["light", "dark", "auto"])
        
        # Куки для мобильной версии
        if BROWSER_PROFILES[self.os][self.browser].get("mobile", False):
            cookies["mobile_view"] = "1"
            cookies["app_version"] = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        # Пользовательские куки из конфига
        if spoof_config.get("custom_cookies"):
            cookies.update(spoof_config["custom_cookies"])
            
        if spoof_config.get("session_id"):
            try:
                key, value = spoof_config["session_id"].split('=', 1)
                cookies[key.strip()] = value.strip()
            except ValueError:
                cookies["custom_session"] = spoof_config["session_id"]
        return cookies

    def get_playwright_fingerprint(self):
        return {
            "locale": self.language.split(',')[0],
            "timezone_id": self.timezone,
            "viewport": self.screen
        }

