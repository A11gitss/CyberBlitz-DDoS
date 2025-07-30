from typing import Dict, List, Optional, Any
import json
import random
import time
import asyncio
from playwright.async_api import async_playwright, Browser, Page
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class BrowserProfile:
    user_agent: str
    headers: Dict[str, str]
    viewport: Dict[str, int]
    languages: List[str]
    platform: str
    webgl_vendor: str
    webgl_renderer: str

class CloudflareBypasser:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.profiles: Dict[str, BrowserProfile] = self._load_browser_profiles()
        self.current_profile: Optional[BrowserProfile] = None
        self.cookies: Dict[str, str] = {}
        self.js_challenge_passed = False

    def _load_browser_profiles(self) -> Dict[str, BrowserProfile]:
        profiles = {
            "chrome_120": BrowserProfile(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "accept-language": "en-US,en;q=0.9",
                    "sec-ch-ua": '"Chromium";v="120", "Google Chrome";v="120", "Not=A?Brand";v="24"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "none",
                    "sec-fetch-user": "?1",
                    "upgrade-insecure-requests": "1"
                },
                viewport={"width": 1920, "height": 1080},
                languages=["en-US", "en"],
                platform="Win32",
                webgl_vendor="Google Inc. (NVIDIA)",
                webgl_renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)"
            ),
            # Add more profiles here
        }
        return profiles

    async def _patch_browser(self, page: Page):
        """Remove automation flags and add human-like behavior"""
        await page.add_init_script("""
            delete Object.getPrototypeOf(navigator).webdriver;
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'platform', {get: () => '%s'});
            Object.defineProperty(navigator, 'languages', {get: () => %s});
        """ % (self.current_profile.platform, json.dumps(self.current_profile.languages)))

        # Patch canvas fingerprint
        await page.add_init_script("""
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type) {
                const context = originalGetContext.apply(this, arguments);
                if (type === 'webgl' || type === 'webgl2') {
                    context.getParameter = function(parameter) {
                        if (parameter === 37445) return '%s';
                        if (parameter === 37446) return '%s';
                        return originalGetParameter.apply(this, arguments);
                    }
                }
                return context;
            };
        """ % (self.current_profile.webgl_vendor, self.current_profile.webgl_renderer))

    async def _emulate_human_behavior(self, page: Page):
        """Emulate human-like mouse movements and interactions"""
        # Random mouse movements
        for _ in range(random.randint(3, 7)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))

        # Random scrolling
        await page.evaluate("""
            window.scrollTo({
                top: document.body.scrollHeight * Math.random(),
                behavior: 'smooth'
            });
        """)
        await asyncio.sleep(random.uniform(1, 2))

    async def init(self, profile_name: str = "chrome_120"):
        """Initialize the bypasser with a specific browser profile"""
        self.current_profile = self.profiles[profile_name]
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )

    async def bypass(self, url: str) -> Dict[str, Any]:
        """Main bypass method that handles Cloudflare protection"""
        if not self.browser:
            raise RuntimeError("Call init() first")

        context = await self.browser.new_context(
            user_agent=self.current_profile.user_agent,
            viewport=self.current_profile.viewport,
            extra_http_headers=self.current_profile.headers
        )

        page = await context.new_page()
        await self._patch_browser(page)

        try:
            response = await page.goto(url, wait_until="networkidle")
            
            # Check for Cloudflare challenge
            if "challenge" in response.url or await page.get_by_text("Checking if the site connection is secure").count():
                logger.info("Detected Cloudflare challenge, attempting to solve...")
                await self._emulate_human_behavior(page)
                await asyncio.sleep(random.uniform(4, 6))  # Wait for challenge to complete
                
                # Get cookies after challenge
                self.cookies = {c["name"]: c["value"] for c in await context.cookies()}
                self.js_challenge_passed = True

            return {
                "cookies": self.cookies,
                "challenge_passed": self.js_challenge_passed,
                "headers": dict(response.headers),
                "status": response.status
            }

        except Exception as e:
            logger.error(f"Bypass failed: {str(e)}")
            raise

        finally:
            await context.close()

    async def close(self):
        """Clean up resources"""
        if self.browser:
            await self.browser.close()
            self.browser = None
