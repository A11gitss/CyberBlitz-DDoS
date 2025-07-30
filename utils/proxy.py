import requests
from torpy.http.requests import tor_requests_session
from config import CONFIG, logger
import random
import re
from urllib.parse import urlparse
from aiohttp_socks import ProxyConnector

def load_proxies_from_file(filepath, proxy_type='http'):
    """
    Load proxies from a file and parse them into a structured format.
    Handles 'ip:port' and 'scheme://user:pass@ip:port' formats.
    """
    proxies = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Prepend scheme if not present
                if '://' not in line:
                    line = f"{proxy_type}://{line}"

                parsed = urlparse(line)
                proxy_dict = {
                    'server': line,
                    'username': parsed.username,
                    'password': parsed.password
                }
                proxies.append(proxy_dict)
    except Exception as e:
        logger.error(f"Error loading proxies from file {filepath}: {e}")
    return proxies

def get_proxies():
    """
    Get proxies from the configured source (file or API) and return them
    in a standardized dictionary format.
    """
    try:
        # Try getting proxies from file first if configured
        if CONFIG.get("proxy_file"):
            return load_proxies_from_file(CONFIG["proxy_file"], CONFIG.get("proxy_type", "socks5"))
            
        # Fallback to API
        response = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=elite")
        proxies = response.text.splitlines()
        # Return in the standardized format
        return [{"server": f"socks5://{proxy}", "username": None, "password": None} for proxy in proxies if proxy]
    except Exception as e:
        logger.error(f"Ошибка при получении прокси: {e}")
        return []

def get_tor_session():
    """Создание сессии с Tor"""
    if CONFIG["tor_library"] == "torpy":
        return tor_requests_session()
    else:
        return requests.Session()

async def get_async_tor_connector():
    """Создание асинхронного коннектора для Tor с поддержкой множественных цепочек"""
    if CONFIG["use_tor"]:
        from .tor_manager import TorCircuitManager
        
        # Инициализируем менеджер Tor (синглтон)
        manager = TorCircuitManager()
        
        # Получаем порт для новой или существующей цепочки
        socks_port = await manager.get_circuit()
        if socks_port:
            return await manager.create_aiohttp_connector(socks_port)
        
    return None

def get_random_proxy():
    """Выбор случайного прокси"""
    proxies = CONFIG.get("proxies") or get_proxies()
    if proxies:
        # Update the global config if proxies were fetched for the first time
        if not CONFIG.get("proxies"):
            CONFIG["proxies"] = proxies
        return random.choice(proxies)
    return None
