#!/usr/bin/env python3
"""
Shopify Verification Script for UI Audit MVP.

This script verifies whether discovered sites are Shopify stores by checking
multiple signals in the HTML source and HTTP headers.

Features:
- Checks multiple Shopify indicators (CDN, scripts, headers, etc.)
- Calculates confidence score based on weighted signals
- Uses rotating user agents
- Applies strict rate limiting
- Discards non-Shopify sites automatically

Usage:
    python scripts/verify_shopify.py [--min-confidence 60]
"""

import sys
import json
import time
import random
import logging
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    USER_AGENTS_FILE,
    DISCOVERED_SITES_FILE,
    SHOPIFY_SITES_FILE,
    MIN_REQUEST_DELAY,
    MAX_REQUEST_DELAY,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    MIN_SHOPIFY_CONFIDENCE,
    SHOPIFY_SIGNALS,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class UserAgentRotator:
    """Manages rotation of user agents for requests."""

    def __init__(self, user_agents_file: Path):
        self.user_agents = self._load_user_agents(user_agents_file)
        if not self.user_agents:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]

    def _load_user_agents(self, filepath: Path) -> List[str]:
        agents = []
        try:
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        agents.append(line)
        except FileNotFoundError:
            logger.warning(f"User agents file not found: {filepath}")
        return agents

    def get_random(self) -> str:
        return random.choice(self.user_agents)


class RateLimiter:
    """Enforces rate limiting between requests."""

    def __init__(self, min_delay: float, max_delay: float):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0

    def wait(self):
        elapsed = time.time() - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()


class ShopifyVerifier:
    """Verifies if a website is built on Shopify platform."""

    def __init__(self, user_agent_rotator: UserAgentRotator, rate_limiter: RateLimiter):
        self.ua_rotator = user_agent_rotator
        self.rate_limiter = rate_limiter
        self.session = requests.Session()

    def _fetch_page(self, url: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Fetch page HTML and headers.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (html_content, headers_dict) or (None, None) on failure
        """
        self.rate_limiter.wait()

        headers = {
            "User-Agent": self.ua_rotator.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                )
                response.raise_for_status()
                return response.text, dict(response.headers)

            except requests.RequestException as e:
                logger.warning(f"Request failed for {url} (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(3 * (attempt + 1))

        return None, None

    def _check_html_signals(self, html: str) -> Dict[str, bool]:
        """
        Check HTML content for Shopify signals.

        Args:
            html: HTML content of the page

        Returns:
            Dictionary of signal -> found mapping
        """
        signals_found = {}
        html_lower = html.lower()

        # Check for CDN references
        signals_found["cdn.shopify.com"] = "cdn.shopify.com" in html_lower

        # Check for myshopify.com references
        signals_found["myshopify.com"] = "myshopify.com" in html_lower

        # Check for Shopify.theme JavaScript object
        signals_found["Shopify.theme"] = "shopify.theme" in html_lower or "window.shopify" in html_lower

        # Check for shopify-section elements
        signals_found["shopify-section"] = "shopify-section" in html_lower

        # Check for Shopify Pay
        signals_found["shopify_pay"] = "shopify_pay" in html_lower or "shopify-payment" in html_lower

        # Check for cart.js endpoint
        signals_found["/cart.js"] = "/cart.js" in html_lower or "cart.js" in html_lower

        # Check for Shopify access token references
        signals_found["shopify.accessToken"] = "accesstoken" in html_lower and "shopify" in html_lower

        # Additional checks via BeautifulSoup
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Check for Shopify meta tags
            for meta in soup.find_all("meta"):
                content = str(meta.get("content", "")).lower()
                name = str(meta.get("name", "")).lower()
                if "shopify" in content or "shopify" in name:
                    signals_found["shopify_meta"] = True
                    break

            # Check for Shopify scripts
            for script in soup.find_all("script", src=True):
                src = script.get("src", "").lower()
                if "shopify" in src or "cdn.shopify" in src:
                    signals_found["shopify_scripts"] = True
                    break

            # Check for Shopify-specific data attributes
            shopify_attrs = soup.find_all(attrs={"data-shopify": True})
            if shopify_attrs:
                signals_found["data-shopify"] = True

        except Exception as e:
            logger.debug(f"BeautifulSoup parsing error: {e}")

        return signals_found

    def _check_header_signals(self, headers: Dict) -> Dict[str, bool]:
        """
        Check HTTP headers for Shopify signals.

        Args:
            headers: Response headers dictionary

        Returns:
            Dictionary of signal -> found mapping
        """
        signals_found = {}

        # Normalize header names to lowercase
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # Check for X-ShopId header
        signals_found["X-ShopId"] = "x-shopid" in headers_lower

        # Check for X-Shopify-Stage header
        signals_found["X-Shopify-Stage"] = "x-shopify-stage" in headers_lower

        # Check server header for Shopify
        server = headers_lower.get("server", "").lower()
        if "shopify" in server:
            signals_found["server_shopify"] = True

        # Check for Shopify cookies
        cookies = headers_lower.get("set-cookie", "").lower()
        if "shopify" in cookies or "_shopify" in cookies:
            signals_found["shopify_cookies"] = True

        return signals_found

    def _calculate_confidence(self, html_signals: Dict[str, bool], header_signals: Dict[str, bool]) -> int:
        """
        Calculate confidence score based on detected signals.

        Args:
            html_signals: Signals found in HTML
            header_signals: Signals found in headers

        Returns:
            Confidence score (0-100)
        """
        total_score = 0

        # Score HTML signals
        for signal, found in html_signals.items():
            if found and signal in SHOPIFY_SIGNALS:
                total_score += SHOPIFY_SIGNALS[signal]

        # Score header signals
        for signal, found in header_signals.items():
            if found and signal in SHOPIFY_SIGNALS:
                total_score += SHOPIFY_SIGNALS[signal]

        # Cap at 100
        return min(total_score, 100)

    def verify(self, url: str) -> Dict:
        """
        Verify if a URL is a Shopify store.

        Args:
            url: URL to verify

        Returns:
            Verification result dictionary
        """
        logger.info(f"Verifying: {url}")

        result = {
            "url": url,
            "is_shopify": False,
            "confidence": 0,
            "signals_found": [],
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }

        # Fetch page
        html, headers = self._fetch_page(url)

        if not html:
            result["error"] = "Failed to fetch page"
            return result

        # Check signals
        html_signals = self._check_html_signals(html)
        header_signals = self._check_header_signals(headers or {})

        # Combine signals
        all_signals = {**html_signals, **header_signals}
        signals_found = [signal for signal, found in all_signals.items() if found]

        # Calculate confidence
        confidence = self._calculate_confidence(html_signals, header_signals)

        result["signals_found"] = signals_found
        result["confidence"] = confidence
        result["is_shopify"] = confidence >= MIN_SHOPIFY_CONFIDENCE

        # Log result
        status = "SHOPIFY" if result["is_shopify"] else "NOT SHOPIFY"
        logger.info(f"  {status} (confidence: {confidence}%, signals: {len(signals_found)})")

        return result


def normalize_url(url: str) -> Optional[str]:
    """
    Normalize URL to standard format, handling breadcrumb-style URLs.

    Args:
        url: Raw URL string

    Returns:
        Normalized URL or None if invalid
    """
    try:
        # Clean up breadcrumb-style URLs from search results (e.g., "site.com › path › page")
        if "›" in url or " > " in url:
            url = url.replace(" › ", "/").replace("›", "/")
            url = url.replace(" > ", "/").replace(">", "/")
            url = url.replace(" ", "")
            url = url.rstrip("…").rstrip(".")

        # Skip if still contains spaces (invalid URL)
        if " " in url:
            return None

        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Basic validation
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.netloc or "." not in parsed.netloc:
            return None

        return url

    except Exception:
        return None


def load_discovered_sites() -> List[str]:
    """Load discovered URLs from discovery output file."""
    urls = []

    if not DISCOVERED_SITES_FILE.exists():
        logger.error(f"Discovery file not found: {DISCOVERED_SITES_FILE}")
        return urls

    try:
        with open(DISCOVERED_SITES_FILE, "r") as f:
            data = json.load(f)

        # Extract URLs from all discoveries
        for discovery in data.get("discoveries", []):
            for url in discovery.get("urls", []):
                # Normalize URL to handle breadcrumb-style formats
                normalized = normalize_url(url)
                if normalized:
                    urls.append(normalized)

        # Deduplicate
        urls = list(set(urls))
        logger.info(f"Loaded {len(urls)} unique URLs from discovery file")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse discovery file: {e}")

    return urls


def main():
    """Main entry point for Shopify verification."""
    parser = argparse.ArgumentParser(
        description="Verify discovered sites as Shopify stores"
    )
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=MIN_SHOPIFY_CONFIDENCE,
        help=f"Minimum confidence score to classify as Shopify (default: {MIN_SHOPIFY_CONFIDENCE})",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Single URL to verify (overrides discovery file)",
    )
    args = parser.parse_args()

    # Determine URLs to verify
    if args.url:
        urls = [args.url]
        logger.info(f"Verifying single URL: {args.url}")
    else:
        urls = load_discovered_sites()
        if not urls:
            logger.error("No URLs to verify. Run discover_sites.py first.")
            sys.exit(1)

    # Initialize components
    ua_rotator = UserAgentRotator(USER_AGENTS_FILE)
    rate_limiter = RateLimiter(MIN_REQUEST_DELAY, MAX_REQUEST_DELAY)
    verifier = ShopifyVerifier(ua_rotator, rate_limiter)

    # Verify each URL
    results = []
    shopify_sites = []

    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] Processing {url}")
        try:
            result = verifier.verify(url)
            results.append(result)

            if result["is_shopify"]:
                shopify_sites.append(result)

        except Exception as e:
            logger.error(f"Error verifying {url}: {e}")
            results.append({
                "url": url,
                "is_shopify": False,
                "confidence": 0,
                "signals_found": [],
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            })

    # Prepare output
    output = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_verified": len(results),
            "shopify_count": len(shopify_sites),
            "non_shopify_count": len(results) - len(shopify_sites),
            "min_confidence_threshold": args.min_confidence,
        },
        "shopify_sites": shopify_sites,
        "verification_log": results,
    }

    # Ensure output directory exists
    SHOPIFY_SITES_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(SHOPIFY_SITES_FILE, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Verification complete. Results saved to {SHOPIFY_SITES_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"  Total URLs verified: {len(results)}")
    print(f"  Confirmed Shopify stores: {len(shopify_sites)}")
    print(f"  Non-Shopify sites: {len(results) - len(shopify_sites)}")
    print(f"  Confidence threshold: {args.min_confidence}%")
    print("=" * 60)

    if shopify_sites:
        print("\nConfirmed Shopify stores:")
        for site in shopify_sites:
            print(f"  - {site['url']} (confidence: {site['confidence']}%)")

    print(f"\nOutput: {SHOPIFY_SITES_FILE}")


if __name__ == "__main__":
    main()
