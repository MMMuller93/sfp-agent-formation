"""
Delaware Name Availability Check — Playwright Automation

Converted from Chrome DevTools Recorder export.
Source: recordings/delaware/de-name-search-and-filing.recording.json

Usage:
    python name_check.py --name "My Company" --type LLC --ending "L.L.C."

CAPTCHA handling:
    - Screenshots the CAPTCHA image for human solving
    - Plays audio CAPTCHA if available
    - Returns CAPTCHA image path for human kernel integration

NOTE: Delaware Division of Corporations prohibits automated data mining.
This script is for checking specific names for actual entity formations only.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Install playwright: pip install playwright && playwright install chromium")
    sys.exit(1)


# --- DE Form Constants ---

DE_NAME_SEARCH_URL = "https://icis.corp.delaware.gov/Ecorp/NameReserv/NameReservation.aspx"
DE_HOME_URL = "https://corp.delaware.gov/"
DE_FILING_PORTAL_URL = "https://icis.corp.delaware.gov/ecorp2/"

# Entity type values for the dropdown
ENTITY_TYPES = {
    "CORPORATION": "C",
    "LLC": "Y",
    "LP": "P",
    "GP": "G",
    "STATUTORY_TRUST": "S",
}

# Entity ending values for LLC
LLC_ENDINGS = ["L.L.C.", "LLC", "Limited Liability Company"]
CORP_ENDINGS = ["INC.", "INCORPORATED", "CORPORATION", "CORP."]

# Form selectors
SELECTORS = {
    "disclaimer_checkbox": "#ctl00_ContentPlaceHolder1_frmDisclaimerChkBox",
    "entity_type": "#ctl00_ContentPlaceHolder1_frmEntityType",
    "entity_ending": "#ctl00_ContentPlaceHolder1_frmEntityEnding",
    "entity_name": "#ctl00_ContentPlaceHolder1_frmEntityName",
    "captcha_input": "#ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha",
    "captcha_refresh": "#btnRefresh",
    "captcha_audio": "#playCaptchaButton",
    "captcha_image": "#ctl00_ContentPlaceHolder1_pnlCaptcha img",
    "search_button": "#ctl00_ContentPlaceHolder1_btnSubmit",
    "new_search_button": "#ctl00_ContentPlaceHolder1_btnNo",
}


async def check_name_availability(
    entity_name: str,
    entity_type: str = "LLC",
    entity_ending: str = "L.L.C.",
    captcha_code: str | None = None,
    screenshot_dir: str = "/tmp/de-name-check",
    headless: bool = True,
    timeout_ms: int = 10000,
) -> dict:
    """
    Check entity name availability on DE Division of Corporations.

    Args:
        entity_name: The entity name to check (case-insensitive)
        entity_type: Entity type key from ENTITY_TYPES
        entity_ending: Entity ending string
        captcha_code: Pre-solved CAPTCHA code (if None, will screenshot for human)
        screenshot_dir: Directory for screenshots
        headless: Run browser headlessly
        timeout_ms: Page timeout in ms

    Returns:
        dict with keys:
            - available: bool | None (None if CAPTCHA needed)
            - captcha_needed: bool
            - captcha_image_path: str | None
            - result_text: str
            - screenshot_path: str
            - error: str | None
    """
    screenshot_path = Path(screenshot_dir)
    screenshot_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {
        "available": None,
        "captcha_needed": False,
        "captcha_image_path": None,
        "result_text": "",
        "screenshot_path": "",
        "error": None,
        "automation_log": [],
    }

    def log(msg: str):
        entry = {"timestamp": datetime.now().isoformat(), "message": msg}
        result["automation_log"].append(entry)
        print(f"  [{entry['timestamp'][-12:]}] {msg}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1024, "height": 768},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        page = await context.new_page()
        page.set_default_timeout(timeout_ms)

        try:
            # Step 1: Navigate to name search
            log("Navigating to DE name search...")
            await page.goto(DE_NAME_SEARCH_URL, wait_until="networkidle")
            await page.screenshot(
                path=str(screenshot_path / f"{timestamp}_01_landing.png")
            )
            log("Landed on name search page")

            # Step 2: Accept disclaimer
            log("Accepting disclaimer...")
            disclaimer = page.locator(SELECTORS["disclaimer_checkbox"])
            if await disclaimer.count() > 0:
                await disclaimer.check()
                log("Disclaimer accepted")
            else:
                log("No disclaimer checkbox found (may already be accepted)")

            # Step 3: Select entity type
            type_value = ENTITY_TYPES.get(entity_type.upper(), "Y")
            log(f"Selecting entity type: {entity_type} (value={type_value})")
            await page.select_option(SELECTORS["entity_type"], value=type_value)

            # Step 4: Select entity ending
            log(f"Selecting entity ending: {entity_ending}")
            await page.select_option(SELECTORS["entity_ending"], value=entity_ending)

            # Step 5: Enter entity name
            log(f"Entering entity name: {entity_name}")
            await page.fill(SELECTORS["entity_name"], entity_name)

            await page.screenshot(
                path=str(screenshot_path / f"{timestamp}_02_form_filled.png")
            )

            # Step 6: Handle CAPTCHA
            captcha_img = page.locator(SELECTORS["captcha_image"])
            if await captcha_img.count() > 0:
                # Screenshot the CAPTCHA
                captcha_path = str(
                    screenshot_path / f"{timestamp}_captcha.png"
                )
                await captcha_img.screenshot(path=captcha_path)
                result["captcha_image_path"] = captcha_path
                log(f"CAPTCHA image saved to {captcha_path}")

                if captcha_code:
                    # We have a pre-solved CAPTCHA
                    log(f"Entering CAPTCHA code: {captcha_code}")
                    await page.fill(SELECTORS["captcha_input"], captcha_code)
                else:
                    # Need human to solve
                    result["captcha_needed"] = True
                    log("CAPTCHA code needed — returning for human solving")
                    await page.screenshot(
                        path=str(
                            screenshot_path / f"{timestamp}_03_captcha_needed.png"
                        )
                    )
                    result["screenshot_path"] = str(
                        screenshot_path / f"{timestamp}_03_captcha_needed.png"
                    )
                    await browser.close()
                    return result

            # Step 7: Submit search
            log("Submitting search...")
            async with page.expect_navigation():
                await page.click(SELECTORS["search_button"])

            await page.wait_for_load_state("networkidle")
            await page.screenshot(
                path=str(screenshot_path / f"{timestamp}_04_results.png")
            )
            result["screenshot_path"] = str(
                screenshot_path / f"{timestamp}_04_results.png"
            )

            # Step 8: Parse results
            log("Parsing results...")
            page_text = await page.inner_text("body")

            if "is available" in page_text.lower():
                result["available"] = True
                result["result_text"] = "Name is available"
                log("RESULT: Name is AVAILABLE")
            elif "is not available" in page_text.lower() or "is reserved" in page_text.lower():
                result["available"] = False
                result["result_text"] = "Name is NOT available"
                log("RESULT: Name is NOT AVAILABLE")
            elif "already exists" in page_text.lower():
                result["available"] = False
                result["result_text"] = "Entity already exists"
                log("RESULT: Entity ALREADY EXISTS")
            elif "invalid" in page_text.lower() and "captcha" in page_text.lower():
                result["captcha_needed"] = True
                result["result_text"] = "CAPTCHA was incorrect"
                result["error"] = "captcha_invalid"
                log("RESULT: CAPTCHA was incorrect — needs retry")
            else:
                result["result_text"] = page_text[:500]
                log(f"RESULT: Unrecognized response — {page_text[:200]}")

        except Exception as e:
            result["error"] = str(e)
            log(f"ERROR: {e}")
            try:
                await page.screenshot(
                    path=str(screenshot_path / f"{timestamp}_error.png")
                )
                result["screenshot_path"] = str(
                    screenshot_path / f"{timestamp}_error.png"
                )
            except Exception:
                pass

        finally:
            await browser.close()

    return result


async def main():
    parser = argparse.ArgumentParser(description="Check DE entity name availability")
    parser.add_argument("--name", required=True, help="Entity name to check")
    parser.add_argument("--type", default="LLC", help="Entity type (LLC, CORPORATION, LP)")
    parser.add_argument("--ending", default="L.L.C.", help="Entity ending")
    parser.add_argument("--captcha", default=None, help="Pre-solved CAPTCHA code")
    parser.add_argument("--screenshots", default="/tmp/de-name-check", help="Screenshot directory")
    parser.add_argument("--visible", action="store_true", help="Run browser visibly")
    args = parser.parse_args()

    result = await check_name_availability(
        entity_name=args.name,
        entity_type=args.type,
        entity_ending=args.ending,
        captcha_code=args.captcha,
        screenshot_dir=args.screenshots,
        headless=not args.visible,
    )

    print(f"\n{'='*50}")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
