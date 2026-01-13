"""
Configuration settings for Shopify UI Audit MVP.
All paths, timeouts, and API configurations are centralized here.
"""

import os
from pathlib import Path

# =============================================================================
# PROJECT PATHS
# =============================================================================

# Base project directory
PROJECT_ROOT = Path(__file__).parent.parent

# Input/Output directories
INPUT_DIR = PROJECT_ROOT / "input"
DISCOVERY_DIR = PROJECT_ROOT / "discovery"
VERIFICATION_DIR = PROJECT_ROOT / "verification"
AUDITS_DIR = PROJECT_ROOT / "audits"
SCREENSHOTS_DIR = AUDITS_DIR / "screenshots"
CONTACTS_DIR = PROJECT_ROOT / "contacts"
OUTREACH_DIR = PROJECT_ROOT / "outreach"
DRAFTS_DIR = OUTREACH_DIR / "drafts"
CONFIG_DIR = PROJECT_ROOT / "config"

# Input files
NICHES_FILE = INPUT_DIR / "niches.txt"
USER_AGENTS_FILE = CONFIG_DIR / "user_agents.txt"

# Output files
DISCOVERED_SITES_FILE = DISCOVERY_DIR / "discovered_sites.json"
SHOPIFY_SITES_FILE = VERIFICATION_DIR / "shopify_sites.json"
AUDIT_RESULTS_FILE = AUDITS_DIR / "audit_results.json"
CONTACTS_FILE = CONTACTS_DIR / "contacts.json"

# =============================================================================
# RATE LIMITING & SAFETY
# =============================================================================

# Minimum delay between requests (in seconds)
MIN_REQUEST_DELAY = 10

# Maximum delay between requests (in seconds)
MAX_REQUEST_DELAY = 15

# Maximum results per search engine per niche
MAX_RESULTS_PER_ENGINE = 30

# Maximum total sites to discover per niche
MAX_SITES_PER_NICHE = 10

# Request timeout (in seconds)
REQUEST_TIMEOUT = 30

# Maximum retries per request
MAX_RETRIES = 3

# =============================================================================
# PLAYWRIGHT SETTINGS
# =============================================================================

# Desktop viewport
DESKTOP_VIEWPORT = {"width": 1440, "height": 900}

# Mobile viewport
MOBILE_VIEWPORT = {"width": 390, "height": 844}

# Page load timeout (in milliseconds)
PAGE_LOAD_TIMEOUT = 60000

# Screenshot quality (0-100)
SCREENSHOT_QUALITY = 85

# Wait after page load for dynamic content (in milliseconds)
POST_LOAD_WAIT = 3000

# =============================================================================
# SHOPIFY VERIFICATION
# =============================================================================

# Minimum confidence score to consider a site as Shopify (0-100)
MIN_SHOPIFY_CONFIDENCE = 50

# Shopify detection signals and their weights
SHOPIFY_SIGNALS = {
    "cdn.shopify.com": 40,
    "myshopify.com": 50,
    "Shopify.theme": 30,
    "shopify-section": 25,
    "shopify_pay": 20,
    "/cart.js": 25,
    "shopify.accessToken": 30,
    "X-ShopId": 50,
    "X-Shopify-Stage": 50,
}

# =============================================================================
# GEMINI API SETTINGS
# =============================================================================

# Gemini API key (set via environment variable)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini model to use
GEMINI_MODEL = "gemini-2.5-flash"

# Maximum issues to report per site
MAX_ISSUES_PER_SITE = 3

# Gemini API endpoint
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"

# =============================================================================
# UI ISSUE DETECTION THRESHOLDS
# =============================================================================

# LCP threshold (in milliseconds) - above this is considered slow
LCP_THRESHOLD_MS = 2500

# CLS threshold - above this indicates layout shift issues
CLS_THRESHOLD = 0.1

# Time to Interactive threshold (in milliseconds)
TTI_THRESHOLD_MS = 3800

# Fold line position (pixels from top) for CTA detection
DESKTOP_FOLD_LINE = 900
MOBILE_FOLD_LINE = 844

# =============================================================================
# CONTACT EXTRACTION
# =============================================================================

# Pages to check for contact information
CONTACT_PAGES = [
    "/contact",
    "/pages/contact",
    "/pages/contact-us",
    "/contact-us",
]

# Email patterns to exclude (generic/support emails)
EXCLUDED_EMAIL_PATTERNS = [
    "noreply@",
    "no-reply@",
    "support@shopify.com",
    "help@shopify.com",
]

# =============================================================================
# OUTREACH SETTINGS
# =============================================================================

# Sender name for email drafts
SENDER_NAME = "Your Name"

# Sender company/title
SENDER_TITLE = "UI/UX Consultant"

# Maximum email body length (characters)
MAX_EMAIL_LENGTH = 1500

# =============================================================================
# LOGGING
# =============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# =============================================================================
# SEARCH ENGINE SETTINGS
# =============================================================================

# Bing search URL template
BING_SEARCH_URL = "https://www.bing.com/search"

# DuckDuckGo HTML search URL
DUCKDUCKGO_SEARCH_URL = "https://html.duckduckgo.com/html/"

# Search query templates for Shopify store discovery
# Prioritize myshopify.com which guarantees Shopify stores
SEARCH_QUERY_TEMPLATES = [
    'site:myshopify.com {niche}',
    '{niche} site:myshopify.com',
    '"{niche}" inurl:myshopify.com',
    '"{niche}" "powered by shopify" shop -site:shopify.com -site:apps.shopify.com',
]
