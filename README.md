# Shopify UI Audit MVP

A zero-cost, script-based system for discovering Shopify stores, auditing their homepages for UI issues, and generating professional outreach email drafts.

## Overview

This MVP system:
1. Discovers Shopify stores via search engine scraping or built-in database
2. Verifies stores are actually built on Shopify
3. Audits homepage UI using Playwright (desktop + mobile screenshots)
4. Analyzes screenshots with Gemini AI for visual/design issues
5. Extracts public contact information
6. Generates copy-paste-ready outreach emails

**Important**: This system is designed for manual outreach only. No automated email sending is included.

## Quick Start

The easiest way to run the tool is using the unified CLI (`run.py`):

### Interactive Mode (Recommended)

```bash
python run.py
```

This launches an interactive wizard that guides you through the entire pipeline.

### Batch Mode

```bash
python run.py run --niches "sustainable fashion, jewelry" --max-sites 10 --sender-name "Your Name"
```

### Manual URL Input (Skip Discovery)

```bash
# Comma-separated URLs
python run.py add-urls --urls "https://store1.com,https://store2.com"

# From a file (one URL per line)
python run.py add-urls --file urls.txt
```

### Check Pipeline Status

```bash
python run.py status
```

### Clean All Output Data

```bash
python run.py clean
```

## Requirements

### Python Dependencies

```bash
pip install requests beautifulsoup4 playwright google-generativeai pillow typer questionary rich python-dotenv
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

Or create a `.env` file in the project root:

```
GEMINI_API_KEY=your-api-key-here
```

## Project Structure

```
project-root/
├── run.py                       # Main CLI entry point (unified interface)
├── config/
│   ├── settings.py              # All configuration settings
│   └── user_agents.txt          # User agents for rotation
├── input/
│   └── niches.txt               # Niche keywords to search
├── scripts/
│   ├── discover_sites.py        # Site discovery (search + database)
│   ├── verify_shopify.py        # Shopify verification
│   ├── audit_homepage.py        # Playwright-based auditing
│   ├── analyze_with_gemini.py   # AI visual analysis
│   ├── extract_contacts.py      # Contact extraction
│   └── generate_outreach.py     # Email draft generation
├── discovery/
│   └── discovered_sites.json    # Discovered site URLs (output)
├── verification/
│   └── shopify_sites.json       # Verified Shopify stores (output)
├── audits/
│   ├── screenshots/             # Homepage screenshots (output)
│   └── audit_results.json       # Audit data + AI analysis (output)
├── contacts/
│   └── contacts.json            # Extracted contact info (output)
├── outreach/
│   └── drafts/                  # Generated email drafts (output)
├── debug/                       # Debug HTML files when search fails
├── .env                         # Environment variables (create this)
└── README.md
```

## Built-in Shopify Store Database

When search engines block requests or return zero results, the system automatically falls back to a built-in database of 100+ verified Shopify stores across these niches:

- **shoes** - Kizik, Allbirds, Rothy's, GOAT, Steve Madden, etc.
- **fashion** - Fashion Nova, Gymshark, Princess Polly, etc.
- **jewelry** - Mejuri, Kendra Scott, Gorjana, etc.
- **beauty** - ColourPop, Kylie Cosmetics, Morphe, etc.
- **skincare** - The Ordinary, Glossier, CeraVe, etc.
- **men skincare / grooming** - Dollar Shave Club, Manscaped, etc.
- **fitness** - Gymshark, Alo Yoga, Fabletics, etc.
- **home** - Brooklinen, Parachute, Article, etc.
- **food** - Magic Spoon, Liquid Death, etc.
- **pets** - BarkBox, Chewy, etc.

To use the database directly (bypasses search engines):

```bash
python scripts/discover_sites.py --use-database
```

## CLI Reference

### run.py Commands

| Command | Description |
|---------|-------------|
| `python run.py` | Interactive mode with guided prompts |
| `python run.py run` | Batch mode with CLI flags |
| `python run.py status` | Show pipeline status and data counts |
| `python run.py add-urls` | Add URLs manually (skip discovery) |
| `python run.py clean` | Clean all output files |

### run.py run Options

| Option | Description | Default |
|--------|-------------|---------|
| `--niches` | Comma-separated niche keywords | Reads from input/niches.txt |
| `--max-sites` | Maximum sites per niche | 5 |
| `--confidence` | Minimum Shopify confidence score | 70 |
| `--sender-name` | Your name for email drafts | "Your Name" |
| `--sender-title` | Your title for email drafts | "UI/UX Consultant" |

### Individual Script Options

#### discover_sites.py

```bash
python scripts/discover_sites.py [options]
```

| Option | Description |
|--------|-------------|
| `--niche "keyword"` | Search single niche instead of file |
| `--append` | Add to existing results instead of overwriting |
| `--use-database` | Use built-in store database (skip search engines) |

#### verify_shopify.py

```bash
python scripts/verify_shopify.py [options]
```

| Option | Description |
|--------|-------------|
| `--min-confidence 70` | Minimum confidence score (default: 70) |
| `--url "https://example.com"` | Verify single URL |

#### audit_homepage.py

```bash
python scripts/audit_homepage.py [options]
```

| Option | Description |
|--------|-------------|
| `--url "https://example.com"` | Audit single URL |

#### analyze_with_gemini.py

```bash
python scripts/analyze_with_gemini.py [options]
```

**Requires**: `GEMINI_API_KEY` environment variable

| Option | Description |
|--------|-------------|
| `--url "https://example.com"` | Analyze single URL |

#### extract_contacts.py

```bash
python scripts/extract_contacts.py [options]
```

| Option | Description |
|--------|-------------|
| `--url "https://example.com"` | Extract from single URL |

#### generate_outreach.py

```bash
python scripts/generate_outreach.py [options]
```

| Option | Description |
|--------|-------------|
| `--url "https://example.com"` | Generate for single URL |
| `--sender-name "Your Name"` | Custom sender name |
| `--sender-title "Your Title"` | Custom sender title |

## Execution Order (Manual Mode)

If running scripts individually instead of using `run.py`:

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

Output: `discovery/discovered_sites.json`

### Step 3: Verify Shopify Stores

```bash
python scripts/verify_shopify.py
```

Output: `verification/shopify_sites.json`

### Step 4: Audit Homepages

```bash
python scripts/audit_homepage.py
```

Output: `audits/audit_results.json` + `audits/screenshots/`

### Step 5: Analyze with Gemini

```bash
python scripts/analyze_with_gemini.py
```

Output: Updates `audits/audit_results.json` with visual analysis

### Step 6: Extract Contacts

```bash
python scripts/extract_contacts.py
```

Output: `contacts/contacts.json`

### Step 7: Generate Outreach

```bash
python scripts/generate_outreach.py
```

Output: `outreach/drafts/` (individual .txt files + summary JSON)

## Safety Limits

The system includes built-in safety measures:

| Setting | Default Value | Purpose |
|---------|---------------|---------|
| MIN_REQUEST_DELAY | 10 seconds | Minimum delay between requests |
| MAX_REQUEST_DELAY | 15 seconds | Maximum delay between requests |
| MAX_RESULTS_PER_ENGINE | 30 | Max results per search engine |
| MAX_SITES_PER_NICHE | 5 | Max sites discovered per niche |
| REQUEST_TIMEOUT | 30 seconds | HTTP request timeout |
| MAX_RETRIES | 3 | Retry attempts for failed requests |
| MIN_SHOPIFY_CONFIDENCE | 70 | Minimum Shopify verification score |

These can be adjusted in `config/settings.py`.

## Gemini API Configuration

Settings in `config/settings.py`:

```python
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"  # Free tier model
MAX_ISSUES_PER_SITE = 3  # Maximum issues reported per site
```

The system uses Gemini 2.5 Flash for cost efficiency. For higher quality analysis, change to `gemini-2.5-pro`.

## UI Issue Detection

The system uses **visual/design analysis** via Gemini AI to detect issues from screenshots. It focuses on:

| Issue Category | What's Detected |
|----------------|-----------------|
| Typography | Font issues, readability problems, inconsistent text styling |
| Layout & Spacing | Alignment issues, inconsistent spacing, cramped or sparse layouts |
| Images | Broken images, poor quality, sizing issues |
| Mobile Responsiveness | Layout breaks, touch target issues, content overflow |
| Color & Contrast | Poor contrast, accessibility issues, inconsistent colors |
| Visual Hierarchy | Unclear focus, competing elements, missing emphasis |

**Note**: The analysis focuses on visual issues only. Performance metrics (LCP, FCP) are collected for reference but issues are detected through screenshot analysis.

## Email Templates

The system includes category-specific email templates:

| Category | Focus |
|----------|-------|
| `typography` | Font and text styling issues |
| `layout` | Spacing and alignment problems |
| `images` | Visual/image quality issues |
| `mobile` | Mobile responsiveness problems |
| `contrast` | Color and contrast issues |
| `hierarchy` | Visual hierarchy and focus issues |
| `generic` | General design improvements |

Each email is personalized with:
- Store name and URL
- Specific issue evidence from AI analysis
- Actionable recommendations
- Your sender name and title

## Search Engines

The system uses multiple search engines in this order:

1. **Bing** - First choice (less aggressive blocking)
2. **Google** - Second choice
3. **DuckDuckGo** - Third choice
4. **Built-in Database** - Automatic fallback when all engines fail

When search engines block requests, debug HTML is saved to `debug/` for troubleshooting.

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
      ],
      "search_metadata": [
        {"engine": "bing", "query": "sustainable fashion site:myshopify.com", "results_count": 10}
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
    "min_confidence_threshold": 70
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
        "screenshot_path": "/path/to/screenshot_mobile.png"
      },
      "analysis": {
        "issues": [
          {
            "id": "issue_1",
            "category": "typography",
            "severity": "high",
            "title": "Inconsistent font sizing",
            "description": "Body text varies between 14px and 16px across sections",
            "evidence": "Visible in hero section vs product grid",
            "recommendation": "Standardize body text to 16px for consistency"
          }
        ],
        "summary": {
          "total_issues": 1,
          "high_severity": 1,
          "primary_concern": "Typography consistency"
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

SUBJECT: Design improvement opportunity for Example Store

--------------------------------------------------------------------------------
BODY:
--------------------------------------------------------------------------------

Hi there,

I was looking at Example Store and noticed an opportunity to improve the design.

I spotted some inconsistent font sizing - body text varies between 14px and 16px
across sections. Small design improvements like this can often have a meaningful
impact on conversions.

Would you be open to a quick conversation about it?

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
# Performance thresholds (for reference)
LCP_THRESHOLD_MS = 2500  # Largest Contentful Paint
CLS_THRESHOLD = 0.1      # Cumulative Layout Shift

# Shopify verification
MIN_SHOPIFY_CONFIDENCE = 70  # Minimum confidence score

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

Or create a `.env` file with `GEMINI_API_KEY=your-key`.

### Playwright browser not found

```bash
playwright install chromium
```

### Rate limiting / No sites discovered

The system has built-in fallback to the store database. If you still get no results:
1. Use `--use-database` flag to skip search engines entirely
2. Increase `MIN_REQUEST_DELAY` in settings
3. Wait 30 minutes before retrying
4. Use a VPN to change IP

### Debug search issues

Check the `debug/` folder for saved HTML files from search engines. These show what the search engine returned, useful for diagnosing blocking issues.

### Empty audit results

1. Ensure Playwright is installed correctly: `playwright install chromium`
2. Check that discovered sites are accessible
3. Review console output for errors

## Best Practices

1. **Start small**: Test with 1-2 niches first
2. **Use the database**: For testing, use `--use-database` to avoid rate limits
3. **Review drafts**: Always review and personalize emails before sending
4. **Respect rate limits**: Don't increase scraping speed
5. **Keep records**: Track which stores you've contacted
6. **Be professional**: Only send to business contacts

## License

This project is for personal/educational use. Respect website terms of service and applicable laws when using this tool.

## Disclaimer

- This tool is for legitimate business outreach only
- Respect robots.txt and website terms of service
- Do not use for spam or unsolicited bulk email
- The developers are not responsible for misuse
