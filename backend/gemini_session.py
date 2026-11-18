"""
Gemini Session Manager using Playwright with persistent Chromium profile.

Features:
- Uses Playwright launch_persistent_context to preserve cookies, local storage, and authentication.
- Headed visible mode allowing manual Google login without automated bot flags.
- Prevents concurrent instances from corrupting the profile using a PID lock file.
- Graceful context shutdown to ensure all SQLite databases & cookies flush to disk.
- Automatically reuses session for Gemini Notebook.
"""

import sys
import os
import json
import time
import asyncio
import threading
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure project root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from app.core.config import settings
    DEFAULT_PROFILE_DIR = settings.BROWSER_PROFILE_DIR
    DEFAULT_DATA_DIR = settings.DATA_DIR
    DEFAULT_NOTEBOOK_URL = settings.GEMINI_NOTEBOOK_URL
except Exception:
    DEFAULT_PROFILE_DIR = SCRIPT_DIR / "browser_profile"
    DEFAULT_DATA_DIR = SCRIPT_DIR / "data"
    DEFAULT_NOTEBOOK_URL = "https://gemini.google.com/notebook/455d7360-aa4b-4d50-bf2c-2bb489a5a3fd"

from playwright.async_api import async_playwright, BrowserContext, Page

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gemini_session")

# Browser arguments optimized for human interaction and bypassing bot detection
CHROMIUM_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-infobars",
    "--start-maximized",
    "--no-default-browser-check",
    "--disable-notifications",
]

IGNORE_DEFAULT_ARGS = [
    "--enable-automation",
]


def is_pid_running(pid: int) -> bool:
    """Check if a process with given PID is running on Windows."""
    if pid <= 0:
        return False
    try:
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        exit_code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return exit_code.value == STILL_ACTIVE
    except Exception:
        return False


class GeminiSessionManager:
    def __init__(
        self,
        profile_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None,
        notebook_url: Optional[str] = None
    ):
        self.profile_dir = Path(profile_dir or DEFAULT_PROFILE_DIR).resolve()
        self.data_dir = Path(data_dir or DEFAULT_DATA_DIR).resolve()
        self.notebook_url = notebook_url or DEFAULT_NOTEBOOK_URL

        # Ensure directories exist
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.lock_file = self.data_dir / "browser_session.lock"
        self.save_trigger_file = self.data_dir / ".save_trigger"
        self.stop_trigger_file = self.data_dir / ".stop_trigger"
        self.state_file = self.data_dir / "session_state.json"

    # --- Lock Management ---
    def acquire_lock(self) -> bool:
        """Acquires PID lock to prevent multiple Chromium instances using the same profile."""
        if self.lock_file.exists():
            try:
                locked_pid = int(self.lock_file.read_text(encoding="utf-8").strip())
                if is_pid_running(locked_pid):
                    logger.warning(f"Browser instance already active with PID {locked_pid}.")
                    return False
                else:
                    logger.info(f"Removing stale lock from PID {locked_pid}.")
                    self.lock_file.unlink(missing_ok=True)
            except Exception:
                self.lock_file.unlink(missing_ok=True)

        try:
            self.lock_file.write_text(str(os.getpid()), encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    def release_lock(self):
        """Releases the PID lock."""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink(missing_ok=True)
        except Exception:
            pass

    def is_locked(self) -> bool:
        if not self.lock_file.exists():
            return False
        try:
            pid = int(self.lock_file.read_text(encoding="utf-8").strip())
            return is_pid_running(pid)
        except Exception:
            return False

    # --- State Management ---
    def update_state(self, status: str, extra: Optional[Dict[str, Any]] = None):
        state = {
            "status": status,
            "profile_dir": str(self.profile_dir),
            "notebook_url": self.notebook_url,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if extra:
            state.update(extra)
        try:
            self.state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write state file: {e}")

    def get_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"status": "uninitialized", "profile_dir": str(self.profile_dir)}

    def trigger_save(self):
        """Signals the running login session to save and close gracefully."""
        self.save_trigger_file.write_text("save", encoding="utf-8")
        logger.info("Save trigger created.")

    def trigger_stop(self):
        """Signals the running browser session to stop."""
        self.stop_trigger_file.write_text("stop", encoding="utf-8")
        logger.info("Stop trigger created.")

    # --- Browser Launch Helpers ---
    async def _launch_context(self, playwright_instance) -> BrowserContext:
        """Launches persistent context with Chrome channel (or chromium fallback)."""
        logger.info(f"Using persistent profile at: {self.profile_dir}")
        try:
            context = await playwright_instance.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                channel="chrome",
                args=CHROMIUM_ARGS,
                ignore_default_args=IGNORE_DEFAULT_ARGS,
                viewport=None,
            )
            logger.info("Launched persistent context using Chrome channel.")
            return context
        except Exception as e:
            logger.warning(f"Chrome channel unavailable ({e}), launching bundled Chromium...")
            context = await playwright_instance.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                args=CHROMIUM_ARGS,
                ignore_default_args=IGNORE_DEFAULT_ARGS,
                viewport=None,
            )
            logger.info("Launched persistent context using bundled Chromium.")
            return context

    # --- Step 1 & 2: Launch for Manual Login ---
    async def launch_login_session(self):
        """
        Launches visible Chromium for the user to log in manually to their Google Account.
        Waits until save trigger, terminal Enter key, or browser close, then saves and exits.
        """
        if not self.acquire_lock():
            print("\n[ERROR] Another browser session is already running using this profile.", flush=True)
            print("Please close any open Chromium/Chrome windows using this profile first.\n", flush=True)
            return False

        # Clear triggers
        self.save_trigger_file.unlink(missing_ok=True)
        self.stop_trigger_file.unlink(missing_ok=True)

        self.update_state("awaiting_manual_login")

        print("\n" + "=" * 70, flush=True)
        print("  STEP 1: CHROMIUM PERSISTENT BROWSER LAUNCHED", flush=True)
        print("=" * 70, flush=True)
        print(f"Profile Directory: {self.profile_dir}", flush=True)
        print("Opening Google Accounts login page...", flush=True)
        print("Please log in to your Google Account manually in the opened browser window.", flush=True)
        print("-" * 70, flush=True)
        print("WHEN FINISHED LOGGING IN:", flush=True)
        print("  -> Press [Enter] here in this terminal, OR", flush=True)
        print("  -> Tell the AI assistant: 'Save this session'", flush=True)
        print("=" * 70 + "\n", flush=True)

        # Non-blocking terminal input listener
        save_requested_flag = [False]
        def listen_stdin():
            try:
                if sys.stdin and sys.stdin.isatty():
                    sys.stdin.readline()
                    save_requested_flag[0] = True
            except Exception:
                pass

        t = threading.Thread(target=listen_stdin, daemon=True)
        t.start()

        async with async_playwright() as p:
            context = None
            try:
                context = await self._launch_context(p)
                page = context.pages[0] if context.pages else await context.new_page()

                # Open Google Accounts login
                await page.goto("https://accounts.google.com/", wait_until="domcontentloaded", timeout=60000)

                # Wait loop for save signal
                save_requested = False
                while True:
                    # 1. Check for terminal Enter key
                    if save_requested_flag[0]:
                        logger.info("Terminal [Enter] key detected!")
                        save_requested = True
                        break

                    # 2. Check for save trigger file
                    if self.save_trigger_file.exists():
                        logger.info("Save trigger file detected!")
                        save_requested = True
                        break

                    # 3. Check for stop trigger file
                    if self.stop_trigger_file.exists():
                        logger.info("Stop trigger detected without saving.")
                        break

                    # 4. Check if user closed all browser windows manually
                    if not context.pages:
                        logger.info("All browser windows were closed by the user.")
                        save_requested = True
                        break

                    await asyncio.sleep(0.5)

                if save_requested:
                    print("\n[INFO] Gracefully closing browser context to persist session...", flush=True)
                    self.save_trigger_file.unlink(missing_ok=True)
                    # Graceful context close flushes SQLite cookies and session storage
                    await context.close()
                    context = None
                    self.update_state("session_saved", {"last_saved": time.strftime("%Y-%m-%d %H:%M:%S")})
                    print("[SUCCESS] Browser session successfully saved and preserved!", flush=True)
                    print(f"All authentication cookies and storage retained in:\n  {self.profile_dir}\n", flush=True)
                    return True
                else:
                    self.stop_trigger_file.unlink(missing_ok=True)
                    if context:
                        await context.close()
                        context = None
                    self.update_state("cancelled")
                    return False

            except Exception as e:
                logger.error(f"Error during login session: {e}")
                self.update_state("error", {"error": str(e)})
                return False
            finally:
                if context:
                    try:
                        await context.close()
                    except Exception:
                        pass
                self.release_lock()

    # --- Step 4 & 5: Open Gemini Notebook with Reused Session ---
    async def open_notebook_session(self, url: Optional[str] = None):
        """
        Reuses the saved profile, opens Gemini Notebook, and verifies authentication.
        """
        target_url = url or self.notebook_url

        if not self.acquire_lock():
            print("\n[ERROR] Another browser session is already active.", flush=True)
            print("Please close any open Chromium/Chrome windows using this profile first.\n", flush=True)
            return False

        self.stop_trigger_file.unlink(missing_ok=True)
        self.update_state("running_notebook", {"target_url": target_url})

        print("\n" + "=" * 70, flush=True)
        print("  REUSING PERSISTENT SESSION -> OPENING GEMINI NOTEBOOK", flush=True)
        print("=" * 70, flush=True)
        print(f"Profile: {self.profile_dir}", flush=True)
        print(f"Target:  {target_url}", flush=True)
        print("=" * 70 + "\n", flush=True)

        async with async_playwright() as p:
            context = None
            try:
                context = await self._launch_context(p)
                page = context.pages[0] if context.pages else await context.new_page()

                print(f"[INFO] Navigating to {target_url}...", flush=True)
                await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

                # Wait for page elements to stabilize
                await asyncio.sleep(3)

                current_url = page.url
                page_title = await page.title()
                print(f"[INFO] Current URL: {current_url}", flush=True)
                print(f"[INFO] Page Title:  {page_title}", flush=True)

                # Check if redirected to Google login
                if "accounts.google.com" in current_url:
                    print("\n[WARNING] Redirected to Google login! Session expired or not authenticated.", flush=True)
                    print("Please run the login step again:\n  start_login.bat  (or python backend/gemini_session.py login)\n", flush=True)
                    self.update_state("reauth_required")
                else:
                    print("\n[SUCCESS] Successfully authenticated! Gemini Notebook is active.", flush=True)
                    self.update_state("notebook_active")

                print("[INFO] Browser is open for your interaction. Close browser window when done.\n", flush=True)

                # Keep browser alive until user closes it or sends stop trigger
                while True:
                    if self.stop_trigger_file.exists():
                        self.stop_trigger_file.unlink(missing_ok=True)
                        print("[INFO] Stop trigger received. Closing browser...", flush=True)
                        break

                    if not context.pages:
                        print("[INFO] Browser closed by user.", flush=True)
                        break

                    await asyncio.sleep(0.5)

                await context.close()
                context = None
                self.update_state("closed")
                return True

            except Exception as e:
                logger.error(f"Error in notebook session: {e}")
                self.update_state("error", {"error": str(e)})
                return False
            finally:
                if context:
                    try:
                        await context.close()
                    except Exception:
                        pass
                self.release_lock()


def main():
    parser = argparse.ArgumentParser(description="Gemini Playwright Persistent Session Manager")
    parser.add_argument(
        "action",
        choices=["login", "save", "notebook", "open", "stop", "status"],
        help="Action to perform: 'login' (Step 1-2), 'save' (Step 3), 'notebook'/'open' (Step 4-5), 'status', or 'stop'"
    )
    parser.add_argument("--profile-dir", type=str, default=None, help="Custom profile directory")
    parser.add_argument("--url", type=str, default=None, help="Custom notebook URL")
    args = parser.parse_args()

    manager = GeminiSessionManager(
        profile_dir=Path(args.profile_dir) if args.profile_dir else None,
        notebook_url=args.url
    )

    if args.action == "login":
        asyncio.run(manager.launch_login_session())
    elif args.action == "save":
        manager.trigger_save()
        print("[INFO] Save signal sent to active login session.", flush=True)
    elif args.action in ("notebook", "open"):
        asyncio.run(manager.open_notebook_session(args.url))
    elif args.action == "stop":
        manager.trigger_stop()
        print("[INFO] Stop signal sent to active session.", flush=True)
    elif args.action == "status":
        state = manager.get_state()
        print("\n--- Session Status ---", flush=True)
        print(f"Status:       {state.get('status')}", flush=True)
        print(f"Profile Dir:  {state.get('profile_dir')}", flush=True)
        print(f"Is Locked:    {manager.is_locked()}", flush=True)
        print(f"Details:      {json.dumps(state, indent=2)}\n", flush=True)


if __name__ == "__main__":
    main()
