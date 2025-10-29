# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WSWS Bulletin is an automated daily bulletin generator for the World Socialist Web Site (WSWS). It scrapes recent articles and perspectives, synthesizes them using AI (Claude or GPT-4), and converts the summary to audio using TTS.

## Development Commands

### Installation
```bash
# Install in editable mode with core dependencies
pip install -e .

# Install with development tools (pytest, black, ruff)
pip install -e ".[dev]"

# Install with Coqui TTS support
pip install -e ".[tts-coqui]"
```

### Configuration
```bash
# Setup environment file
cp .env.example .env
# Edit .env to add API keys (ANTHROPIC_API_KEY or OPENAI_API_KEY)
```

### Running the Tool
```bash
# Generate bulletin (default: last 24 hours, with audio)
wsws-bulletin generate

# Common options
wsws-bulletin generate --hours 48          # Look back 48 hours
wsws-bulletin generate --no-audio          # Skip audio generation
wsws-bulletin generate --verbose           # Debug logging
wsws-bulletin generate --print-summary     # Print to stdout after generation

# List articles without generating bulletin
wsws-bulletin list-articles --hours 24

# Check configuration and dependencies
wsws-bulletin check
```

### Code Quality
```bash
# Format code
black wsws_bulletin/

# Lint code
ruff check wsws_bulletin/

# Run tests (when available)
pytest
```

## Architecture

### Core Pipeline Flow
The application follows a three-stage pipeline:

1. **Scrape** (scraper.py) → 2. **Synthesize** (synthesizer.py) → 3. **TTS** (text_to_speech.py)

Orchestrated by the CLI (__main__.py) with configuration managed centrally (config.py).

### Module Responsibilities

**scraper.py (WWSSScraper)**
- Scrapes WSWS archive for recent articles using BeautifulSoup
- Fetches the latest "Perspective" article (featured analysis)
- Extracts full article content (title, text, author, date, URL)
- Key method: `fetch_all_content(hours)` returns dict with 'articles' and 'perspective'
- URLs follow pattern: `/en/articles/YYYY/MM/slug-d##.html` where day is encoded

**synthesizer.py (ArticleSynthesizer)**
- Takes scraped content and generates comprehensive political analysis
- Supports both Anthropic (Claude) and OpenAI (GPT-4) providers
- Uses detailed system prompt emphasizing Marxist/Trotskyist analysis framework
- Key method: `generate_bulletin(content)` returns formatted text with header, synthesis, and source links
- Output structured as: Executive Summary, Major Developments, Theoretical Insights, International Connections, Key Takeaways

**text_to_speech.py (TextToSpeech)**
- Converts bulletin text to audio
- Two engines: Coqui TTS (local, free) and OpenAI TTS (cloud, paid)
- Coqui produces .wav files, OpenAI produces .mp3
- Coqui downloads model on first run (~100MB)
- Key method: `convert_bulletin(text, output_dir)` saves audio file

**config.py (Config)**
- Centralized configuration from environment variables
- Auto-loads .env from current directory or ~/.wsws-bulletin.env
- Manages API keys for both AI providers and both TTS engines
- Validates configuration and returns helpful error messages

**__main__.py**
- Click-based CLI with three commands: generate, list-articles, check
- All commands support --verbose flag for debug logging
- generate command can override config with CLI flags
- Error handling and progress reporting for user feedback

### Key Design Patterns

**Provider Abstraction**: Both synthesizer and TTS abstract away provider differences. Synthesizer handles Anthropic vs OpenAI, TTS handles Coqui vs OpenAI.

**Configuration Hierarchy**: CLI flags override .env file which overrides defaults. This allows flexible configuration without code changes.

**Graceful Degradation**: Text bulletin always saved even if audio generation fails. Perspective is optional (recent articles still work without it).

**Content Structure**: Scraped content passed as dict with 'articles' (list) and 'perspective' (single dict or None) throughout the pipeline.

## Important Implementation Details

### Date Parsing from URLs
WSWS URLs encode dates as: `/en/articles/2025/10/example-d29.html` where the letter after the last dash indicates the day of week and the number is the day of month. The scraper extracts year/month/day to filter articles by time window.

### AI Model Selection
- Anthropic: Uses `claude-3-5-sonnet-20241022` (synthesizer.py:42)
- OpenAI: Uses `gpt-4-turbo-preview` (synthesizer.py:45)

Update these model names when newer versions are available.

### TTS Engine Limitations
- **Coqui TTS**: Requires minimum text length (50+ characters) due to Tacotron2 model kernel size constraints. If text is too short, use OpenAI TTS instead or disable audio generation with `--no-audio`.
- **System dependencies**: Coqui TTS may require system audio libraries for processing.

### Configuration Validation
The Config.validate() method must be called before using API keys. The CLI does this automatically, but any new scripts should call it explicitly.

### Output File Naming
Files are named `bulletin_YYYY-MM-DD.md` (markdown) and `bulletin_YYYY-MM-DD.{wav|mp3}` (audio). If running multiple times per day, files are overwritten.

## Testing the Application

To test changes end-to-end:
```bash
# Quick test without API calls or audio
wsws-bulletin list-articles --hours 24

# Test with API but skip audio (faster)
wsws-bulletin generate --no-audio --hours 24

# Full test
wsws-bulletin generate --hours 24 --verbose
```

## Political Context

This tool is designed for readers familiar with Trotskyist political analysis and the perspective of the International Committee of the Fourth International (ICFI). The AI synthesis emphasizes:
- Class analysis of political developments
- Historical materialism and theoretical lessons
- International working class perspective
- Connections between global struggles

When modifying the synthesis prompt (synthesizer.py), maintain this analytical framework.
