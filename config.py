import logging
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

def setup_logging(level=logging.INFO, console=False, file_logging=True, file_path="logs/cyberblitz.log"):
    """Настройка логирования"""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    if file_logging:
        log_file = Path(file_path)
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(stream_handler)

setup_logging()
logger = logging.getLogger(__name__)

CONFIG = {
    # Proxy configuration
    "proxy_source": "api",  # "api" or "file"
    "proxy_file": None,     # Path to proxy list file
    "proxy_type": "socks5", # Default proxy type for file-based proxies
    "target_ip": "127.0.0.1",
    "target_url": "http://localhost",
    "port": 80,
    "threads": 100,
    "duration": 60,
    "proxies": [],
    "use_tor": False,
    "tor_library": "torpy",
    "use_proxy": False,
    "proxy_type": "socks5",
    "use_browser": "playwright",
    "tls_client_identifier": "chrome_120",
    "spoofing": {
        "x_forwarded_for": "",
        "session_id": "",
        "auth_token": "",
        "referer_pool": [
            "https://www.google.com/",
            "https://yandex.ru/",
            "https://duckduckgo.com/",
            "https://www.bing.com/"
        ],
        "language_pool": ["en-US,en;q=0.9", "ru-RU,ru;q=0.9", "es-ES,es;q=0.9"],
        "timezone_pool": ["America/New_York", "Europe/Moscow", "Europe/London"],
        "screen_size_pool": ["1920x1080", "1600x900", "1366x768"],
        "ua_matrix": {
            "Windows": {"Chrome": True, "Firefox": True, "Safari": False},
            "macOS": {"Chrome": True, "Firefox": True, "Safari": True},
            "Linux": {"Chrome": True, "Firefox": True, "Safari": False}
        }
    },
    "browser_behavior": {
        "clicks": False,
        "scroll": False,
        "delay": 1
    }
}

def update_config(**kwargs):
    """Обновление конфигурации"""
    for key, value in kwargs.items():
        if key in CONFIG and isinstance(CONFIG[key], dict):
            CONFIG[key].update(value)
        else:
            CONFIG[key] = value
    logger.debug(f"Конфигурация обновлена: {kwargs}")