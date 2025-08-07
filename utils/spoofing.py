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
            "weight": 0.45
        },
        "Firefox": { "sec_ch_ua_template": '"Firefox";v="{major_version}"', "sec_ch_ua_platform": '"Windows"', "mobile": False, "weight": 0.25 },
        "Edge": { "sec_ch_ua_template": '"Microsoft Edge";v="{major_version}", "Chromium";v="{major_version}"', "sec_ch_ua_platform": '"Windows"', "mobile": False, "weight": 0.15 }
    },
    "macOS": {
        "Chrome": { "sec_ch_ua_template": '"Not/A)Brand";v="99", "Google Chrome";v="{major_version}", "Chromium";v="{major_version}"', "sec_ch_ua_platform": '"macOS"', "mobile": False, "weight": 0.35 },
        "Safari": { "sec_ch_ua_template": '"Safari";v="{major_version}"', "sec_ch_ua_platform": '"macOS"', "mobile": False, "weight": 0.45 },
        "Firefox": { "sec_ch_ua_template": '"Firefox";v="{major_version}"', "sec_ch_ua_platform": '"macOS"', "mobile": False, "weight": 0.20 }
    },
    "Linux": {
        "Chrome": { "sec_ch_ua_template": '"Not/A)Brand";v="99", "Google Chrome";v="{major_version}", "Chromium";v="{major_version}"', "sec_ch_ua_platform": '"Linux"', "mobile": False, "weight": 0.50 },
        "Firefox": { "sec_ch_ua_template": '"Firefox";v="{major_version}"', "sec_ch_ua_platform": '"Linux"', "mobile": False, "weight": 0.45 }
    },
    "iOS": {
        "Safari": { "sec_ch_ua_template": '"Safari";v="{major_version}"', "sec_ch_ua_platform": '"iOS"', "mobile": True, "weight": 0.90 },
        "Chrome": { "sec_ch_ua_template": '"Not/A)Brand";v="99", "Google Chrome";v="{major_version}", "Chromium";v="{major_version}"', "sec_ch_ua_platform": '"iOS"', "mobile": True, "weight": 0.10 }
    },
    "Android": {
        "Chrome": { "sec_ch_ua_template": '"Not/A)Brand";v="99", "Google Chrome";v="{major_version}", "Chromium";v="{major_version}"', "sec_ch_ua_platform": '"Android"', "mobile": True, "weight": 0.70 },
        "Firefox": { "sec_ch_ua_template": '"Firefox";v="{major_version}"', "sec_ch_ua_platform": '"Android"', "mobile": True, "weight": 0.15 },
        "Samsung": { "sec_ch_ua_template": '"Samsung Internet";v="{major_version}"', "sec_ch_ua_platform": '"Android"', "mobile": True, "weight": 0.15 }
    }
}

def load_user_agents_from_file(file_path):
    """Loads user agents from a text file."""
    try:
        with open(file_path, 'r') as f:
            user_agents = [line.strip() for line in f if line.strip()]
        if not user_agents:
            logger.warning(f"Файл с User-Agent'ами {file_path} пуст.")
            return []
        logger.info(f"Загружено {len(user_agents)} User-Agent'ов из {file_path}.")
        return user_agents
    except FileNotFoundError:
        logger.error(f"Файл с User-Agent'ами не найден: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Ошибка при чтении файла с User-Agent'ами: {e}")
        return []

class BrowserProfile:
    def __init__(self):
        self.fake = Faker()
        self.ua = ua_instance

        spoof_config = CONFIG.get("spoofing", {})
        ua_source = spoof_config.get("user_agent_source", "generate")
        
        # --- User-Agent Selection ---
        if ua_source == "file" and CONFIG.get("user_agents_list"):
            self.user_agent = random.choice(CONFIG["user_agents_list"])
            logger.debug(f"Using User-Agent from file: {self.user_agent}")
        else:
            if ua_source == "file":
                logger.warning("User-Agent source is 'file' but no agents were loaded. Falling back to generation.")
            self.user_agent = self._generate_ua_from_matrix()

        version_match = re.search(r"(?:Chrome|Firefox|Safari|Edge|Opera|SamsungBrowser)[/\s](\d+)", self.user_agent)
        self.major_version = version_match.group(1) if version_match else "100"

        self.os, self.browser = self._determine_os_browser_from_ua(self.user_agent)
        profile_data = BROWSER_PROFILES.get(self.os, {}).get(self.browser, BROWSER_PROFILES["Windows"]["Chrome"])

        self.language = random.choice(spoof_config.get("language_pool", ["en-US,en;q=0.9", "ru-RU,ru;q=0.9"]))
        self.timezone = random.choice(spoof_config.get("timezone_pool", ["America/New_York", "Europe/Moscow"]))
        
        screen_resolutions = ["375x812", "360x800"] if profile_data.get("mobile", False) else ["1920x1080", "2560x1440", "1366x768"]
        screen_res = random.choice(spoof_config.get("screen_size_pool", screen_resolutions))
        width, height = map(int, screen_res.split('x'))
        self.screen = {"width": width, "height": height}
        
        self.referer = self._generate_smart_referer() if spoof_config.get("smart_referer", True) else random.choice(spoof_config.get("referer_pool", ["https://google.com/"]))

        self.sec_ch_ua = profile_data.get("sec_ch_ua_template", "").format(major_version=self.major_version)
        self.sec_ch_ua_mobile = "?1" if profile_data.get("mobile", False) else "?0"
        self.sec_ch_ua_platform = profile_data.get("sec_ch_ua_platform", f'"{self.os}"')

    def _determine_os_browser_from_ua(self, ua_string):
        if "Windows" in ua_string: os = "Windows"
        elif "Macintosh" in ua_string: os = "macOS"
        elif "Linux" in ua_string and "Android" not in ua_string: os = "Linux"
        elif "iPhone" in ua_string: os = "iOS"
        elif "Android" in ua_string: os = "Android"
        else: os = "Windows"

        if "Edg/" in ua_string: browser = "Edge"
        elif "SamsungBrowser" in ua_string: browser = "Samsung"
        elif "Chrome" in ua_string: browser = "Chrome"
        elif "Firefox" in ua_string: browser = "Firefox"
        elif "Safari" in ua_string and "Chrome" not in ua_string: browser = "Safari"
        else: browser = "Chrome"
        
        return os, browser

    def _generate_ua_from_matrix(self):
        spoof_config = CONFIG.get("spoofing", {})
        allowed_combos = []
        weights = []
        
        for os, browsers in spoof_config.get("ua_matrix", {}).items():
            if os not in BROWSER_PROFILES: continue
            for browser, allowed in browsers.items():
                if allowed and browser in BROWSER_PROFILES[os]:
                    allowed_combos.append((os, browser))
                    weights.append(BROWSER_PROFILES[os][browser]["weight"])

        if not allowed_combos:
            os_choice, browser_choice = "Windows", "Chrome"
        else:
            os_choice, browser_choice = random.choices(allowed_combos, weights=weights, k=1)[0]

        if self.ua:
            try:
                browser_attr = browser_choice.lower().replace(" ", "")
                return getattr(self.ua, browser_attr)
            except (AttributeError, FakeUserAgentError):
                return self._generate_fallback_ua(os_choice, browser_choice)
        return self._generate_fallback_ua(os_choice, browser_choice)

    def _generate_fallback_ua(self, os, browser):
        os_info = {"Windows": "Windows NT 10.0; Win64; x64", "macOS": "Macintosh; Intel Mac OS X 10_15_7", "Linux": "X11; Linux x86_64"}
        browser_info = {"Chrome": f"Chrome/{random.randint(100, 120)}.0.0.0 Safari/537.36", "Firefox": f"Firefox/{random.randint(100, 120)}.0"}
        return f"Mozilla/5.0 ({os_info.get(os, os_info['Windows'])}) AppleWebKit/537.36 (KHTML, like Gecko) {browser_info.get(browser, browser_info['Chrome'])}"
    
    def _generate_smart_referer(self):
        search_engines = ["https://www.google.com/", "https://www.bing.com/", "https://duckduckgo.com/"]
        return random.choice(search_engines) + self.fake.word()
    
    def _generate_accept_headers(self):
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": self.language,
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }
    
    def get_headers(self):
        headers = {"user-agent": self.user_agent, **self._generate_accept_headers()}
        if self.referer: headers["referer"] = self.referer
        if self.browser in ["Chrome", "Edge"]:
            headers.update({
                "sec-ch-ua": self.sec_ch_ua,
                "sec-ch-ua-mobile": self.sec_ch_ua_mobile,
                "sec-ch-ua-platform": self.sec_ch_ua_platform,
            })
        return headers

    def get_cookies(self):
        return {"session": self.fake.sha256(raw_output=False)[:32]}

    def get_playwright_fingerprint(self):
        return {"locale": self.language.split(',')[0], "timezone_id": self.timezone, "viewport": self.screen}

# Инициализация при импорте модуля
init_user_agent()