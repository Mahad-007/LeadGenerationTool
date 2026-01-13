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
    pip install google-generativeai pillow
"""

import sys
import json
import logging
import argparse
import base64
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import google.generativeai as genai
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
    LCP_THRESHOLD_MS,
    CLS_THRESHOLD,
    DESKTOP_FOLD_LINE,
    MOBILE_FOLD_LINE,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Analysis prompt for Gemini
ANALYSIS_PROMPT = """You are a professional UI/UX auditor analyzing a Shopify store homepage.

CRITICAL INSTRUCTIONS:
1. Report ONLY high-confidence, objectively verifiable UI issues
2. Each issue MUST have specific visual evidence from the screenshots
3. Report maximum {max_issues} issues total
4. DO NOT include subjective opinions or preferences
5. DO NOT hallucinate or assume issues not visible in screenshots
6. Focus on issues that demonstrably impact conversion or usability

OBJECTIVE CRITERIA TO CHECK:

1. CTA Visibility (Above the Fold)
   - Is there a clear call-to-action button visible without scrolling?
   - Fold line for desktop: {desktop_fold}px, mobile: {mobile_fold}px
   - Evidence: Button position coordinates, visibility in screenshot

2. Performance Issues (from metrics)
   - LCP > {lcp_threshold}ms indicates slow loading
   - Console errors indicate JavaScript problems
   - Evidence: Specific metric values provided

3. Layout/Visual Issues
   - Broken images (src errors, missing images)
   - Text overlapping elements
   - Elements cut off or misaligned
   - Evidence: Visible in screenshot with specific location

4. Mobile Responsiveness
   - Content overflow or horizontal scroll
   - Touch targets too small or too close
   - Text too small to read
   - Evidence: Visible in mobile screenshot

5. Console Errors
   - JavaScript errors that may affect functionality
   - Evidence: Specific error messages from console log

PROVIDED DATA:
- Desktop screenshot
- Mobile screenshot
- Performance metrics: {metrics}
- DOM analysis: {dom_info}
- Console errors: {console_errors}

REQUIRED JSON OUTPUT FORMAT:
{{
    "issues": [
        {{
            "id": "issue_1",
            "category": "cta_visibility|performance|layout|mobile|console_error",
            "severity": "high|medium|low",
            "title": "Brief issue title",
            "description": "Specific description with evidence",
            "evidence": "Exact evidence from screenshot/metrics/console",
            "recommendation": "Specific actionable fix"
        }}
    ],
    "summary": {{
        "total_issues": 0,
        "high_severity": 0,
        "medium_severity": 0,
        "low_severity": 0,
        "primary_concern": "Most important issue or 'None' if no issues"
    }}
}}

If NO clear issues are found, return:
{{
    "issues": [],
    "summary": {{
        "total_issues": 0,
        "high_severity": 0,
        "medium_severity": 0,
        "low_severity": 0,
        "primary_concern": "None - homepage appears well-optimized"
    }}
}}

Analyze the screenshots and data now. Return ONLY valid JSON, no other text."""


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

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
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
            "analyzed_at": datetime.utcnow().isoformat(),
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

            # Prepare prompt with data
            prompt = ANALYSIS_PROMPT.format(
                max_issues=MAX_ISSUES_PER_SITE,
                desktop_fold=DESKTOP_FOLD_LINE,
                mobile_fold=MOBILE_FOLD_LINE,
                lcp_threshold=LCP_THRESHOLD_MS,
                metrics=self._prepare_metrics_summary(audit_data),
                dom_info=self._prepare_dom_summary(audit_data),
                console_errors=self._prepare_console_errors(audit_data),
            )

            # Build content list for Gemini
            content = [prompt]
            for img, label in zip(images, image_labels):
                content.append(f"\n{label}:")
                content.append(img)

            # Call Gemini API
            logger.info("  Sending to Gemini API...")
            response = self.model.generate_content(content)

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

        data["metadata"]["analysis_completed_at"] = datetime.utcnow().isoformat()
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
