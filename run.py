#!/usr/bin/env python3
"""
Shopify UI Audit - Unified CLI Runner

A streamlined interface to discover Shopify stores, audit their UIs,
and generate outreach emails.

Usage:
    python run.py              # Interactive mode
    python run.py --help       # Show all options
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, List

import typer
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich import print as rprint

# Project paths
PROJECT_ROOT = Path(__file__).parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CONFIG_DIR = PROJECT_ROOT / "config"
INPUT_DIR = PROJECT_ROOT / "input"
DISCOVERY_DIR = PROJECT_ROOT / "discovery"
VERIFICATION_DIR = PROJECT_ROOT / "verification"
AUDITS_DIR = PROJECT_ROOT / "audits"
CONTACTS_DIR = PROJECT_ROOT / "contacts"
OUTREACH_DIR = PROJECT_ROOT / "outreach"

# Initialize
app = typer.Typer(
    name="shopify-audit",
    help="Shopify UI Audit Tool - Discover, audit, and outreach",
    add_completion=False,
)
console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
[bold cyan]╔═══════════════════════════════════════════════════════════╗
║         🔍 Shopify UI Audit Tool                          ║
║         Discover • Audit • Outreach                       ║
╚═══════════════════════════════════════════════════════════╝[/bold cyan]
"""
    console.print(banner)


def run_script(script_name: str, args: List[str] = None, show_output: bool = True) -> tuple[bool, str]:
    """
    Run a Python script from the scripts directory.

    Returns:
        Tuple of (success, output)
    """
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    try:
        env = os.environ.copy()
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=not show_output,
            text=True,
            env=env,
        )

        if show_output and result.returncode != 0:
            return False, f"Script exited with code {result.returncode}"

        return result.returncode == 0, result.stdout if not show_output else ""
    except Exception as e:
        return False, str(e)


def get_file_count(filepath: Path, key: str = None) -> int:
    """Get count of items from a JSON file."""
    try:
        if filepath.exists():
            with open(filepath) as f:
                data = json.load(f)
                # Check metadata for total counts first
                metadata = data.get("metadata", {})
                if key == "discoveries" and "total_urls" in metadata:
                    return metadata["total_urls"]
                if key == "shopify_sites" and "shopify_count" in metadata:
                    return metadata["shopify_count"]
                if key == "audits" and "total_audited" in metadata:
                    return metadata["total_audited"]
                if key == "contacts" and "sites_with_contacts" in metadata:
                    return metadata["sites_with_contacts"]
                # Fallback to counting items in the key
                if key:
                    items = data.get(key, [])
                    if isinstance(items, list):
                        return len(items)
                    return 0
                return len(data)
    except:
        pass
    return 0


def update_niches_file(niches: List[str]):
    """Update the niches.txt file with new niches."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    niches_file = INPUT_DIR / "niches.txt"

    with open(niches_file, "w") as f:
        f.write("# Niche keywords for Shopify store discovery\n")
        f.write("# One niche per line\n\n")
        for niche in niches:
            f.write(f"{niche}\n")


def update_settings(settings: dict):
    """Update specific settings in config/settings.py."""
    settings_file = CONFIG_DIR / "settings.py"

    with open(settings_file, "r") as f:
        content = f.read()

    for key, value in settings.items():
        import re
        if isinstance(value, str):
            pattern = rf'^{key}\s*=\s*.*$'
            replacement = f'{key} = "{value}"'
        else:
            pattern = rf'^{key}\s*=\s*.*$'
            replacement = f'{key} = {value}'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(settings_file, "w") as f:
        f.write(content)


def check_gemini_key() -> bool:
    """Check if Gemini API key is configured."""
    return bool(os.environ.get("GEMINI_API_KEY"))


def prompt_for_settings() -> dict:
    """Interactive prompts for pipeline settings."""
    settings = {}

    console.print("\n[bold yellow]📋 Configuration[/bold yellow]\n")

    # Niches
    niches_input = questionary.text(
        "Enter niches (comma-separated):",
        default="sustainable fashion, organic skincare",
        instruction="e.g., fitness gear, pet supplies, home decor"
    ).ask()

    if niches_input is None:
        raise typer.Abort()

    settings["niches"] = [n.strip() for n in niches_input.split(",") if n.strip()]

    # Max sites per niche
    max_sites = questionary.text(
        "Max sites per niche:",
        default="50",
        validate=lambda x: x.isdigit() and int(x) > 0
    ).ask()

    if max_sites is None:
        raise typer.Abort()

    settings["max_sites"] = int(max_sites)

    # Min Shopify confidence
    min_confidence = questionary.text(
        "Min Shopify confidence score (0-100):",
        default="60",
        validate=lambda x: x.isdigit() and 0 <= int(x) <= 100
    ).ask()

    if min_confidence is None:
        raise typer.Abort()

    settings["min_confidence"] = int(min_confidence)

    # Gemini API key
    if not check_gemini_key():
        console.print("\n[yellow]⚠ Gemini API key not found in environment[/yellow]")
        gemini_key = questionary.password(
            "Enter Gemini API key (or press Enter to skip AI analysis):"
        ).ask()

        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
            settings["gemini_key"] = gemini_key
    else:
        console.print("[green]✓ Gemini API key found[/green]")

    # Sender info
    console.print("\n[bold yellow]📧 Outreach Settings[/bold yellow]\n")

    sender_name = questionary.text(
        "Your name (for email drafts):",
        default="Your Name"
    ).ask()

    if sender_name is None:
        raise typer.Abort()

    settings["sender_name"] = sender_name

    sender_title = questionary.text(
        "Your title:",
        default="UI/UX Consultant"
    ).ask()

    if sender_title is None:
        raise typer.Abort()

    settings["sender_title"] = sender_title

    return settings


def show_summary(settings: dict):
    """Display configuration summary."""
    table = Table(title="Configuration Summary", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="dim")
    table.add_column("Value")

    table.add_row("Niches", ", ".join(settings["niches"]))
    table.add_row("Max sites/niche", str(settings["max_sites"]))
    table.add_row("Min confidence", f"{settings['min_confidence']}%")
    table.add_row("Gemini AI", "✓ Enabled" if check_gemini_key() else "✗ Disabled")
    table.add_row("Sender name", settings["sender_name"])
    table.add_row("Sender title", settings["sender_title"])

    console.print()
    console.print(table)
    console.print()


def run_pipeline(settings: dict, skip_discovery: bool = False):
    """Run the full pipeline with progress display."""

    steps = [
        ("discover_sites.py", "Discovering sites", "discoveries", DISCOVERY_DIR / "discovered_sites.json"),
        ("verify_shopify.py", "Verifying Shopify stores", "shopify_sites", VERIFICATION_DIR / "shopify_sites.json"),
        ("audit_homepage.py", "Auditing homepages", "audits", AUDITS_DIR / "audit_results.json"),
        ("analyze_with_gemini.py", "Analyzing with Gemini AI", "audits", AUDITS_DIR / "audit_results.json"),
        ("extract_contacts.py", "Extracting contacts", "contacts", CONTACTS_DIR / "contacts.json"),
        ("generate_outreach.py", "Generating outreach emails", None, OUTREACH_DIR / "drafts"),
    ]

    if skip_discovery:
        steps = steps[1:]

    # Skip Gemini if no API key
    if not check_gemini_key():
        steps = [s for s in steps if "gemini" not in s[0]]
        console.print("[yellow]⚠ Skipping Gemini analysis (no API key)[/yellow]\n")

    results = {}

    console.print("\n[bold green]🚀 Starting Pipeline[/bold green]\n")

    for i, (script, description, json_key, output_path) in enumerate(steps, 1):
        step_num = f"[{i}/{len(steps)}]"

        # Build arguments
        args = []
        if script == "verify_shopify.py":
            args.extend(["--min-confidence", str(settings["min_confidence"])])
        elif script == "generate_outreach.py":
            args.extend(["--sender-name", settings["sender_name"]])
            args.extend(["--sender-title", settings["sender_title"]])

        console.print(f"{step_num} [cyan]⠋ {description}...[/cyan]")

        success, error = run_script(script, args, show_output=True)

        if success:
            # Get count of results
            if json_key and output_path.exists():
                count = get_file_count(output_path, json_key)
                results[script] = count
                console.print(f"{step_num} [green]✓ {description}[/green] - {count} items")

                # Check if we have 0 Shopify stores after verification
                if script == "verify_shopify.py" and count == 0:
                    console.print("\n[yellow]⚠ No Shopify stores found. Pipeline will end here.[/yellow]")
                    console.print("[dim]Try different niches or broader search terms.[/dim]\n")
                    break
            elif output_path.is_dir() and output_path.exists():
                count = len(list(output_path.glob("*.txt")))
                results[script] = count
                console.print(f"{step_num} [green]✓ {description}[/green] - {count} drafts")
            else:
                console.print(f"{step_num} [green]✓ {description}[/green]")
        else:
            console.print(f"{step_num} [red]✗ {description} failed[/red]")
            if error:
                console.print(f"    [dim]{error}[/dim]")

            # Check if it's due to no data (not a real failure)
            if "No URLs" in error or "No verified" in error or "exit code 1" in error:
                console.print("[yellow]⚠ No data to process at this step.[/yellow]")
                if i < len(steps):
                    continue  # Skip to next step or end gracefully

            # Ask to continue only for real errors
            elif i < len(steps):
                if not questionary.confirm("Continue with next step?", default=True).ask():
                    break

        console.print()

    return results


def show_final_report(results: dict):
    """Show final pipeline results."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]✓ Pipeline Complete![/bold green]",
        border_style="green"
    ))

    # Results table
    table = Table(title="Results Summary", show_header=True, header_style="bold cyan")
    table.add_column("Step", style="dim")
    table.add_column("Count", justify="right")

    step_names = {
        "discover_sites.py": "Sites Discovered",
        "verify_shopify.py": "Shopify Verified",
        "audit_homepage.py": "Audits Complete",
        "analyze_with_gemini.py": "AI Analyzed",
        "extract_contacts.py": "Contacts Found",
        "generate_outreach.py": "Email Drafts",
    }

    for script, count in results.items():
        table.add_row(step_names.get(script, script), str(count))

    console.print()
    console.print(table)

    # Output locations
    console.print("\n[bold yellow]📁 Output Files:[/bold yellow]")
    console.print(f"  • Discovered sites: [dim]{DISCOVERY_DIR / 'discovered_sites.json'}[/dim]")
    console.print(f"  • Verified Shopify: [dim]{VERIFICATION_DIR / 'shopify_sites.json'}[/dim]")
    console.print(f"  • Audit results:    [dim]{AUDITS_DIR / 'audit_results.json'}[/dim]")
    console.print(f"  • Contacts:         [dim]{CONTACTS_DIR / 'contacts.json'}[/dim]")
    console.print(f"  • Email drafts:     [dim]{OUTREACH_DIR / 'drafts/'}[/dim]")
    console.print()


@app.command()
def interactive():
    """Run the full pipeline interactively (default)."""
    print_banner()

    try:
        # Get settings from user
        settings = prompt_for_settings()

        # Show summary and confirm
        show_summary(settings)

        if not questionary.confirm("Start the pipeline?", default=True).ask():
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Abort()

        # Update niches file
        update_niches_file(settings["niches"])

        # Update settings file
        update_settings({
            "MAX_SITES_PER_NICHE": settings["max_sites"],
            "MIN_SHOPIFY_CONFIDENCE": settings["min_confidence"],
            "SENDER_NAME": settings["sender_name"],
            "SENDER_TITLE": settings["sender_title"],
        })

        # Run pipeline
        results = run_pipeline(settings)

        # Show report
        show_final_report(results)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        raise typer.Abort()


@app.command()
def run(
    niches: str = typer.Option(None, "--niches", "-n", help="Comma-separated niches"),
    max_sites: int = typer.Option(50, "--max-sites", "-m", help="Max sites per niche"),
    min_confidence: int = typer.Option(60, "--confidence", "-c", help="Min Shopify confidence"),
    sender_name: str = typer.Option("Your Name", "--sender-name", help="Sender name for emails"),
    sender_title: str = typer.Option("UI/UX Consultant", "--sender-title", help="Sender title"),
    skip_discovery: bool = typer.Option(False, "--skip-discovery", help="Skip discovery step"),
):
    """Run the pipeline with command-line arguments."""
    print_banner()

    if not niches and not skip_discovery:
        console.print("[red]Error: --niches is required (or use --skip-discovery)[/red]")
        raise typer.Abort()

    settings = {
        "niches": [n.strip() for n in niches.split(",")] if niches else [],
        "max_sites": max_sites,
        "min_confidence": min_confidence,
        "sender_name": sender_name,
        "sender_title": sender_title,
    }

    if niches:
        update_niches_file(settings["niches"])

    update_settings({
        "MAX_SITES_PER_NICHE": max_sites,
        "MIN_SHOPIFY_CONFIDENCE": min_confidence,
        "SENDER_NAME": sender_name,
        "SENDER_TITLE": sender_title,
    })

    show_summary(settings)

    results = run_pipeline(settings, skip_discovery=skip_discovery)
    show_final_report(results)


@app.command()
def status():
    """Show current pipeline status and data counts."""
    print_banner()

    console.print("[bold yellow]📊 Pipeline Status[/bold yellow]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Data", style="dim")
    table.add_column("Count", justify="right")
    table.add_column("File")

    files = [
        ("Discovered Sites", "discoveries", DISCOVERY_DIR / "discovered_sites.json"),
        ("Verified Shopify", "shopify_sites", VERIFICATION_DIR / "shopify_sites.json"),
        ("Audits", "audits", AUDITS_DIR / "audit_results.json"),
        ("Contacts", "contacts", CONTACTS_DIR / "contacts.json"),
    ]

    for name, key, path in files:
        count = get_file_count(path, key) if path.exists() else 0
        status = "✓" if path.exists() else "✗"
        table.add_row(name, str(count), f"{status} {path.name}")

    # Count drafts
    drafts_dir = OUTREACH_DIR / "drafts"
    draft_count = len(list(drafts_dir.glob("*.txt"))) if drafts_dir.exists() else 0
    table.add_row("Email Drafts", str(draft_count), f"{'✓' if draft_count else '✗'} drafts/")

    console.print(table)
    console.print()


@app.command()
def add_urls(
    urls: str = typer.Option(None, "--urls", "-u", help="Comma-separated URLs to add"),
    file: str = typer.Option(None, "--file", "-f", help="File containing URLs (one per line)"),
):
    """Add URLs manually and run the pipeline (bypasses discovery)."""
    print_banner()

    url_list = []

    # Get URLs from command line
    if urls:
        url_list.extend([u.strip() for u in urls.split(",") if u.strip()])

    # Get URLs from file
    if file:
        file_path = Path(file)
        if file_path.exists():
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        url_list.append(line)
            console.print(f"[green]✓ Loaded {len(url_list)} URLs from {file}[/green]")
        else:
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Abort()

    # Interactive input if no URLs provided
    if not url_list:
        console.print("[bold yellow]📝 Enter URLs manually[/bold yellow]")
        console.print("[dim]Enter Shopify store URLs (one per line). Enter empty line when done.[/dim]\n")

        while True:
            url = questionary.text("URL (or Enter to finish):").ask()
            if url is None:
                raise typer.Abort()
            if not url:
                break
            if url.startswith("http"):
                url_list.append(url)
            else:
                url_list.append(f"https://{url}")

    if not url_list:
        console.print("[red]No URLs provided.[/red]")
        raise typer.Abort()

    # Deduplicate
    url_list = list(set(url_list))
    console.print(f"\n[green]✓ {len(url_list)} URLs to process[/green]\n")

    # Create discovery file with manual URLs
    DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)
    discovery_data = {
        "metadata": {
            "generated_at": __import__("datetime").datetime.now().isoformat(),
            "total_niches": 1,
            "total_urls": len(url_list),
            "source": "manual_input"
        },
        "discoveries": [{
            "niche": "manual_input",
            "discovered_at": __import__("datetime").datetime.now().isoformat(),
            "total_urls": len(url_list),
            "urls": url_list
        }]
    }

    with open(DISCOVERY_DIR / "discovered_sites.json", "w") as f:
        json.dump(discovery_data, f, indent=2)

    # Get settings
    console.print("[bold yellow]📧 Outreach Settings[/bold yellow]\n")

    sender_name = questionary.text("Your name:", default="Your Name").ask()
    sender_title = questionary.text("Your title:", default="UI/UX Consultant").ask()

    if not sender_name or not sender_title:
        raise typer.Abort()

    settings = {
        "niches": ["manual_input"],
        "max_sites": len(url_list),
        "min_confidence": 50,
        "sender_name": sender_name,
        "sender_title": sender_title,
    }

    # Run pipeline starting from verification (skip discovery)
    results = run_pipeline(settings, skip_discovery=True)
    show_final_report(results)


@app.command()
def clean():
    """Clean all output files and start fresh."""
    print_banner()

    if not questionary.confirm(
        "This will delete all discovered data. Continue?",
        default=False
    ).ask():
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Abort()

    import shutil

    dirs_to_clean = [
        DISCOVERY_DIR,
        VERIFICATION_DIR,
        AUDITS_DIR,
        CONTACTS_DIR,
        OUTREACH_DIR / "drafts",
    ]

    for dir_path in dirs_to_clean:
        if dir_path.exists():
            if dir_path.is_file():
                dir_path.unlink()
            else:
                for f in dir_path.iterdir():
                    if f.is_file():
                        f.unlink()
                    elif f.is_dir():
                        shutil.rmtree(f)

    console.print("[green]✓ All output files cleaned![/green]")


def main():
    """Main entry point."""
    # If no arguments, run interactive mode
    if len(sys.argv) == 1:
        interactive()
    else:
        app()


if __name__ == "__main__":
    main()
