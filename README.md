# Shopify UI Audit MVP

A zero-cost, script-based system for discovering Shopify stores, auditing their homepages for UI issues, and generating professional outreach email drafts.

## Overview

This MVP system:
1. Discovers Shopify stores via search engine scraping
2. Verifies stores are actually built on Shopify
3. Audits homepage UI using Playwright
4. Analyzes screenshots with Gemini AI for high-confidence issues
5. Extracts public contact information
6. Generates copy-paste-ready outreach emails

**Important**: This system is designed for manual outreach only. No automated email sending is included.

## Requirements

### Python Dependencies

```bash
pip install requests beautifulsoup4 playwright google-generativeai pillow
```

### Playwright Setup

```bash
playwright install chromium
```

### Gemini API Key

1. Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Set the environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Project Structure

```
project-root/
├── config/
│   ├── settings.py          # All configuration settings
│   └── user_agents.txt      # User agents for rotation
├── input/
│   └── niches.txt           # Niche keywords to search
├── discovery/
│   └── discovered_sites.json    # Discovered site URLs
├── verification/
│   └── shopify_sites.json       # Verified Shopify stores
├── audits/
│   ├── screenshots/             # Homepage screenshots
│   └── audit_results.json       # Audit data + AI analysis
├── contacts/
│   └── contacts.json            # Extracted contact info
├── outreach/
│   └── drafts/                  # Generated email drafts
├── scripts/
│   ├── discover_sites.py
│   ├── verify_shopify.py
│   ├── audit_homepage.py
│   ├── analyze_with_gemini.py
│   ├── extract_contacts.py
│   └── generate_outreach.py
└── README.md
```

## Execution Order

Run scripts in this exact order:

### Step 1: Configure Niches

Edit `input/niches.txt` with your target niches (one per line):

```
sustainable fashion
organic skincare
handmade jewelry
```

### Step 2: Discover Sites

```bash
python scripts/discover_sites.py
```

Options:
- `--niche "keyword"` - Search single niche instead of file
- `--append` - Add to existing results instead of overwriting

Output: `discovery/discovered_sites.json`

### Step 3: Verify Shopify Stores

```bash
python scripts/verify_shopify.py
```

Options:
- `--min-confidence 60` - Minimum confidence score (default: 60)
- `--url "https://example.com"` - Verify single URL

Output: `verification/shopify_sites.json`

### Step 4: Audit Homepages

```bash
python scripts/audit_homepage.py
```

Options:
- `--url "https://example.com"` - Audit single URL

Output:
- `audits/audit_results.json`
- `audits/screenshots/` (PNG files)

### Step 5: Analyze with Gemini

```bash
python scripts/analyze_with_gemini.py
```

**Requires**: `GEMINI_API_KEY` environment variable

Options:
- `--url "https://example.com"` - Analyze single URL

Output: Updates `audits/audit_results.json` with analysis

### Step 6: Extract Contacts

```bash
python scripts/extract_contacts.py
```

Options:
- `--url "https://example.com"` - Extract from single URL

Output: `contacts/contacts.json`

### Step 7: Generate Outreach

```bash
python scripts/generate_outreach.py
```

Options:
- `--url "https://example.com"` - Generate for single URL
- `--sender-name "Your Name"` - Custom sender name
- `--sender-title "Your Title"` - Custom sender title

Output: `outreach/drafts/` (individual .txt files + summary JSON)

## Safety Limits

The system includes built-in safety measures:

| Setting | Value | Purpose |
|---------|-------|---------|
| MIN_REQUEST_DELAY | 10 seconds | Minimum delay between requests |
| MAX_REQUEST_DELAY | 15 seconds | Maximum delay between requests |
| MAX_RESULTS_PER_ENGINE | 30 | Max results per search engine |
| MAX_SITES_PER_NICHE | 50 | Max sites discovered per niche |
| REQUEST_TIMEOUT | 30 seconds | HTTP request timeout |
| MAX_RETRIES | 3 | Retry attempts for failed requests |

These can be adjusted in `config/settings.py`.

## Gemini API Configuration

Settings in `config/settings.py`:

```python
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"  # Free tier model
MAX_ISSUES_PER_SITE = 3  # Maximum issues reported per site
```

The system uses Gemini 1.5 Flash for cost efficiency. For higher quality analysis, change to `gemini-1.5-pro`.

## UI Issue Detection

The system detects only high-confidence, evidence-based issues:

| Issue Type | Detection Method |
|------------|------------------|
| CTA below fold | DOM analysis + screenshot position |
| Missing primary CTA | DOM analysis |
| Slow LCP (>2.5s) | Performance API metrics |
| Console errors | Browser console capture |
| Broken images | DOM naturalWidth check |
| Mobile layout issues | Screenshot analysis |
| Text/element overlap | Gemini vision analysis |

**No subjective opinions** - only issues with concrete evidence are reported.

## Output Examples

### discovered_sites.json

```json
{
  "metadata": {
    "generated_at": "2024-01-15T10:30:00.000000",
    "total_niches": 1,
    "total_urls": 25
  },
  "discoveries": [
    {
      "niche": "sustainable fashion",
      "discovered_at": "2024-01-15T10:30:00.000000",
      "total_urls": 25,
      "urls": [
        "https://example-store.com",
        "https://another-store.com"
      ]
    }
  ]
}
```

### shopify_sites.json

```json
{
  "metadata": {
    "generated_at": "2024-01-15T11:00:00.000000",
    "total_verified": 25,
    "shopify_count": 18,
    "min_confidence_threshold": 60
  },
  "shopify_sites": [
    {
      "url": "https://example-store.com",
      "is_shopify": true,
      "confidence": 85,
      "signals_found": ["cdn.shopify.com", "Shopify.theme", "shopify-section"],
      "verified_at": "2024-01-15T11:00:00.000000"
    }
  ]
}
```

### audit_results.json (with analysis)

```json
{
  "metadata": {
    "generated_at": "2024-01-15T12:00:00.000000",
    "total_audited": 18,
    "analysis_completed_at": "2024-01-15T13:00:00.000000"
  },
  "audits": [
    {
      "url": "https://example-store.com",
      "desktop": {
        "screenshot_path": "/path/to/screenshot_desktop.png",
        "performance_metrics": {
          "lcp": 3200,
          "fcp": 1200
        },
        "console_errors": []
      },
      "mobile": {
        "screenshot_path": "/path/to/screenshot_mobile.png",
        "performance_metrics": {
          "lcp": 4100
        }
      },
      "analysis": {
        "issues": [
          {
            "id": "issue_1",
            "category": "performance",
            "severity": "high",
            "title": "Slow page load on mobile",
            "description": "LCP of 4100ms exceeds recommended 2500ms threshold",
            "evidence": "Mobile LCP: 4100ms",
            "recommendation": "Optimize images and reduce JavaScript bundle size"
          }
        ],
        "summary": {
          "total_issues": 1,
          "high_severity": 1,
          "primary_concern": "Page performance on mobile"
        }
      }
    }
  ]
}
```

### contacts.json

```json
{
  "metadata": {
    "generated_at": "2024-01-15T14:00:00.000000",
    "total_sites": 18,
    "sites_with_contacts": 15
  },
  "contacts": [
    {
      "url": "https://example-store.com",
      "emails": ["hello@example-store.com"],
      "phones": ["+1-555-123-4567"],
      "social": {
        "instagram": "https://instagram.com/examplestore",
        "facebook": "https://facebook.com/examplestore"
      },
      "contact_page_found": true
    }
  ]
}
```

### Email Draft (example_store_com.txt)

```
================================================================================
OUTREACH DRAFT
================================================================================

Store: https://example-store.com
Generated: 2024-01-15T15:00:00.000000

--------------------------------------------------------------------------------
TO: hello@example-store.com
--------------------------------------------------------------------------------

SUBJECT: Page speed opportunity for Example Store

--------------------------------------------------------------------------------
BODY:
--------------------------------------------------------------------------------

Hi there,

I took a look at Example Store and ran some performance tests. I noticed your
homepage is loading slower than ideal - Mobile LCP of 4100ms exceeds the
recommended 2500ms threshold.

Slow load times can significantly impact both conversions and search rankings.
Studies show that each second of delay can reduce conversions by 7%.

There are usually some quick optimizations that can make a noticeable difference.

Would you be interested in a brief overview of what could be improved?

Best regards,
Your Name
UI/UX Consultant

--------------------------------------------------------------------------------
```

## Customization

### Changing Sender Info

Edit `config/settings.py`:

```python
SENDER_NAME = "Your Name"
SENDER_TITLE = "UI/UX Consultant"
```

Or use command-line options:

```bash
python scripts/generate_outreach.py --sender-name "John Doe" --sender-title "Web Developer"
```

### Adjusting Thresholds

In `config/settings.py`:

```python
# Performance thresholds
LCP_THRESHOLD_MS = 2500  # Largest Contentful Paint
CLS_THRESHOLD = 0.1      # Cumulative Layout Shift

# Shopify verification
MIN_SHOPIFY_CONFIDENCE = 60  # Minimum confidence score

# Analysis
MAX_ISSUES_PER_SITE = 3  # Maximum issues to report
```

### Adding Search Queries

Edit `SEARCH_QUERY_TEMPLATES` in `config/settings.py`:

```python
SEARCH_QUERY_TEMPLATES = [
    '"{niche}" site:myshopify.com',
    '"{niche}" "powered by shopify"',
    '"{niche}" shopify store',
    '"{niche}" shop online -amazon -ebay -etsy',
]
```

## Troubleshooting

### "GEMINI_API_KEY not set"

```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Playwright browser not found

```bash
playwright install chromium
```

### Rate limiting errors

The system has built-in delays. If you still get blocked:
1. Increase `MIN_REQUEST_DELAY` in settings
2. Wait before retrying
3. Use a VPN to change IP

### No sites discovered

1. Check your niche keywords are reasonable
2. Try broader search terms
3. Verify internet connection

### Empty audit results

1. Ensure Playwright is installed correctly
2. Check that discovered sites are accessible
3. Review console output for errors

## Best Practices

1. **Start small**: Test with 1-2 niches first
2. **Review drafts**: Always review and personalize emails before sending
3. **Respect rate limits**: Don't increase scraping speed
4. **Keep records**: Track which stores you've contacted
5. **Be professional**: Only send to business contacts

## License

This project is for personal/educational use. Respect website terms of service and applicable laws when using this tool.

## Disclaimer

- This tool is for legitimate business outreach only
- Respect robots.txt and website terms of service
- Do not use for spam or unsolicited bulk email
- The developers are not responsible for misuse
