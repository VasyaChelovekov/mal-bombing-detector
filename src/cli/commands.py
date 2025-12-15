"""
Command-line interface for MAL Bombing Detector.

Provides multiple commands for analyzing anime review bombing:
- analyze: Analyze top N anime
- single: Deep-dive analysis of a single anime
- compare: Compare bombing metrics between anime
- batch: Batch analysis from file
- serve: Start REST API server
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..core import (
    AnimeData,
    AnalysisResult,
    BombingAnalyzer,
    SuspicionLevel,
)
from ..exporters import get_exporter
from ..platforms import get_platform, AnimePlatform
from ..utils import get_logger, reload_config, set_language
from ..utils.config import ExportConfig


# Initialize
app = typer.Typer(
    name="mal-detector",
    help="MAL Bombing Detector - Detect vote brigading on anime platforms",
    add_completion=False,
)
console = Console()
logger = get_logger(__name__)


def get_level_color(level: SuspicionLevel) -> str:
    """Get Rich color for suspicion level."""
    return {
        SuspicionLevel.CRITICAL: "red",
        SuspicionLevel.HIGH: "orange1",
        SuspicionLevel.MEDIUM: "yellow",
        SuspicionLevel.LOW: "green",
    }.get(level, "white")


def get_level_emoji(level: SuspicionLevel) -> str:
    """Get emoji for suspicion level."""
    return {
        SuspicionLevel.CRITICAL: "🔴",
        SuspicionLevel.HIGH: "🟠",
        SuspicionLevel.MEDIUM: "🟡",
        SuspicionLevel.LOW: "🟢",
    }.get(level, "⚪")


def print_header():
    """Print application header."""
    console.print()
    console.print("╔══════════════════════════════════════════════════════════════╗", style="cyan")
    console.print("║         [bold]MAL BOMBING DETECTOR[/bold] v2.0                            ║", style="cyan")
    console.print("║         Vote brigading detection for anime platforms         ║", style="cyan")
    console.print("╚══════════════════════════════════════════════════════════════╝", style="cyan")
    console.print()


def print_results(results: AnalysisResult, top_n: int = 20):
    """Print analysis results in a formatted table."""
    console.print()
    console.print(f"[bold]{'=' * 80}[/bold]")
    console.print(f"[bold]TOP {top_n} ANIME WITH HIGHEST BOMBING SUSPICION[/bold]")
    console.print(f"[bold]{'=' * 80}[/bold]")
    console.print()
    
    for metrics in results.get_top(top_n):
        emoji = get_level_emoji(metrics.suspicion_level)
        color = get_level_color(metrics.suspicion_level)
        level = metrics.suspicion_level.value.upper()
        
        console.print(
            f"#{metrics.bombing_rank:>3} {emoji} [bold]{metrics.title}[/bold]"
        )
        console.print(
            f"     Bombing Score: [{color}]{metrics.bombing_score:.2f}[/{color}] "
            f"([{color}]{level}[/{color}])"
        )
        console.print(
            f"     Ones: {metrics.ones_percentage:.2f}% | "
            f"Tens: {metrics.tens_percentage:.2f}%"
        )
        if metrics.anomaly_flags:
            flags = ", ".join(metrics.anomaly_flags[:3])
            console.print(f"     [dim]Flags: {flags}[/dim]")
        console.print()
    
    # Summary
    summary = results.summary
    console.print(f"[bold]{'=' * 80}[/bold]")
    console.print("[bold]SUMMARY[/bold]")
    console.print(f"[bold]{'=' * 80}[/bold]")
    console.print(f"Total analyzed: {summary.total_analyzed} anime")
    console.print(f"Average Bombing Score: {summary.score_mean:.2f}")
    console.print()
    console.print("Distribution by levels:")
    console.print(f"  🔴 Critical: {summary.critical_count}")
    console.print(f"  🟠 High: {summary.high_count}")
    console.print(f"  🟡 Medium: {summary.medium_count}")
    console.print(f"  🟢 Low: {summary.low_count}")


async def run_analysis(
    platform: AnimePlatform,
    limit: int,
    no_cache: bool,
) -> AnalysisResult:
    """Run the main analysis workflow."""
    anime_list: List[AnimeData] = []
    
    # Fetch top anime
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Fetching top {limit} anime...", total=None)
        
        top_anime = await platform.get_top_anime(limit)
        progress.update(task, completed=True)
        
        logger.info(f"Fetched {len(top_anime)} anime from rankings")
    
    # Fetch stats for each anime
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Collecting statistics...", total=len(top_anime))
        
        for anime in top_anime:
            try:
                stats = await platform.get_anime_stats(anime.mal_id)
                if stats and stats.distribution:
                    # Merge data
                    stats.rank = anime.rank
                    stats.members = anime.members or stats.members
                    anime_list.append(stats)
            except Exception as e:
                logger.warning(f"Failed to get stats for {anime.mal_id}: {e}")
            
            progress.advance(task)
    
    logger.info(f"Collected stats for {len(anime_list)} anime")
    
    # Analyze
    analyzer = BombingAnalyzer()
    results = analyzer.analyze_batch(anime_list)
    
    return results


@app.command()
def analyze(
    limit: int = typer.Option(
        50,
        "--limit", "-n",
        help="Number of top anime to analyze",
    ),
    platform: str = typer.Option(
        "myanimelist",
        "--platform", "-p",
        help="Platform to analyze (myanimelist, anilist, kitsu)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory for reports",
    ),
    format: str = typer.Option(
        "excel,json",
        "--format", "-f",
        help="Export format(s), comma-separated (excel, csv, json, html)",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable caching",
    ),
    no_charts: bool = typer.Option(
        False,
        "--no-charts",
        help="Disable chart generation",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to configuration file",
    ),
    language: str = typer.Option(
        "en",
        "--lang", "-l",
        help="Language for output (en, ru, es, ja, zh, de, fr)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output",
    ),
):
    """
    Analyze top anime for review bombing.
    
    Fetches the top N anime from the specified platform and
    analyzes their score distributions for signs of vote
    manipulation.
    
    Examples:
        mal-analyzer analyze -n 100
        mal-analyzer analyze --limit 50 --format excel,json
        mal-analyzer analyze -n 100 -o ./reports -f json
    """
    # Setup
    if config_file:
        reload_config(config_file)
    set_language(language)
    
    print_header()
    
    try:
        # Get platform
        plat = get_platform(platform)
        
        # Run analysis
        async def main():
            async with plat:
                return await run_analysis(plat, limit, no_cache)
        
        results = asyncio.run(main())
        
        # Print results
        print_results(results)
        
        # Export to requested formats
        console.print()
        console.print("[bold]Exporting results...[/bold]")
        
        # Determine output directory
        output_dir = output or Path("output/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create export config
        export_config = ExportConfig(
            output_directory=str(output_dir),
        )
        
        # Export to each format
        formats = [f.strip().lower() for f in format.split(",")]
        exported_files = []
        
        for fmt in formats:
            try:
                exporter = get_exporter(fmt, export_config)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"top_{limit}_analysis_{timestamp}"
                filepath = output_dir / f"{filename}.{exporter.file_extension}"
                
                exporter.export(results, filepath)
                exported_files.append(filepath)
                console.print(f"   ✅ {fmt.upper()}: {filepath}")
            except Exception as e:
                console.print(f"   ❌ {fmt.upper()}: {e}")
                if verbose:
                    console.print_exception()
        
        console.print()
        console.print("[green]✅ Analysis complete![/green]")
        console.print(f"   Analyzed: {results.summary.total_analyzed} anime")
        console.print(f"   🔴 Critical: {results.summary.critical_count}")
        console.print(f"   🟠 High: {results.summary.high_count}")
        console.print(f"   🟡 Medium: {results.summary.medium_count}")
        console.print(f"   🟢 Low: {results.summary.low_count}")
        
        if exported_files:
            console.print()
            console.print("[bold]Output files:[/bold]")
            for f in exported_files:
                console.print(f"   📄 {f}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def single(
    anime_id: int = typer.Argument(..., help="Anime ID to analyze"),
    platform: str = typer.Option(
        "myanimelist",
        "--platform", "-p",
        help="Platform (myanimelist, anilist, kitsu)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output",
    ),
):
    """
    Deep-dive analysis of a single anime.
    
    Provides detailed bombing analysis for a specific anime ID.
    
    Example:
        mal-analyzer single 52991  # Frieren
    """
    print_header()
    
    try:
        plat = get_platform(platform)
        
        async def main():
            async with plat:
                console.print(f"Fetching data for anime ID {anime_id}...")
                stats = await plat.get_anime_stats(anime_id)
                
                if not stats:
                    console.print(f"[red]Anime {anime_id} not found[/red]")
                    raise typer.Exit(1)
                
                if not stats.distribution:
                    console.print(f"[red]No distribution data for {anime_id}[/red]")
                    raise typer.Exit(1)
                
                analyzer = BombingAnalyzer()
                metrics = analyzer.analyze_single(stats)
                
                return stats, metrics
        
        anime, metrics = asyncio.run(main())
        
        # Print detailed results
        console.print()
        console.print(f"[bold]Analysis for: {anime.title}[/bold]")
        console.print(f"MAL ID: {anime.mal_id}")
        console.print(f"Score: {anime.score}")
        console.print(f"Total Votes: {anime.distribution.total_votes:,}")
        console.print()
        
        emoji = get_level_emoji(metrics.suspicion_level)
        color = get_level_color(metrics.suspicion_level)
        
        console.print(f"[bold]Bombing Score:[/bold] [{color}]{metrics.bombing_score:.2f}[/{color}]")
        console.print(f"[bold]Suspicion Level:[/bold] {emoji} [{color}]{metrics.suspicion_level.value.upper()}[/{color}]")
        console.print()
        
        # Metrics table
        table = Table(title="Metric Breakdown")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_column("Score", justify="right")
        
        table.add_row("Ones Z-Score", f"{metrics.ones_zscore:.2f}", f"{metrics.metric_breakdown.get('ONES_Z', 0):.2f}")
        table.add_row("Spike Ratio", f"{metrics.spike_ratio:.2f}", f"{metrics.metric_breakdown.get('SPIKE', 0):.2f}")
        table.add_row("Effect Size", f"{metrics.distribution_effect_size:.3f}", f"{metrics.metric_breakdown.get('EFFECT', 0):.2f}")
        table.add_row("Entropy Deficit", f"{metrics.entropy_deficit:.3f}", f"{metrics.metric_breakdown.get('ENTROPY', 0):.2f}")
        table.add_row("Bimodality", f"{metrics.bimodality_coefficient:.3f}", f"{metrics.metric_breakdown.get('BIMODAL', 0):.2f}")
        
        console.print(table)
        
        # Anomaly flags
        if metrics.anomaly_flags:
            console.print()
            console.print("[bold]Anomaly Flags:[/bold]")
            for flag in metrics.anomaly_flags:
                console.print(f"  ⚠️  {flag}")
        
        # Severity
        if metrics.severity:
            console.print()
            console.print(f"[bold]Severity:[/bold] {metrics.severity.level.value}")
            console.print(f"  {metrics.severity.description}")
            console.print(f"  Estimated fake votes: {metrics.severity.estimated_fake_votes:,}")
            console.print(f"  Rating impact: {metrics.severity.rating_impact:.3f}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def compare(
    ids: str = typer.Argument(
        ...,
        help="Comma-separated anime IDs to compare",
    ),
    platform: str = typer.Option(
        "myanimelist",
        "--platform", "-p",
        help="Platform (myanimelist, anilist, kitsu)",
    ),
):
    """
    Compare bombing metrics between anime.
    
    Example:
        mal-analyzer compare 52991,57555,5114
    """
    print_header()
    
    anime_ids = [int(x.strip()) for x in ids.split(",")]
    console.print(f"Comparing {len(anime_ids)} anime...")
    
    try:
        plat = get_platform(platform)
        
        async def main():
            async with plat:
                results = []
                for aid in anime_ids:
                    stats = await plat.get_anime_stats(aid)
                    if stats and stats.distribution:
                        analyzer = BombingAnalyzer()
                        metrics = analyzer.analyze_single(stats)
                        results.append((stats, metrics))
                return results
        
        comparisons = asyncio.run(main())
        
        # Print comparison table
        table = Table(title="Bombing Comparison")
        table.add_column("Title", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Ones %", justify="right")
        table.add_column("Bombing Score", justify="right")
        table.add_column("Level")
        
        for anime, metrics in comparisons:
            color = get_level_color(metrics.suspicion_level)
            emoji = get_level_emoji(metrics.suspicion_level)
            
            table.add_row(
                anime.title[:40],
                f"{anime.score:.2f}",
                f"{metrics.ones_percentage:.2f}%",
                f"[{color}]{metrics.bombing_score:.2f}[/{color}]",
                f"{emoji} {metrics.suspicion_level.value}",
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    console.print("MAL Bombing Detector v2.0.0")
    console.print("https://github.com/VasyaChelovekov/mal-bombing-detector")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
