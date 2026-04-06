"""Browser manager for persistent Playwright sessions."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from job_hunter.config.job_boards.naukri import NAUKRI

load_dotenv()


class BrowserManager:
    """Manages a persistent browser session for Naukri scraping."""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self, headless: bool | None = None) -> Page:
        """Start browser and return page."""
        if headless is not None:
            self.headless = headless

        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )

        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )

        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)

        self._page = await self._context.new_page()
        return self._page

    async def login_naukri(
        self, email: str | None = None, password: str | None = None
    ) -> bool:
        """Login to Naukri and return success status."""
        if not email:
            email = os.getenv("NAUKRI_EMAIL", "")
        if not password:
            password = os.getenv("NAUKRI_PASSWORD", "")

        if not email or not password:
            print("[ERROR] Naukri credentials not provided")
            return False

        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")

        try:
            print("[INFO] Logging into Naukri...")
            await self._page.goto(
                NAUKRI.login_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await asyncio.sleep(2)

            html = await self._page.content()
            if "Access Denied" in html or len(html) < 1000:
                print("[ERROR] Login page blocked by bot protection")
                return False

            email_input = self._page.locator('input[placeholder*="Email ID"]').first
            if await email_input.count() == 0:
                email_input = self._page.locator('input[type="email"]').first
            if await email_input.count() == 0:
                print("[ERROR] Could not find email input")
                return False

            await email_input.wait_for(state="visible", timeout=5000)
            await email_input.fill(email)

            pass_input = self._page.locator('input[type="password"]').first
            if await pass_input.count() > 0:
                await pass_input.fill(password)

            await asyncio.sleep(1)

            login_btn = self._page.locator('button:has-text("Login")').first
            if await login_btn.count() > 0:
                await login_btn.click()
            else:
                submit = self._page.locator('button[type="submit"]').first
                if await submit.count() > 0:
                    await submit.click()

            await asyncio.sleep(5)

            current_url = self._page.url
            if "login" in current_url.lower() or "nlogin" in current_url.lower():
                print("[ERROR] Still on login page. Check credentials or CAPTCHA.")
                return False

            print("[INFO] Login successful.")
            return True

        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            return False

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    async def close(self):
        """Close browser session."""
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
        self._browser = None
        self._context = None
        self._page = None
