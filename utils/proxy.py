import requests
from torpy.http.requests import tor_requests_session
from config import CONFIG, logger
import random

def get_proxies():
    try:
        response = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=elite")
        proxies = response.text.splitlines()
        return [{"socks5": f"socks5://{proxy}"} for proxy in proxies if proxy]
    except Exception as e:
        logger.error(f"Ошибка при получении прокси: {e}")
        return []

def get_tor_session():
    """Создание сессии с Tor"""
    if CONFIG["tor_library"] == "torpy":
        return tor_requests_session()
    else:
        return requests.Session()
def get_random_proxy():
    """Выбор случайного прокси"""
    proxies = CONFIG["proxies"] or get_proxies()
    return random.choice(proxies) if proxies else None