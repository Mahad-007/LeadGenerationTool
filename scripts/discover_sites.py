#!/usr/bin/env python3
"""
Site Discovery Script for Shopify UI Audit MVP.

This script discovers potential Shopify stores by scraping Bing and DuckDuckGo
search results for given niche keywords.

Features:
- Scrapes Bing and DuckDuckGo HTML endpoints
- Uses rotating user agents
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
from urllib.parse import urlparse, urljoin, quote_plus
from datetime import datetime
from typing import List, Dict, Set, Optional

import requests
from bs4 import BeautifulSoup

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    NICHES_FILE,
    USER_AGENTS_FILE,
    DISCOVERED_SITES_FILE,
    MIN_REQUEST_DELAY,
    MAX_REQUEST_DELAY,
    MAX_RESULTS_PER_ENGINE,
    MAX_SITES_PER_NICHE,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    BING_SEARCH_URL,
    DUCKDUCKGO_SEARCH_URL,
    SEARCH_QUERY_TEMPLATES,
    LOG_LEVEL,
    LOG_FORMAT,
)

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
    """Scrapes search engines for potential Shopify store URLs."""

    def __init__(self, user_agent_rotator: UserAgentRotator, rate_limiter: RateLimiter):
        """
        Initialize scraper.

        Args:
            user_agent_rotator: UserAgentRotator instance
            rate_limiter: RateLimiter instance
        """
        self.ua_rotator = user_agent_rotator
        self.rate_limiter = rate_limiter
        self.session = requests.Session()

    def _make_request(self, url: str, params: Dict = None) -> Optional[str]:
        """
        Make HTTP request with retries and rate limiting.

        Args:
            url: URL to request
            params: Query parameters

        Returns:
            Response text or None if failed
        """
        self.rate_limiter.wait()

        headers = {
            "User-Agent": self.ua_rotator.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                )
                response.raise_for_status()
                return response.text

            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5 * (attempt + 1))  # Exponential backoff

        return None

    def search_bing(self, query: str) -> Set[str]:
        """
        Search Bing and extract URLs.

        Args:
            query: Search query string

        Returns:
            Set of discovered URLs
        """
        urls = set()
        logger.info(f"Searching Bing for: {query}")

        # Bing pagination: first=1, first=11, first=21, etc.
        for start in range(1, MAX_RESULTS_PER_ENGINE + 1, 10):
            params = {
                "q": query,
                "first": start,
                "FORM": "PORE",
            }

            html = self._make_request(BING_SEARCH_URL, params)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")

            # Extract URLs from search results
            # Bing uses various selectors for results
            for link in soup.select("li.b_algo h2 a, .b_algo a"):
                href = link.get("href", "")
                if href and href.startswith("http"):
                    normalized = normalize_url(href)
                    if normalized:
                        urls.add(normalized)

            # Also check cite elements for URLs
            for cite in soup.select("cite"):
                text = cite.get_text()
                if text:
                    normalized = normalize_url(text)
                    if normalized:
                        urls.add(normalized)

            # Check if there are more results
            if not soup.select(".sw_next"):
                break

        logger.info(f"Bing found {len(urls)} URLs for query")
        return urls

    def search_duckduckgo(self, query: str) -> Set[str]:
        """
        Search DuckDuckGo HTML endpoint and extract URLs.

        Args:
            query: Search query string

        Returns:
            Set of discovered URLs
        """
        urls = set()
        logger.info(f"Searching DuckDuckGo for: {query}")

        # DuckDuckGo HTML endpoint
        params = {"q": query}

        html = self._make_request(DUCKDUCKGO_SEARCH_URL, params)
        if not html:
            return urls

        soup = BeautifulSoup(html, "html.parser")

        # Extract URLs from search results
        for result in soup.select(".result__url, .result__a"):
            href = result.get("href", "")
            text = result.get_text()

            # Try href first
            if href and href.startswith("http"):
                normalized = normalize_url(href)
                if normalized:
                    urls.add(normalized)

            # Also try text content (often contains URL)
            if text:
                normalized = normalize_url(text.strip())
                if normalized:
                    urls.add(normalized)

        # Also check for links in result snippets
        for link in soup.select("a.result__snippet"):
            href = link.get("href", "")
            if href:
                # DuckDuckGo may use redirect URLs
                if "uddg=" in href:
                    # Extract actual URL from redirect
                    match = re.search(r"uddg=([^&]+)", href)
                    if match:
                        from urllib.parse import unquote
                        actual_url = unquote(match.group(1))
                        normalized = normalize_url(actual_url)
                        if normalized:
                            urls.add(normalized)

        logger.info(f"DuckDuckGo found {len(urls)} URLs for query")
        return urls

    def discover_for_niche(self, niche: str) -> Dict:
        """
        Discover potential Shopify stores for a niche.

        Args:
            niche: Niche keyword to search for

        Returns:
            Dictionary with discovery results
        """
        all_urls = set()
        search_metadata = []

        for template in SEARCH_QUERY_TEMPLATES:
            query = template.format(niche=niche)

            # Search Bing
            bing_urls = self.search_bing(query)
            all_urls.update(bing_urls)
            search_metadata.append({
                "engine": "bing",
                "query": query,
                "results_count": len(bing_urls),
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

        # Convert to list and limit
        urls_list = list(all_urls)[:MAX_SITES_PER_NICHE]

        return {
            "niche": niche,
            "discovered_at": datetime.utcnow().isoformat(),
            "total_urls": len(urls_list),
            "urls": urls_list,
            "search_metadata": search_metadata,
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
            result = scraper.discover_for_niche(niche)
            discoveries.append(result)
            logger.info(f"Discovered {result['total_urls']} URLs for '{niche}'")
        except Exception as e:
            logger.error(f"Error processing niche '{niche}': {e}")
            continue

    # Prepare output
    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
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
