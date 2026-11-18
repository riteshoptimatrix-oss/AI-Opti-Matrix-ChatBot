"""
Gemini Notebook Background Automation Service.

Features:
- Runs in headless background mode using the authenticated persistent browser profile.
- Keeps an active page on the Gemini Notebook URL for fast prompt execution.
- Reads 'Prompt Template.txt' and dynamically replaces '{user_question}'.
- Dispatches the prompt to the Notebook, waits for generation to complete, and extracts the response.
- Concurrency-safe using asyncio.Lock.
- Automatic recovery and graceful error handling.
"""

import sys
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, List
from playwright.async_api import async_playwright, Playwright, BrowserContext, Page

from app.core.config import settings

logger = logging.getLogger("notebook_automation")

# Headless persistent Chromium arguments
CHROMIUM_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-infobars",
    "--no-default-browser-check",
    "--disable-notifications",
]

IGNORE_DEFAULT_ARGS = [
    "--enable-automation",
]


class NotebookAutomationService:
    def __init__(self):
        self.profile_dir = settings.BROWSER_PROFILE_DIR
        self.notebook_url = settings.GEMINI_NOTEBOOK_URL
        self.template_path = settings.PROMPT_TEMPLATE_PATH

        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._lock = asyncio.Lock()

    def load_prompt_template(self, user_question: str) -> str:
        """Reads Prompt Template.txt and replaces {user_question}."""
        if not self.template_path.exists():
            logger.warning(f"Template path {self.template_path} does not exist. Using fallback.")
            return f"User question: {user_question}"

        raw_template = self.template_path.read_text(encoding="utf-8")
        if "{user_question}" in raw_template:
            final_prompt = raw_template.replace("{user_question}", user_question.strip())
        else:
            final_prompt = f"{raw_template}\n\nUSER QUESTION:\n{user_question.strip()}"
        return final_prompt

    async def ensure_ready(self) -> Page:
        """Ensures that the headless browser context and notebook page are active and ready."""
        try:
            if self._page and not self._page.is_closed() and self._context:
                # Test if page is responsive
                await self._page.evaluate("() => document.title")
                return self._page
        except Exception:
            logger.warning("Existing page unresponsive. Rebuilding context...")
            await self.close()

        logger.info("Initializing background Gemini Notebook browser...")
        if not self._playwright:
            self._playwright = await async_playwright().start()

        try:
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=True,
                channel="chrome",
                args=CHROMIUM_ARGS,
                ignore_default_args=IGNORE_DEFAULT_ARGS,
                viewport={"width": 1280, "height": 800},
            )
        except Exception as e:
            logger.warning(f"Chrome channel launch failed ({e}), falling back to bundled Chromium...")
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=True,
                args=CHROMIUM_ARGS,
                ignore_default_args=IGNORE_DEFAULT_ARGS,
                viewport={"width": 1280, "height": 800},
            )

        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        
        logger.info(f"Navigating to Gemini Notebook: {self.notebook_url}")
        await self._page.goto(self.notebook_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)

        current_url = self._page.url
        if "accounts.google.com" in current_url:
            logger.error("Session expired or not logged in! Redirected to accounts.google.com")
            raise RuntimeError("Google session expired or not authenticated. Please run start_login.bat.")

        logger.info("Background Gemini Notebook is ready.")
        return self._page

    async def submit_question(self, user_question: str) -> str:
        """
        End-to-end execution:
        1. Formats prompt with Prompt Template.txt.
        2. Submits to Gemini Notebook input.
        3. Waits for response generation.
        4. Extracts and returns response text.
        """
        async with self._lock:
            final_prompt = self.load_prompt_template(user_question)
            logger.info(f"Generated prompt ({len(final_prompt)} chars) for question: '{user_question}'")

            page = await self.ensure_ready()

            # Locate the rich-text editor
            try:
                editor = await page.wait_for_selector('div[role="textbox"], .ql-editor', timeout=15000)
            except Exception:
                logger.warning("Editor not found, reloading page...")
                await page.goto(self.notebook_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(4)
                editor = await page.wait_for_selector('div[role="textbox"], .ql-editor', timeout=15000)

            # Record existing responses count
            prev_responses = await page.query_selector_all('message-content, .markdown, model-response')
            prev_count = len(prev_responses)

            # Focus and clear editor
            await editor.click()
            await editor.fill("")
            await asyncio.sleep(0.3)

            # Fill prompt text
            await editor.fill(final_prompt)
            await asyncio.sleep(1)

            # Find and click the send button
            send_btn = None
            try:
                send_btn = await page.wait_for_selector('button[aria-label="Send message"]', timeout=8000)
                await send_btn.click()
            except Exception:
                logger.info("Send button not found or disabled, sending Enter key...")
                await editor.press("Enter")

            logger.info("Prompt submitted to Gemini Notebook. Waiting for generation...")

            # Wait for generation to finish
            start_time = time.time()
            max_wait_seconds = 50
            final_response_text = ""

            while (time.time() - start_time) < max_wait_seconds:
                await asyncio.sleep(1)
                elapsed = int(time.time() - start_time)

                # Check if stop button is present (generation in progress)
                stop_btn = await page.query_selector('button[aria-label*="Stop"]')
                is_generating = stop_btn is not None

                current_responses = await page.query_selector_all('message-content, .markdown, model-response')
                current_count = len(current_responses)

                if current_count > prev_count and not is_generating and elapsed >= 3:
                    # Allow 1 second for DOM markdown rendering to settle
                    await asyncio.sleep(1)
                    final_response_text = (await current_responses[-1].inner_text()).strip()
                    if final_response_text:
                        logger.info(f"Response successfully received ({len(final_response_text)} chars) in {elapsed}s.")
                        return final_response_text

            # If loop finished and response exists, try to get last response
            current_responses = await page.query_selector_all('message-content, .markdown, model-response')
            if current_responses and len(current_responses) > prev_count:
                final_response_text = (await current_responses[-1].inner_text()).strip()
                if final_response_text:
                    logger.info("Retrieved response after wait completion.")
                    return final_response_text

            raise TimeoutError("Gemini Notebook did not complete generation within the timeout period.")

    async def close(self):
        """Cleanly closes page, context, and playwright engine."""
        try:
            if self._context:
                await self._context.close()
                self._context = None
                self._page = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            logger.info("Notebook automation service closed gracefully.")
        except Exception as e:
            logger.warning(f"Error closing notebook service: {e}")


notebook_automation = NotebookAutomationService()
