"""Command-line interface for WSWS Bulletin."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import click

from .config import Config
from .scraper import WWSSScraper
from .synthesizer import ArticleSynthesizer
from .text_to_speech import TextToSpeech, get_available_engines


def setup_logging(verbose: bool = False):
    """Configure logging for the application.

    Args:
        verbose: Enable debug logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s:%(levelname)s:%(module)s:%(message)s',
        datefmt='%H:%M:%S'
    )


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """WSWS Bulletin - Automated daily bulletin from World Socialist Web Site.

    This tool scrapes recent articles and perspectives from WSWS, synthesizes
    them using AI, and converts the summary to audio.
    """
    pass


@cli.command()
@click.option(
    "--hours",
    default=24,
    type=int,
    help="Number of hours to look back for recent articles (default: 24)"
)
@click.option(
    "--output-dir",
    default=None,
    type=click.Path(),
    help="Output directory for generated files (default: ./output or from config)"
)
@click.option(
    "--no-audio",
    is_flag=True,
    help="Skip audio generation, only create markdown bulletin"
)
@click.option(
    "--ai-provider",
    type=click.Choice(["openai", "anthropic"], case_sensitive=False),
    help="AI provider to use (default: from config or 'anthropic')"
)
@click.option(
    "--tts-engine",
    type=click.Choice(["coqui", "openai"], case_sensitive=False),
    help="TTS engine to use (default: from config or 'coqui')"
)
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="Path to .env file with configuration"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging (debug mode)"
)
@click.option(
    "--print-summary",
    is_flag=True,
    help="Print the text summary to stdout after generation"
)
def generate(hours, output_dir, no_audio, ai_provider, tts_engine, env_file, verbose, print_summary):
    """Generate a daily bulletin from WSWS articles.

    This command:
    1. Scrapes recent articles from WSWS
    2. Fetches the latest perspective article
    3. Synthesizes and summarizes using AI
    4. Converts the summary to audio (unless --no-audio is used)
    """
    # Setup logging
    setup_logging(verbose=verbose)

    # Load configuration
    config = Config(env_file=env_file)

    # Override config with CLI options
    if ai_provider:
        os.environ["AI_PROVIDER"] = ai_provider
    if tts_engine:
        os.environ["TTS_ENGINE"] = tts_engine
    if output_dir:
        os.environ["OUTPUT_DIR"] = output_dir

    # Validate configuration
    errors = config.validate()
    if errors:
        click.echo("Configuration errors:", err=True)
        for error in errors:
            click.echo(f"  • {error}", err=True)
        click.echo("\nPlease check your .env file or environment variables.", err=True)
        sys.exit(1)

    # Create output directory
    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    click.echo("=" * 60)
    click.echo("WSWS Bulletin Generator".center(60))
    click.echo("=" * 60)
    click.echo()

    # Step 1: Scrape articles
    click.echo("Step 1: Scraping WSWS articles")
    click.echo("-" * 60)
    scraper = WWSSScraper(
        cache_enabled=config.cache_enabled,
        cache_expire_minutes=config.cache_expire_minutes
    )
    content = scraper.fetch_all_content(hours=hours)

    num_articles = len(content.get('articles', []))
    has_perspective = content.get('perspective') is not None

    click.echo(f"✓ Fetched {num_articles} recent articles")
    click.echo(f"✓ Fetched perspective: {'Yes' if has_perspective else 'No'}")
    click.echo()

    if num_articles == 0 and not has_perspective:
        click.echo("No articles found. Nothing to synthesize.", err=True)
        sys.exit(1)

    # Step 2: Synthesize with AI
    click.echo("Step 2: Synthesizing with AI")
    click.echo("-" * 60)

    # Get model name based on provider
    model_name = config.anthropic_model if config.ai_provider == "anthropic" else config.openai_model
    click.echo(f"Using provider: {config.ai_provider}")
    click.echo(f"Using model: {model_name}")

    synthesizer = ArticleSynthesizer(
        provider=config.ai_provider,
        api_key=config.get_api_key(),
        model=model_name
    )

    bulletin_text = synthesizer.generate_bulletin(content)
    click.echo("✓ Synthesis complete")
    click.echo()

    # Save markdown bulletin
    date_str = datetime.now().strftime("%Y-%m-%d")
    text_filename = f"bulletin_{date_str}.md"
    text_path = output_path / text_filename

    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(bulletin_text)

    click.echo(f"✓ Markdown bulletin saved: {text_path}")
    click.echo()

    # Step 3: Convert to audio (optional)
    if not no_audio:
        click.echo("Step 3: Converting to audio")
        click.echo("-" * 60)
        click.echo(f"Using TTS engine: {config.tts_engine}")

        tts = TextToSpeech(
            engine=config.tts_engine,
            api_key=config.openai_api_key if config.tts_engine == "openai" else None
        )

        audio_path = tts.convert_bulletin(
            bulletin_text,
            output_dir=str(output_path)
        )

        click.echo(f"✓ Audio saved: {audio_path}")
        click.echo()

    # Summary
    click.echo("=" * 60)
    click.echo("✓ Bulletin generation complete!")
    click.echo("=" * 60)
    click.echo(f"Output directory: {output_path}")
    click.echo(f"Markdown file: {text_filename}")
    click.echo()

    # Print summary if requested
    if print_summary:
        click.echo("=" * 60)
        click.echo("BULLETIN TEXT")
        click.echo("=" * 60)
        print(bulletin_text)


@cli.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging (debug mode)"
)
def check(verbose):
    """Check configuration and dependencies."""
    setup_logging(verbose=verbose)

    click.echo("Checking WSWS Bulletin configuration...\n")

    # Load config
    config = Config()

    click.echo("Configuration:")
    click.echo(f"  AI Provider: {config.ai_provider}")
    click.echo(f"  TTS Engine: {config.tts_engine}")
    click.echo(f"  Output Dir: {config.output_dir}")
    click.echo()

    # Check API keys
    click.echo("API Keys:")
    click.echo(f"  OpenAI: {'✓ Set' if config.openai_api_key else '✗ Not set'}")
    click.echo(f"  Anthropic: {'✓ Set' if config.anthropic_api_key else '✗ Not set'}")
    click.echo()

    # Validate
    errors = config.validate()
    if errors:
        click.echo("Validation Errors:", err=True)
        for error in errors:
            click.echo(f"  ✗ {error}", err=True)
        click.echo()
        sys.exit(1)
    else:
        click.echo("✓ Configuration is valid")
        click.echo()

    # Check TTS engines
    click.echo("Available TTS Engines:")
    engines = get_available_engines()
    for engine in ["coqui", "openai"]:
        if engine in engines:
            click.echo(f"  ✓ {engine}")
        else:
            click.echo(f"  ✗ {engine} (not available)")
    click.echo()

    # Check AI models
    click.echo("AI Models:")
    if config.ai_provider == "anthropic":
        click.echo(f"  Configured: {config.anthropic_model}")
        if config.anthropic_api_key:
            try:
                from anthropic import Anthropic
                client = Anthropic(api_key=config.anthropic_api_key)
                model_info = client.models.get(config.anthropic_model)
                click.echo(f"  ✓ Model exists: {model_info.display_name}")
            except Exception as e:
                click.echo(f"  ⚠ Could not verify model: {e}", err=True)
    elif config.ai_provider == "openai":
        click.echo(f"  Configured: {config.openai_model}")
        # OpenAI doesn't have a model listing API in the same way
        click.echo(f"  ℹ Model validation not implemented for OpenAI")
    click.echo()

    click.echo("✓ All checks passed!")


@cli.command()
@click.option(
    "--provider",
    type=click.Choice(["anthropic", "openai"], case_sensitive=False),
    help="AI provider to list models for (default: from config)"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed model information"
)
def list_models(provider, verbose):
    """List available AI models for the configured provider."""
    config = Config()

    # Use provider from config if not specified
    provider = (provider or config.ai_provider).lower()

    if provider == "anthropic":
        if not config.anthropic_api_key:
            click.echo("Error: ANTHROPIC_API_KEY not set", err=True)
            sys.exit(1)

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=config.anthropic_api_key)

            click.echo("Fetching available Anthropic models...\n")
            models = client.models.list()

            click.echo(f"Available Models ({len(models.data)} total):")
            click.echo("-" * 80)

            for model in models.data:
                click.echo(f"ID: {model.id}")
                click.echo(f"  Display Name: {model.display_name}")
                click.echo(f"  Created: {model.created_at}")
                if verbose:
                    click.echo(f"  Type: {model.type}")
                click.echo()

            # Highlight current configured model
            current = config.anthropic_model
            click.echo("-" * 80)
            click.echo(f"Currently configured: {current}")

            # Check if configured model exists
            model_ids = [m.id for m in models.data]
            if current in model_ids:
                click.echo("✓ Configured model is valid")
            else:
                click.echo("⚠ Warning: Configured model not found in available models", err=True)
                click.echo("  You may need to update ANTHROPIC_MODEL in your .env file", err=True)

        except Exception as e:
            click.echo(f"Error fetching models: {e}", err=True)
            sys.exit(1)

    elif provider == "openai":
        click.echo("OpenAI model listing not yet implemented.")
        click.echo("Common models: gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo")
        click.echo(f"\nCurrently configured: {config.openai_model}")
    else:
        click.echo(f"Unknown provider: {provider}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--hours",
    default=24,
    type=int,
    help="Number of hours to look back (default: 24)"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging (debug mode)"
)
def list_articles(hours, verbose):
    """List recent articles without generating a bulletin."""
    setup_logging(verbose=verbose)

    click.echo(f"Fetching articles from the last {hours} hours...\n")

    # Load config for cache settings
    config = Config()
    scraper = WWSSScraper(
        cache_enabled=config.cache_enabled,
        cache_expire_minutes=config.cache_expire_minutes
    )

    # Get perspective
    click.echo("Latest Perspective:")
    click.echo("-" * 60)
    perspective = scraper.get_latest_perspective()
    if perspective:
        click.echo(f"Title: {perspective['title']}")
        click.echo(f"Date: {perspective['date']}")
        click.echo(f"URL: {perspective['url']}")
    else:
        click.echo("No perspective found")
    click.echo()

    # Get recent articles
    click.echo(f"Recent Articles ({hours}h):")
    click.echo("-" * 60)
    articles = scraper.get_recent_articles(hours=hours)

    if articles:
        for i, article in enumerate(articles, 1):
            click.echo(f"{i}. {article['title']}")
            click.echo(f"   {article['date']} - {article['url']}")
            click.echo()
    else:
        click.echo("No recent articles found")

    click.echo(f"Total: {len(articles)} articles")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
