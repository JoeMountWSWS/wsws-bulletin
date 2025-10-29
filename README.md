# WSWS Bulletin

An automated daily bulletin generator for the World Socialist Web Site (WSWS). This tool scrapes recent articles and perspectives, synthesizes them using AI, and converts the summary to audio.

## Features

- **Web Scraping**: Automatically fetches recent articles from WSWS archive and the latest perspective
- **AI Synthesis**: Uses Claude (Anthropic) or GPT-4 (OpenAI) to synthesize and summarize articles with focus on:
  - Major political developments and their class character
  - Theoretical and historical lessons from current events
  - Connections between global struggles
  - Strategic implications for the international working class
- **Text-to-Speech**: Converts bulletins to audio using Coqui TTS (local) or OpenAI TTS
- **CLI Interface**: Easy-to-use command-line tool

## Installation

### Prerequisites

- Python 3.9 or higher
- API key for Anthropic or OpenAI

### Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/wsws-bulletin.git
cd wsws-bulletin

# Install in development mode
pip install -e .

# Or install with all dependencies
pip install -e ".[dev]"
```

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   # Choose your AI provider
   AI_PROVIDER=anthropic  # or "openai"
   
   # Add your API key
   ANTHROPIC_API_KEY=your_key_here
   # or
   OPENAI_API_KEY=your_key_here
   
   # Optional: configure TTS engine
   TTS_ENGINE=coqui  # or "openai" for OpenAI TTS
   
   # Optional: set output directory
   OUTPUT_DIR=./output
   ```

## Usage

### Generate a daily bulletin

```bash
# Generate bulletin with default settings (last 24 hours)
wsws-bulletin generate

# Look back 48 hours instead
wsws-bulletin generate --hours 48

# Skip audio generation (text only)
wsws-bulletin generate --no-audio

# Specify output directory
wsws-bulletin generate --output-dir /path/to/output

# Use specific AI provider
wsws-bulletin generate --ai-provider openai

# Use OpenAI TTS instead of local Coqui TTS
wsws-bulletin generate --tts-engine openai
```

### List recent articles

```bash
# List articles from last 24 hours
wsws-bulletin list-articles

# List articles from last 48 hours
wsws-bulletin list-articles --hours 48
```

### Check configuration

```bash
# Verify your configuration and dependencies
wsws-bulletin check
```

## Output

The tool generates two files in the output directory:

1. **Markdown bulletin** (`bulletin_YYYY-MM-DD.md`): Complete synthesized summary with:
   - Executive summary
   - Major political developments
   - Theoretical and historical insights
   - International connections
   - Key takeaways
   - Links to source articles

2. **Audio file** (`bulletin_YYYY-MM-DD.wav` or `.mp3`): Audio version of the bulletin

## Advanced Configuration

### Using OpenAI TTS

OpenAI's TTS produces higher quality audio but requires an OpenAI API key and costs money per generation:

```bash
wsws-bulletin generate --tts-engine openai
```

Or set in `.env`:
```bash
TTS_ENGINE=openai
```

### Using Coqui TTS (Local)

Coqui TTS runs locally and is free, but may be slower on first run (downloads model):

```bash
wsws-bulletin generate --tts-engine coqui
```

### Custom .env location

```bash
wsws-bulletin generate --env-file /path/to/custom/.env
```

## Architecture

The tool consists of four main modules:

1. **`scraper.py`**: Web scraping functionality for WSWS
   - Fetches recent articles from archive
   - Retrieves latest perspective article
   - Extracts full article content

2. **`synthesizer.py`**: AI-powered analysis and synthesis
   - Formats articles for LLM processing
   - Generates comprehensive analysis with Marxist perspective
   - Structures output for advanced readers

3. **`text_to_speech.py`**: Text-to-speech conversion
   - Supports Coqui TTS (local, free)
   - Supports OpenAI TTS (cloud, paid)

4. **`__main__.py`**: Command-line interface
   - User-friendly commands
   - Configuration validation
   - Progress reporting

## Development

### Install development dependencies

```bash
pip install -e ".[dev]"
```

### Code formatting

```bash
black wsws_bulletin/
ruff check wsws_bulletin/
```

### Running tests

```bash
pytest
```

## Troubleshooting

### "No articles found"

This usually means no articles were published in the specified time window. Try increasing `--hours`:
```bash
wsws-bulletin generate --hours 48
```

### TTS model download issues

On first run, Coqui TTS downloads a model (~100MB). If this fails:
1. Check your internet connection
2. Try OpenAI TTS instead: `--tts-engine openai`
3. Manually clear cache: `rm -rf ~/.local/share/tts`

### API key errors

Make sure your API keys are set correctly:
```bash
wsws-bulletin check
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Disclaimer

This tool is an independent project and is not affiliated with or endorsed by the World Socialist Web Site or the International Committee of the Fourth International.
