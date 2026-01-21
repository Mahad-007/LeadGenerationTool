#!/usr/bin/env python3
"""
Homepage Audit Script for Shopify UI Audit MVP.

This script uses Playwright to audit verified Shopify store homepages.
It captures screenshots, console errors, and performance metrics.

Features:
- Desktop viewport (1440x900) and mobile viewport (390x844)
- Full page screenshots
- Console error capture
- Performance metrics (LCP, load timing)
- DOM text extraction for AI analysis
- Homepage only - no crawling

Usage:
    python scripts/audit_homepage.py [--url "https://example.com"]

If no URL is provided, processes all verified Shopify sites.

Requirements:
    pip install playwright
    playwright install chromium
"""

import sys
import json
import asyncio
import logging
import argparse
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    SHOPIFY_SITES_FILE,
    AUDIT_RESULTS_FILE,
    SCREENSHOTS_DIR,
    DESKTOP_VIEWPORT,
    MOBILE_VIEWPORT,
    PAGE_LOAD_TIMEOUT,
    SCREENSHOT_QUALITY,
    POST_LOAD_WAIT,
    LCP_THRESHOLD_MS,
    DESKTOP_FOLD_LINE,
    MOBILE_FOLD_LINE,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def generate_safe_filename(url: str) -> str:
    """Generate a safe filename from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    # Create short hash for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    # Sanitize domain name
    safe_domain = re.sub(r"[^\w\-]", "_", domain)
    return f"{safe_domain}_{url_hash}"


class HomepageAuditor:
    """Audits Shopify store homepages using Playwright."""

    def __init__(self, screenshots_dir: Path):
        """
        Initialize auditor.

        Args:
            screenshots_dir: Directory to save screenshots
        """
        self.screenshots_dir = screenshots_dir
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def _capture_console_errors(self, page: Page) -> List[Dict]:
        """
        Set up console error capture.

        Returns list of captured console messages.
        """
        console_messages = []

        def handle_console(msg):
            if msg.type in ("error", "warning"):
                console_messages.append({
                    "type": msg.type,
                    "text": msg.text,
                    "location": msg.location if hasattr(msg, "location") else None,
                })

        page.on("console", handle_console)
        return console_messages

    async def _get_performance_metrics(self, page: Page) -> Dict:
        """
        Extract performance metrics from page.

        Returns dictionary with timing metrics.
        """
        metrics = {
            "lcp": None,
            "fcp": None,
            "dom_content_loaded": None,
            "load_complete": None,
            "ttfb": None,
        }

        try:
            # Get navigation timing
            timing = await page.evaluate("""
                () => {
                    const timing = performance.timing;
                    const navStart = timing.navigationStart;
                    return {
                        domContentLoaded: timing.domContentLoadedEventEnd - navStart,
                        loadComplete: timing.loadEventEnd - navStart,
                        ttfb: timing.responseStart - navStart,
                    };
                }
            """)
            metrics["dom_content_loaded"] = timing.get("domContentLoaded")
            metrics["load_complete"] = timing.get("loadComplete")
            metrics["ttfb"] = timing.get("ttfb")

            # Get LCP using PerformanceObserver results
            lcp = await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        new PerformanceObserver((list) => {
                            const entries = list.getEntries();
                            const lastEntry = entries[entries.length - 1];
                            resolve(lastEntry ? lastEntry.startTime : null);
                        }).observe({type: 'largest-contentful-paint', buffered: true});

                        // Timeout fallback
                        setTimeout(() => resolve(null), 1000);
                    });
                }
            """)
            metrics["lcp"] = lcp

            # Get FCP
            fcp = await page.evaluate("""
                () => {
                    const fcp = performance.getEntriesByName('first-contentful-paint')[0];
                    return fcp ? fcp.startTime : null;
                }
            """)
            metrics["fcp"] = fcp

        except Exception as e:
            logger.warning(f"Failed to get performance metrics: {e}")

        return metrics

    async def _extract_dom_info(self, page: Page, viewport_type: str) -> Dict:
        """
        Extract DOM information for analysis.

        Args:
            page: Playwright page object
            viewport_type: "desktop" or "mobile"

        Returns:
            Dictionary with DOM analysis data
        """
        fold_line = DESKTOP_FOLD_LINE if viewport_type == "desktop" else MOBILE_FOLD_LINE

        try:
            dom_info = await page.evaluate(f"""
                () => {{
                    const foldLine = {fold_line};

                    // Get all buttons and links that could be CTAs
                    const ctaSelectors = 'button, a.btn, a.button, [class*="cta"], [class*="buy"], [class*="shop"], [class*="add-to-cart"], input[type="submit"]';
                    const ctaElements = document.querySelectorAll(ctaSelectors);

                    const ctas = [];
                    ctaElements.forEach(el => {{
                        const rect = el.getBoundingClientRect();
                        const text = el.innerText || el.value || '';
                        if (text.trim()) {{
                            ctas.push({{
                                text: text.trim().substring(0, 100),
                                top: rect.top,
                                visible: rect.top < foldLine,
                                tagName: el.tagName.toLowerCase(),
                            }});
                        }}
                    }});

                    // Get hero/header section info
                    const heroSelectors = '[class*="hero"], [class*="banner"], [class*="header"], header, [class*="masthead"]';
                    const heroEl = document.querySelector(heroSelectors);
                    const heroInfo = heroEl ? {{
                        height: heroEl.getBoundingClientRect().height,
                        hasImage: !!heroEl.querySelector('img'),
                    }} : null;

                    // Get page title and main heading
                    const h1 = document.querySelector('h1');
                    const title = document.title;

                    // Check for broken images
                    const images = document.querySelectorAll('img');
                    const brokenImages = [];
                    images.forEach(img => {{
                        if (!img.complete || img.naturalWidth === 0) {{
                            brokenImages.push(img.src);
                        }}
                    }});

                    // Get internal links
                    const links = document.querySelectorAll('a[href^="/"], a[href^="' + window.location.origin + '"]');
                    const internalLinks = [];
                    links.forEach(link => {{
                        internalLinks.push({{
                            href: link.href,
                            text: link.innerText.trim().substring(0, 50),
                        }});
                    }});

                    // Get viewport info
                    const viewportHeight = window.innerHeight;
                    const pageHeight = document.documentElement.scrollHeight;

                    return {{
                        title: title,
                        h1: h1 ? h1.innerText.trim() : null,
                        ctas: ctas.slice(0, 20),
                        ctasAboveFold: ctas.filter(c => c.visible).length,
                        ctasBelowFold: ctas.filter(c => !c.visible).length,
                        heroInfo: heroInfo,
                        brokenImages: brokenImages.slice(0, 10),
                        internalLinksCount: internalLinks.length,
                        viewportHeight: viewportHeight,
                        pageHeight: pageHeight,
                        foldLine: foldLine,
                    }};
                }}
            """)
            return dom_info

        except Exception as e:
            logger.warning(f"Failed to extract DOM info: {e}")
            return {}

    async def _check_internal_links(self, page: Page) -> List[Dict]:
        """
        Check for potentially broken internal links (without crawling).

        Returns list of suspicious links found in the DOM.
        """
        try:
            links = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a[href]');
                    const issues = [];

                    links.forEach(link => {
                        const href = link.href;
                        const text = link.innerText.trim();

                        // Check for empty or javascript: links
                        if (!href || href === '#' || href.startsWith('javascript:')) {
                            issues.push({
                                type: 'empty_or_invalid',
                                href: href,
                                text: text.substring(0, 50),
                            });
                        }
                    });

                    return issues.slice(0, 10);
                }
            """)
            return links
        except Exception as e:
            logger.warning(f"Failed to check internal links: {e}")
            return []

    async def audit_single_viewport(
        self,
        page: Page,
        url: str,
        viewport: Dict,
        viewport_type: str,
        base_filename: str,
    ) -> Dict:
        """
        Audit page in a specific viewport.

        Args:
            page: Playwright page object
            url: URL being audited
            viewport: Viewport dimensions
            viewport_type: "desktop" or "mobile"
            base_filename: Base filename for screenshots

        Returns:
            Audit results for this viewport
        """
        result = {
            "viewport_type": viewport_type,
            "viewport": viewport,
            "screenshot_path": None,
            "console_errors": [],
            "performance_metrics": {},
            "dom_info": {},
            "link_issues": [],
            "error": None,
        }

        try:
            # Set viewport
            await page.set_viewport_size(viewport)

            # Set up console error capture
            console_errors = []

            def handle_console(msg):
                if msg.type in ("error", "warning"):
                    console_errors.append({
                        "type": msg.type,
                        "text": msg.text[:500],  # Truncate long messages
                    })

            page.on("console", handle_console)

            # Navigate to page
            logger.info(f"  Loading {viewport_type} view...")
            await page.goto(url, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)

            # Wait for dynamic content
            await page.wait_for_timeout(POST_LOAD_WAIT)

            # Get performance metrics
            result["performance_metrics"] = await self._get_performance_metrics(page)

            # Extract DOM info
            result["dom_info"] = await self._extract_dom_info(page, viewport_type)

            # Check internal links
            result["link_issues"] = await self._check_internal_links(page)

            # Capture console errors
            result["console_errors"] = console_errors

            # Take screenshot - viewport only (what users actually see first)
            screenshot_filename = f"{base_filename}_{viewport_type}.png"
            screenshot_path = self.screenshots_dir / screenshot_filename

            await page.screenshot(
                path=str(screenshot_path),
                full_page=False,  # Viewport only - shows the actual first impression
                type="png",
            )
            result["screenshot_path"] = str(screenshot_path)
            logger.info(f"  Screenshot saved: {screenshot_filename}")

        except PlaywrightTimeout:
            result["error"] = "Page load timeout"
            logger.warning(f"  Timeout loading {url} in {viewport_type} view")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"  Error auditing {url} in {viewport_type} view: {e}")

        return result

    async def audit_homepage(self, browser: Browser, url: str) -> Dict:
        """
        Perform full audit of a homepage.

        Args:
            browser: Playwright browser instance
            url: URL to audit

        Returns:
            Complete audit results
        """
        logger.info(f"Auditing: {url}")

        base_filename = generate_safe_filename(url)

        result = {
            "url": url,
            "audited_at": datetime.utcnow().isoformat(),
            "desktop": None,
            "mobile": None,
            "error": None,
        }

        try:
            # Create browser context
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # Audit desktop viewport
            result["desktop"] = await self.audit_single_viewport(
                page, url, DESKTOP_VIEWPORT, "desktop", base_filename
            )

            # Audit mobile viewport
            result["mobile"] = await self.audit_single_viewport(
                page, url, MOBILE_VIEWPORT, "mobile", base_filename
            )

            await context.close()

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error auditing {url}: {e}")

        return result


def load_shopify_sites() -> List[str]:
    """Load verified Shopify site URLs."""
    urls = []

    if not SHOPIFY_SITES_FILE.exists():
        logger.error(f"Shopify sites file not found: {SHOPIFY_SITES_FILE}")
        return urls

    try:
        with open(SHOPIFY_SITES_FILE, "r") as f:
            data = json.load(f)

        for site in data.get("shopify_sites", []):
            urls.append(site["url"])

        logger.info(f"Loaded {len(urls)} verified Shopify sites")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Shopify sites file: {e}")

    return urls


async def main_async(urls: List[str]):
    """Async main function to run audits."""
    auditor = HomepageAuditor(SCREENSHOTS_DIR)
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] Processing {url}")
            result = await auditor.audit_homepage(browser, url)
            results.append(result)

        await browser.close()

    return results


def main():
    """Main entry point for homepage auditing."""
    parser = argparse.ArgumentParser(
        description="Audit Shopify store homepages using Playwright"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Single URL to audit (overrides shopify_sites.json)",
    )
    args = parser.parse_args()

    # Determine URLs to audit
    if args.url:
        urls = [args.url]
        logger.info(f"Auditing single URL: {args.url}")
    else:
        urls = load_shopify_sites()
        if not urls:
            logger.error("No URLs to audit. Run verify_shopify.py first.")
            sys.exit(1)

    # Run audits
    results = asyncio.run(main_async(urls))

    # Calculate summary stats
    successful = sum(1 for r in results if r["error"] is None)
    failed = len(results) - successful

    # Prepare output
    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "total_audited": len(results),
            "successful": successful,
            "failed": failed,
            "screenshots_dir": str(SCREENSHOTS_DIR),
        },
        "audits": results,
    }

    # Ensure output directory exists
    AUDIT_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(AUDIT_RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Audit complete. Results saved to {AUDIT_RESULTS_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"  Total sites audited: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Screenshots: {SCREENSHOTS_DIR}")
    print("=" * 60)

    # Print individual results
    for result in results:
        status = "OK" if result["error"] is None else f"ERROR: {result['error']}"
        console_errors = 0
        if result["desktop"] and result["desktop"].get("console_errors"):
            console_errors += len(result["desktop"]["console_errors"])
        if result["mobile"] and result["mobile"].get("console_errors"):
            console_errors += len(result["mobile"]["console_errors"])

        print(f"  {result['url']}")
        print(f"    Status: {status}")
        if console_errors > 0:
            print(f"    Console errors: {console_errors}")

    print(f"\nOutput: {AUDIT_RESULTS_FILE}")


if __name__ == "__main__":
    main()
