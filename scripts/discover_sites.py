#!/usr/bin/env python3
"""
Site Discovery Script for Shopify UI Audit MVP.

This script discovers potential Shopify stores by scraping Google and DuckDuckGo
search results for given niche keywords using Playwright for reliable scraping.

Features:
- Uses Playwright for JavaScript-rendered search results
- Scrapes Google and DuckDuckGo
- Applies strict rate limiting (≥10s between requests)
- Deduplicates domains
- Outputs normalized URLs

Usage:
    python scripts/discover_sites.py [--niche "keyword"]

If no niche is provided, reads from input/niches.txt
"""

import sys
import json
import time
import random
import logging
import argparse
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin, quote_plus, unquote
from datetime import datetime, timezone
from typing import List, Dict, Set, Optional

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    NICHES_FILE,
    USER_AGENTS_FILE,
    DISCOVERED_SITES_FILE,
    MIN_REQUEST_DELAY,
    MAX_REQUEST_DELAY,
    MAX_SITES_PER_NICHE,
    SEARCH_QUERY_TEMPLATES,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Built-in database of known Shopify stores by niche (fallback when search engines block)
SHOPIFY_STORE_DATABASE = {
    "shoes": [
        "https://kizik.com",
        "https://allbirds.com",
        "https://birdies.com",
        "https://koio.co",
        "https://greats.com",
        "https://rothys.com",
        "https://nisolo.com",
        "https://thursdayboots.com",
        "https://vfrfrfr.com",
        "https://byfarshoes.com",
        "https://dolcevita.com",
        "https://maguireshoes.com",
    ],
    "fashion": [
        "https://fashionnova.com",
        "https://gymshark.com",
        "https://cettire.com",
        "https://princesspolly.com",
        "https://hellomolly.com",
        "https://beginning-boutique.com",
        "https://meshki.com.au",
        "https://boohoo.com",
    ],
    "jewelry": [
        "https://mejuri.com",
        "https://kendrascott.com",
        "https://gorjana.com",
        "https://baublebar.com",
        "https://stelladot.com",
        "https://puravidabracelets.com",
        "https://ringconcierge.com",
    ],
    "beauty": [
        "https://colourpop.com",
        "https://morphe.com",
        "https://kyliecosmetics.com",
        "https://fentybeauty.com",
        "https://milkmakeup.com",
        "https://summerfridays.com",
        "https://tatcha.com",
    ],
    "fitness": [
        "https://gymshark.com",
        "https://alphaleteathletics.com",
        "https://youngla.com",
        "https://buffbunny.com",
        "https://nvgtn.com",
        "https://setactive.co",
    ],
    "home": [
        "https://brooklinen.com",
        "https://parachutehome.com",
        "https://burrow.com",
        "https://article.com",
        "https://floydhome.com",
        "https://thesill.com",
    ],
    "food": [
        "https://drinkmudwtr.com",
        "https://magicspoon.com",
        "https://drink8greens.com",
        "https://drinkag1.com",
        "https://lairdsuperfood.com",
    ],
    "pets": [
        "https://barkbox.com",
        "https://wildone.com",
        "https://fable.co",
        "https://maxbone.com",
        "https://kfrfrong.com",
    ],
    "default": [
        "https://allbirds.com",
        "https://gymshark.com",
        "https://fashionnova.com",
        "https://colourpop.com",
        "https://brooklinen.com",
        "https://mejuri.com",
        "https://bombas.com",
        "https://ruggable.com",
    ],
}

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class UserAgentRotator:
    """Manages rotation of user agents for requests."""

    def __init__(self, user_agents_file: Path):
        """
        Initialize with user agents from file.

        Args:
            user_agents_file: Path to file containing user agents (one per line)
        """
        self.user_agents = self._load_user_agents(user_agents_file)
        if not self.user_agents:
            # Fallback user agent
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            logger.warning("No user agents loaded, using fallback")

    def _load_user_agents(self, filepath: Path) -> List[str]:
        """Load user agents from file, ignoring comments and empty lines."""
        agents = []
        try:
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        agents.append(line)
            logger.info(f"Loaded {len(agents)} user agents")
        except FileNotFoundError:
            logger.error(f"User agents file not found: {filepath}")
        return agents

    def get_random(self) -> str:
        """Get a random user agent."""
        return random.choice(self.user_agents)


class RateLimiter:
    """Enforces rate limiting between requests."""

    def __init__(self, min_delay: float, max_delay: float):
        """
        Initialize rate limiter.

        Args:
            min_delay: Minimum seconds between requests
            max_delay: Maximum seconds between requests
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0

    def wait(self):
        """Wait appropriate time before next request."""
        elapsed = time.time() - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()


def normalize_url(url: str) -> Optional[str]:
    """
    Normalize URL to standard format.

    Args:
        url: Raw URL string

    Returns:
        Normalized URL or None if invalid
    """
    try:
        # Clean up breadcrumb-style URLs from search results (e.g., "site.com › path › page")
        # These use › (U+203A) or > as path separators
        if "›" in url or " > " in url:
            # Replace breadcrumb separators with /
            url = url.replace(" › ", "/").replace("›", "/")
            url = url.replace(" > ", "/").replace(">", "/")
            # Remove any remaining spaces
            url = url.replace(" ", "")
            # Remove trailing ellipsis
            url = url.rstrip("…").rstrip(".")

        # Skip URLs that are clearly not valid domains
        if " " in url and "›" not in url and ">" not in url:
            return None

        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)

        # Validate domain
        if not parsed.netloc:
            return None

        # Remove www. prefix for consistency
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Skip social media, marketplaces, and non-store domains
        excluded_domains = [
            # Social media
            "facebook.com",
            "instagram.com",
            "twitter.com",
            "youtube.com",
            "pinterest.com",
            "linkedin.com",
            "tiktok.com",
            "reddit.com",
            "snapchat.com",
            # Marketplaces
            "amazon.com",
            "ebay.com",
            "etsy.com",
            "alibaba.com",
            "aliexpress.com",
            "walmart.com",
            "target.com",
            # Search engines
            "bing.com",
            "google.com",
            "duckduckgo.com",
            "yahoo.com",
            "baidu.com",
            # Reference sites
            "wikipedia.org",
            "wikimedia.org",
            "github.com",
            "stackoverflow.com",
            "medium.com",
            "quora.com",
            "zhihu.com",
            # Website builders (competitors)
            "wordpress.com",
            "blogspot.com",
            "tumblr.com",
            "weebly.com",
            "wix.com",
            "squarespace.com",
            # Tech companies
            "microsoft.com",
            "apple.com",
            "adobe.com",
            # Shipping
            "usps.com",
            "ups.com",
            "fedex.com",
            # Government/Education
            "gov",
            "edu",
            # News/Media
            "crunchyroll.com",
            "cbsnews.com",
            "cnn.com",
            "bbc.com",
            "nytimes.com",
            "forbes.com",
            "businessinsider.com",
            # Chinese sites
            "163.com",
            "qq.com",
            "taobao.com",
            "jd.com",
            "weibo.com",
            "bilibili.com",
            "douyin.com",
            # Shopify itself (not stores)
            "shopify.com",
            "shopify.dev",
            "shopifycdn.com",
            # Other non-stores
            "trustpilot.com",
            "yelp.com",
            "glassdoor.com",
            "indeed.com",
            "craigslist.org",
            "lenovo.com",
            "dell.com",
            "hp.com",
            "samsung.com",
            "lg.com",
            "sony.com",
            # Additional non-stores from testing
            "freepik.com",
            "tripadvisor",
            "openai.com",
            "whatsapp.com",
            "yandex.com",
            "office.com",
            "asus.com",
            "about.google",
            "translate.google",
            "ok.ru",
            "androidauthority.com",
            "thefork.",
            "allbiz.",
        ]
        for excluded in excluded_domains:
            if excluded in domain:
                return None

        # Return normalized URL (homepage only)
        return f"https://{domain}"

    except Exception as e:
        logger.debug(f"URL normalization failed for {url}: {e}")
        return None


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL for deduplication."""
    normalized = normalize_url(url)
    if normalized:
        return urlparse(normalized).netloc
    return None


class SearchEngineScraper:
    """Scrapes search engines for potential Shopify store URLs using Playwright."""

    def __init__(self, user_agent_rotator: UserAgentRotator, rate_limiter: RateLimiter):
        """
        Initialize scraper.

        Args:
            user_agent_rotator: UserAgentRotator instance
            rate_limiter: RateLimiter instance
        """
        self.ua_rotator = user_agent_rotator
        self.rate_limiter = rate_limiter
        self.playwright = None
        self.browser = None

    def _init_browser(self):
        """Initialize Playwright browser if not already done."""
        if self.browser is None:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            logger.info("Playwright browser initialized")

    def _close_browser(self):
        """Close Playwright browser."""
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def search_google(self, query: str) -> Set[str]:
        """
        Search Google and extract URLs using Playwright.

        Args:
            query: Search query string

        Returns:
            Set of discovered URLs
        """
        urls = set()
        logger.info(f"Searching Google for: {query}")

        self._init_browser()
        self.rate_limiter.wait()

        try:
            context = self.browser.new_context(
                user_agent=self.ua_rotator.get_random(),
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            # Go to Google
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num=30"
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)  # Let results load

            # Handle consent dialog if present
            try:
                consent_btn = page.locator("button:has-text('Accept all'), button:has-text('I agree')")
                if consent_btn.count() > 0:
                    consent_btn.first.click()
                    time.sleep(1)
            except:
                pass

            # Extract URLs from search results
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Google result selectors
            for link in soup.select("a[href^='http']:not([href*='google'])"):
                href = link.get("href", "")
                if href and not any(x in href for x in ["google.com", "youtube.com", "webcache"]):
                    normalized = normalize_url(href)
                    if normalized:
                        urls.add(normalized)

            # Also check cite elements
            for cite in soup.select("cite"):
                text = cite.get_text()
                if text and "›" not in text:
                    normalized = normalize_url(text.split(" ")[0])
                    if normalized:
                        urls.add(normalized)

            context.close()

        except PlaywrightTimeout:
            logger.warning(f"Timeout searching Google for: {query}")
        except Exception as e:
            logger.warning(f"Error searching Google: {e}")

        logger.info(f"Google found {len(urls)} URLs for query")
        return urls

    def search_duckduckgo(self, query: str) -> Set[str]:
        """
        Search DuckDuckGo and extract URLs using Playwright.

        Args:
            query: Search query string

        Returns:
            Set of discovered URLs
        """
        urls = set()
        logger.info(f"Searching DuckDuckGo for: {query}")

        self._init_browser()
        self.rate_limiter.wait()

        try:
            context = self.browser.new_context(
                user_agent=self.ua_rotator.get_random(),
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            # Go to DuckDuckGo
            search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)  # Let JS render results

            # Extract URLs from search results
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # DuckDuckGo result selectors
            for link in soup.select("a[data-testid='result-title-a'], a[href^='http']"):
                href = link.get("href", "")
                if href and href.startswith("http") and "duckduckgo" not in href:
                    # Handle DDG redirect URLs
                    if "uddg=" in href:
                        match = re.search(r"uddg=([^&]+)", href)
                        if match:
                            href = unquote(match.group(1))
                    normalized = normalize_url(href)
                    if normalized:
                        urls.add(normalized)

            context.close()

        except PlaywrightTimeout:
            logger.warning(f"Timeout searching DuckDuckGo for: {query}")
        except Exception as e:
            logger.warning(f"Error searching DuckDuckGo: {e}")

        logger.info(f"DuckDuckGo found {len(urls)} URLs for query")
        return urls

    def discover_for_niche(self, niche: str, use_database: bool = False) -> Dict:
        """
        Discover potential Shopify stores for a niche.

        Args:
            niche: Niche keyword to search for
            use_database: If True, use built-in database instead of search engines

        Returns:
            Dictionary with discovery results
        """
        all_urls = set()
        search_metadata = []

        # Use built-in database if requested or as fallback
        if use_database:
            logger.info(f"Using built-in Shopify store database for: {niche}")
            niche_lower = niche.lower()

            # Try exact match first, then partial match, then default
            if niche_lower in SHOPIFY_STORE_DATABASE:
                db_urls = SHOPIFY_STORE_DATABASE[niche_lower]
            else:
                # Try partial match
                db_urls = []
                for key, urls in SHOPIFY_STORE_DATABASE.items():
                    if niche_lower in key or key in niche_lower:
                        db_urls.extend(urls)
                        break
                if not db_urls:
                    db_urls = SHOPIFY_STORE_DATABASE.get("default", [])

            all_urls.update(db_urls[:MAX_SITES_PER_NICHE])
            search_metadata.append({
                "engine": "built_in_database",
                "query": niche,
                "results_count": len(all_urls),
            })
        else:
            # Try search engines first
            try:
                for template in SEARCH_QUERY_TEMPLATES[:2]:  # Limit to 2 templates to reduce blocking
                    query = template.format(niche=niche)

                    # Search Google
                    google_urls = self.search_google(query)
                    all_urls.update(google_urls)
                    search_metadata.append({
                        "engine": "google",
                        "query": query,
                        "results_count": len(google_urls),
                    })

                    # Search DuckDuckGo
                    ddg_urls = self.search_duckduckgo(query)
                    all_urls.update(ddg_urls)
                    search_metadata.append({
                        "engine": "duckduckgo",
                        "query": query,
                        "results_count": len(ddg_urls),
                    })

                    # Limit total results per niche
                    if len(all_urls) >= MAX_SITES_PER_NICHE:
                        logger.info(f"Reached max sites limit ({MAX_SITES_PER_NICHE}) for niche")
                        break

            finally:
                self._close_browser()

            # Fallback to database if no results from search engines
            if len(all_urls) == 0:
                logger.warning("Search engines returned 0 results, using built-in database as fallback")
                return self.discover_for_niche(niche, use_database=True)

        # Convert to list and limit
        urls_list = list(all_urls)[:MAX_SITES_PER_NICHE]

        return {
            "niche": niche,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "total_urls": len(urls_list),
            "urls": urls_list,
            "search_metadata": search_metadata,
            "source": "database" if use_database else "search_engines",
        }


def load_niches(filepath: Path) -> List[str]:
    """Load niche keywords from file."""
    niches = []
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    niches.append(line)
        logger.info(f"Loaded {len(niches)} niches from {filepath}")
    except FileNotFoundError:
        logger.error(f"Niches file not found: {filepath}")
    return niches


def main():
    """Main entry point for site discovery."""
    parser = argparse.ArgumentParser(
        description="Discover potential Shopify stores for given niches"
    )
    parser.add_argument(
        "--niche",
        type=str,
        help="Single niche keyword to search (overrides niches.txt)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing discovered_sites.json instead of overwriting",
    )
    parser.add_argument(
        "--use-database",
        action="store_true",
        help="Use built-in Shopify store database instead of search engines (recommended if search engines block)",
    )
    args = parser.parse_args()

    # Determine niches to process
    if args.niche:
        niches = [args.niche]
        logger.info(f"Using command-line niche: {args.niche}")
    else:
        niches = load_niches(NICHES_FILE)
        if not niches:
            logger.error("No niches to process. Add niches to input/niches.txt")
            sys.exit(1)

    # Initialize components
    ua_rotator = UserAgentRotator(USER_AGENTS_FILE)
    rate_limiter = RateLimiter(MIN_REQUEST_DELAY, MAX_REQUEST_DELAY)
    scraper = SearchEngineScraper(ua_rotator, rate_limiter)

    # Load existing data if appending
    existing_data = {"discoveries": [], "metadata": {}}
    if args.append and DISCOVERED_SITES_FILE.exists():
        try:
            with open(DISCOVERED_SITES_FILE, "r") as f:
                existing_data = json.load(f)
            logger.info(f"Loaded existing data with {len(existing_data.get('discoveries', []))} discoveries")
        except json.JSONDecodeError:
            logger.warning("Could not parse existing file, starting fresh")

    # Process each niche
    discoveries = existing_data.get("discoveries", [])
    existing_niches = {d["niche"] for d in discoveries}

    for niche in niches:
        if niche in existing_niches and args.append:
            logger.info(f"Skipping already discovered niche: {niche}")
            continue

        logger.info(f"=== Processing niche: {niche} ===")
        try:
            result = scraper.discover_for_niche(niche, use_database=args.use_database)
            discoveries.append(result)
            logger.info(f"Discovered {result['total_urls']} URLs for '{niche}'")
        except Exception as e:
            logger.error(f"Error processing niche '{niche}': {e}")
            continue

    # Prepare output
    output = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_niches": len(discoveries),
            "total_urls": sum(d["total_urls"] for d in discoveries),
        },
        "discoveries": discoveries,
    }

    # Ensure output directory exists
    DISCOVERED_SITES_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(DISCOVERED_SITES_FILE, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Discovery complete. Results saved to {DISCOVERED_SITES_FILE}")
    logger.info(f"Total unique URLs discovered: {output['metadata']['total_urls']}")

    # Print summary
    print("\n" + "=" * 60)
    print("DISCOVERY SUMMARY")
    print("=" * 60)
    for discovery in discoveries:
        print(f"  {discovery['niche']}: {discovery['total_urls']} URLs")
    print("=" * 60)
    print(f"Total: {output['metadata']['total_urls']} URLs")
    print(f"Output: {DISCOVERED_SITES_FILE}")


if __name__ == "__main__":
    main()
