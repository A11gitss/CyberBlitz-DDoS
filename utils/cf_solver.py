import asyncio
from playwright.async_api import async_playwright
from config import logger

async def get_cf_cookie(target_url: str) -> (dict, str):
    """
    Использует Playwright для запуска браузера, перехода на целевой URL,
    решения челленджа Cloudflare и извлечения clearance cookie и User-Agent.

    :param target_url: URL-адрес для получения cookie.
    :return: Кортеж, содержащий словарь с cookie и строку User-Agent.
             Возвращает (None, None) в случае ошибки.
    """
    logger.info(f"Запуск браузера для получения cookie Cloudflare с {target_url}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(target_url, timeout=60000)
            
            # Даем Cloudflare время на выполнение своих скриптов и челленджей
            logger.debug("Ожидание решения челленджа Cloudflare...")
            await page.wait_for_timeout(15000) # Ожидание 15 секунд

            cookies = await page.context.cookies()
            user_agent = await page.evaluate("() => navigator.userAgent")
            
            await browser.close()

            cf_cookie = None
            for cookie in cookies:
                if cookie['name'] == 'cf_clearance':
                    logger.info(f"Cookie 'cf_clearance' успешно получен: {cookie['value'][:20]}...")
                    cf_cookie = {cookie['name']: cookie['value']}
                    break
            
            if not cf_cookie:
                logger.warning("Не удалось найти cookie 'cf_clearance'. Возможно, сайт не защищен Cloudflare или челлендж не был пройден.")
                return None, None

            return cf_cookie, user_agent

    except Exception as e:
        logger.error(f"Ошибка при получении cookie Cloudflare: {e}")
        return None, None

if __name__ == '__main__':
    # Пример использования
    async def main():
        # Замените на URL, защищенный Cloudflare
        test_url = "https://gofile.io/uploadFiles" 
        cookie, ua = await get_cf_cookie(test_url)
        if cookie and ua:
            print("Полученные данные:")
            print("Cookie:", cookie)
            print("User-Agent:", ua)
        else:
            print("Не удалось получить данные.")
            
    asyncio.run(main())
