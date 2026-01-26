#!/usr/bin/env python3
"""
Gemini AI Analysis Script for Shopify UI Audit MVP.

This script uses Google's Gemini API to analyze homepage screenshots
and metrics to identify high-confidence UI issues.

Features:
- Sends screenshots to Gemini Vision API
- Includes performance metrics and DOM data
- Returns evidence-based issues only
- Maximum 1-3 issues per site
- JSON-only structured responses

Usage:
    python scripts/analyze_with_gemini.py [--url "https://example.com"]

Environment Variables:
    GEMINI_API_KEY: Your Gemini API key (required)

Requirements:
    pip install google-genai pillow
"""

import sys
import json
import logging
import argparse
import base64
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

from google import genai
from PIL import Image
import io

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    AUDIT_RESULTS_FILE,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MAX_ISSUES_PER_SITE,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Analysis prompt for Gemini - VISUAL/DESIGN ISSUES ONLY
ANALYSIS_PROMPT = """You are a professional UI/UX designer analyzing screenshots of a Shopify store homepage.

CRITICAL INSTRUCTIONS:
1. ONLY report issues that are CLEARLY VISIBLE in the screenshots provided
2. Do NOT invent or assume issues - if you cannot see it, do not report it
3. Report maximum {max_issues} issues total
4. Focus ONLY on visual design and UI issues - NOT performance or technical issues
5. Each issue MUST include the exact location in the screenshot (e.g., "top-left corner", "hero section", "navigation bar")
6. If the design looks good, return an empty issues array - do NOT force issues

DESIGN ISSUES TO LOOK FOR (only if clearly visible):

1. TYPOGRAPHY ISSUES
   - Text that is too small to read comfortably
   - Poor font contrast (light text on light background or dark on dark)
   - Text that is cut off or truncated awkwardly
   - Inconsistent font sizes that break visual hierarchy
   - Text overlapping other elements or images

2. LAYOUT & SPACING ISSUES
   - Elements that are misaligned or not properly centered
   - Inconsistent spacing/margins between elements
   - Content that appears cramped or too spread out
   - Elements overlapping each other unintentionally
   - Broken grid or inconsistent column alignment

3. IMAGE ISSUES (only what's visible)
   - Images that appear broken (showing broken image icon or placeholder)
   - Images that are pixelated, blurry, or low quality
   - Images that are stretched or distorted
   - Missing product images showing empty boxes

4. MOBILE RESPONSIVENESS (from mobile screenshot)
   - Content extending beyond screen edge (horizontal overflow)
   - Buttons or text that are too small for touch
   - Elements stacking awkwardly or overlapping
   - Navigation that doesn't work on mobile view

5. COLOR & CONTRAST
   - Text that's hard to read due to poor contrast
   - Colors that clash or look unprofessional
   - Important elements that don't stand out visually

6. VISUAL HIERARCHY
   - No clear focal point or call-to-action visible
   - Important elements hidden or hard to find
   - Confusing layout where user doesn't know where to look

WHAT NOT TO REPORT:
- Performance or loading speed issues
- Console errors or JavaScript issues
- SEO or accessibility issues
- Personal design preferences
- Issues you cannot clearly see in the screenshot
- Minor issues that don't impact user experience

SCREENSHOTS PROVIDED:
- Desktop screenshot (showing what users see on first load)
- Mobile screenshot (showing mobile experience)

REQUIRED JSON OUTPUT FORMAT:
{{
    "issues": [
        {{
            "id": "issue_1",
            "category": "typography|layout|images|mobile|contrast|hierarchy",
            "severity": "high|medium|low",
            "title": "Brief, specific issue title",
            "description": "Detailed description of exactly what's wrong",
            "location": "Exact location in screenshot (e.g., 'hero section center', 'top navigation bar', 'footer left side')",
            "evidence": "What you can see in the screenshot that proves this issue",
            "recommendation": "Specific fix recommendation"
        }}
    ],
    "summary": {{
        "total_issues": 0,
        "high_severity": 0,
        "medium_severity": 0,
        "low_severity": 0,
        "primary_concern": "Most important design issue or 'None' if design looks good"
    }}
}}

If the homepage design looks good with NO clear visible issues, return:
{{
    "issues": [],
    "summary": {{
        "total_issues": 0,
        "high_severity": 0,
        "medium_severity": 0,
        "low_severity": 0,
        "primary_concern": "None - homepage design appears well-executed"
    }}
}}

IMPORTANT: Only report what you can actually SEE. Quality over quantity - fewer accurate issues is better than many false ones.

Analyze the screenshots now. Return ONLY valid JSON, no other text."""


class GeminiAnalyzer:
    """Analyzes homepage screenshots using Gemini Vision API."""

    def __init__(self, api_key: str):
        """
        Initialize Gemini analyzer.

        Args:
            api_key: Gemini API key
        """
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.client = genai.Client(api_key=api_key)
        self.model_name = GEMINI_MODEL
        logger.info(f"Initialized Gemini analyzer with model: {GEMINI_MODEL}")

    def _load_image(self, image_path: str) -> Optional[Image.Image]:
        """
        Load and prepare image for Gemini API.

        Args:
            image_path: Path to image file

        Returns:
            PIL Image object or None
        """
        try:
            path = Path(image_path)
            if not path.exists():
                logger.warning(f"Image not found: {image_path}")
                return None

            # Load and resize if too large (Gemini has size limits)
            img = Image.open(path)

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize if too large (max 4MB for Gemini)
            max_size = 2048
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            return img

        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return None

    def _prepare_metrics_summary(self, audit_data: Dict) -> str:
        """
        Prepare performance metrics summary for prompt.

        Args:
            audit_data: Audit results for a site

        Returns:
            Formatted metrics string
        """
        metrics = []

        for viewport in ["desktop", "mobile"]:
            if viewport in audit_data and audit_data[viewport]:
                vp_data = audit_data[viewport]
                perf = vp_data.get("performance_metrics", {})

                metrics.append(f"{viewport.upper()}:")

                if perf.get("lcp"):
                    lcp_status = "SLOW" if perf["lcp"] > LCP_THRESHOLD_MS else "OK"
                    metrics.append(f"  - LCP: {perf['lcp']:.0f}ms ({lcp_status})")

                if perf.get("fcp"):
                    metrics.append(f"  - FCP: {perf['fcp']:.0f}ms")

                if perf.get("load_complete"):
                    metrics.append(f"  - Load Complete: {perf['load_complete']:.0f}ms")

                if perf.get("ttfb"):
                    metrics.append(f"  - TTFB: {perf['ttfb']:.0f}ms")

        return "\n".join(metrics) if metrics else "No metrics available"

    def _prepare_dom_summary(self, audit_data: Dict) -> str:
        """
        Prepare DOM analysis summary for prompt.

        Args:
            audit_data: Audit results for a site

        Returns:
            Formatted DOM info string
        """
        dom_parts = []

        for viewport in ["desktop", "mobile"]:
            if viewport in audit_data and audit_data[viewport]:
                vp_data = audit_data[viewport]
                dom = vp_data.get("dom_info", {})

                if dom:
                    dom_parts.append(f"{viewport.upper()} DOM:")
                    dom_parts.append(f"  - Page title: {dom.get('title', 'N/A')}")
                    dom_parts.append(f"  - H1: {dom.get('h1', 'N/A')}")
                    dom_parts.append(f"  - CTAs above fold: {dom.get('ctasAboveFold', 0)}")
                    dom_parts.append(f"  - CTAs below fold: {dom.get('ctasBelowFold', 0)}")

                    if dom.get("brokenImages"):
                        dom_parts.append(f"  - Broken images: {len(dom['brokenImages'])}")

                    if dom.get("ctas"):
                        dom_parts.append("  - Top CTAs:")
                        for cta in dom["ctas"][:5]:
                            visible = "above fold" if cta.get("visible") else "below fold"
                            dom_parts.append(f"    - '{cta.get('text', '')}' ({visible})")

        return "\n".join(dom_parts) if dom_parts else "No DOM info available"

    def _prepare_console_errors(self, audit_data: Dict) -> str:
        """
        Prepare console errors summary for prompt.

        Args:
            audit_data: Audit results for a site

        Returns:
            Formatted console errors string
        """
        errors = []

        for viewport in ["desktop", "mobile"]:
            if viewport in audit_data and audit_data[viewport]:
                vp_data = audit_data[viewport]
                console = vp_data.get("console_errors", [])

                for error in console[:5]:  # Limit to 5 per viewport
                    errors.append(f"{viewport}: [{error.get('type', 'error')}] {error.get('text', '')[:200]}")

        return "\n".join(errors) if errors else "No console errors detected"

    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON from Gemini response, handling markdown code blocks.

        Args:
            response_text: Raw response from Gemini

        Returns:
            Parsed JSON dictionary
        """
        # Try direct JSON parse first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Return error structure
        return {
            "issues": [],
            "summary": {
                "total_issues": 0,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0,
                "primary_concern": "Failed to parse AI response",
            },
            "parse_error": True,
            "raw_response": response_text[:500],
        }

    def analyze(self, audit_data: Dict) -> Dict:
        """
        Analyze a site's audit data using Gemini.

        Args:
            audit_data: Audit results for a single site

        Returns:
            Analysis results with identified issues
        """
        url = audit_data.get("url", "Unknown")
        logger.info(f"Analyzing: {url}")

        result = {
            "url": url,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "issues": [],
            "summary": None,
            "error": None,
        }

        try:
            # Load screenshots
            images = []
            image_labels = []

            if audit_data.get("desktop") and audit_data["desktop"].get("screenshot_path"):
                desktop_img = self._load_image(audit_data["desktop"]["screenshot_path"])
                if desktop_img:
                    images.append(desktop_img)
                    image_labels.append("Desktop Screenshot")

            if audit_data.get("mobile") and audit_data["mobile"].get("screenshot_path"):
                mobile_img = self._load_image(audit_data["mobile"]["screenshot_path"])
                if mobile_img:
                    images.append(mobile_img)
                    image_labels.append("Mobile Screenshot")

            if not images:
                result["error"] = "No screenshots available for analysis"
                return result

            # Prepare prompt - only need max_issues for visual-only analysis
            prompt = ANALYSIS_PROMPT.format(
                max_issues=MAX_ISSUES_PER_SITE,
            )

            # Build content list for Gemini
            content = [prompt]
            for img, label in zip(images, image_labels):
                content.append(f"\n{label}:")
                content.append(img)

            # Call Gemini API
            logger.info("  Sending to Gemini API...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=content
            )

            # Parse response
            analysis = self._parse_json_response(response.text)

            result["issues"] = analysis.get("issues", [])
            result["summary"] = analysis.get("summary", {})

            issue_count = len(result["issues"])
            logger.info(f"  Found {issue_count} issues")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"  Analysis failed: {e}")

        return result


def load_audit_results() -> List[Dict]:
    """Load audit results from file."""
    if not AUDIT_RESULTS_FILE.exists():
        logger.error(f"Audit results file not found: {AUDIT_RESULTS_FILE}")
        return []

    try:
        with open(AUDIT_RESULTS_FILE, "r") as f:
            data = json.load(f)
        return data.get("audits", [])
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse audit results: {e}")
        return []


def main():
    """Main entry point for Gemini analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze homepage audits using Gemini AI"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Analyze only this URL (must exist in audit_results.json)",
    )
    args = parser.parse_args()

    # Check API key
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY environment variable not set")
        print("\nError: Please set GEMINI_API_KEY environment variable")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        sys.exit(1)

    # Load audit results
    audits = load_audit_results()
    if not audits:
        logger.error("No audit results to analyze. Run audit_homepage.py first.")
        sys.exit(1)

    # Filter by URL if specified
    if args.url:
        audits = [a for a in audits if a.get("url") == args.url]
        if not audits:
            logger.error(f"URL not found in audit results: {args.url}")
            sys.exit(1)

    # Initialize analyzer
    try:
        analyzer = GeminiAnalyzer(GEMINI_API_KEY)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Analyze each audit
    results = []
    for i, audit in enumerate(audits, 1):
        logger.info(f"[{i}/{len(audits)}] Processing {audit.get('url', 'Unknown')}")

        # Skip failed audits
        if audit.get("error"):
            logger.warning(f"  Skipping - audit failed: {audit['error']}")
            continue

        result = analyzer.analyze(audit)
        results.append(result)

    # Update audit results file with analysis
    try:
        with open(AUDIT_RESULTS_FILE, "r") as f:
            data = json.load(f)

        # Add analysis to each audit
        for audit in data.get("audits", []):
            for result in results:
                if audit.get("url") == result.get("url"):
                    audit["analysis"] = result
                    break

        data["metadata"]["analysis_completed_at"] = datetime.now(timezone.utc).isoformat()
        data["metadata"]["total_analyzed"] = len(results)

        with open(AUDIT_RESULTS_FILE, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Analysis results added to {AUDIT_RESULTS_FILE}")

    except Exception as e:
        logger.error(f"Failed to update audit results: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)

    total_issues = 0
    high_severity = 0
    sites_with_issues = 0

    for result in results:
        url = result.get("url", "Unknown")
        issues = result.get("issues", [])
        error = result.get("error")

        if error:
            print(f"\n  {url}")
            print(f"    ERROR: {error}")
            continue

        total_issues += len(issues)
        if issues:
            sites_with_issues += 1

        print(f"\n  {url}")
        if issues:
            for issue in issues:
                severity = issue.get("severity", "medium")
                if severity == "high":
                    high_severity += 1
                print(f"    [{severity.upper()}] {issue.get('title', 'Unknown issue')}")
        else:
            print("    No issues found")

    print("\n" + "=" * 60)
    print(f"  Sites analyzed: {len(results)}")
    print(f"  Sites with issues: {sites_with_issues}")
    print(f"  Total issues found: {total_issues}")
    print(f"  High severity: {high_severity}")
    print("=" * 60)
    print(f"\nResults saved to: {AUDIT_RESULTS_FILE}")


if __name__ == "__main__":
    main()
