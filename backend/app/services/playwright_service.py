import base64
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Playwright
from app.core.config import settings

logger = logging.getLogger(__name__)

class PlaywrightService:
    def __init__(self):
        self.headless = settings.PLAYWRIGHT_HEADLESS

    async def scrape_page(
        self,
        url: str,
        wait_selector: Optional[str] = None,
        wait_timeout_ms: int = 30000,
        extract_text_only: bool = True
    ) -> Dict[str, Any]:
        """
        Scrapes content from a webpage using headless Chromium.
        """
        async with async_playwright() as p:
            browser: Optional[Browser] = None
            try:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                response = await page.goto(url, wait_until="domcontentloaded", timeout=wait_timeout_ms)
                status_code = response.status if response else None

                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=wait_timeout_ms)

                title = await page.title()

                if extract_text_only:
                    # Extract visible body text
                    content = await page.evaluate("() => document.body.innerText")
                else:
                    content = await page.content()

                await context.close()
                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "content": content,
                    "status_code": status_code,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Playwright scrape error for {url}: {e}")
                return {
                    "success": False,
                    "url": url,
                    "title": None,
                    "content": None,
                    "status_code": None,
                    "error": str(e)
                }
            finally:
                if browser:
                    await browser.close()

    async def take_screenshot(
        self,
        url: str,
        full_page: bool = True,
        wait_ms: int = 1500
    ) -> Dict[str, Any]:
        """
        Takes a screenshot of the specified webpage and returns it as a base64 encoded string.
        """
        async with async_playwright() as p:
            browser: Optional[Browser] = None
            try:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(viewport={"width": 1280, "height": 800})
                page = await context.new_page()

                await page.goto(url, wait_until="networkidle", timeout=30000)
                if wait_ms > 0:
                    await page.wait_for_timeout(wait_ms)

                screenshot_bytes = await page.screenshot(full_page=full_page)
                b64_image = base64.b64encode(screenshot_bytes).decode("utf-8")

                await context.close()
                return {
                    "success": True,
                    "url": url,
                    "image_base64": b64_image,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Playwright screenshot error for {url}: {e}")
                return {
                    "success": False,
                    "url": url,
                    "image_base64": None,
                    "error": str(e)
                }
            finally:
                if browser:
                    await browser.close()

    async def check_status(self) -> Dict[str, Any]:
        """
        Checks if Playwright chromium browser is installed and launches successfully.
        """
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                await browser.close()
                return {
                    "status": "online",
                    "engine": "Playwright Chromium",
                    "chromium_available": True
                }
            except Exception as e:
                return {
                    "status": "error",
                    "engine": "Playwright Chromium",
                    "chromium_available": False,
                    "error": str(e)
                }

playwright_service = PlaywrightService()
