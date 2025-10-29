# Quick Installation Guide

## Step 1: Install the package

```bash
# Install in editable mode with all dependencies
pip install -e .
```

## Step 2: Configure API keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your preferred editor
```

Add either:
- `ANTHROPIC_API_KEY=sk-ant-...` for Claude (recommended)
- `OPENAI_API_KEY=sk-...` for GPT-4

## Step 3: Test your setup

```bash
# Check configuration
wsws-bulletin check

# List recent articles (doesn't require API key)
wsws-bulletin list-articles
```

## Step 4: Generate your first bulletin

```bash
# Generate bulletin (text + audio)
wsws-bulletin generate

# Or generate text only (faster, no TTS model download)
wsws-bulletin generate --no-audio
```

Output will be saved in `./output/` directory.

## Troubleshooting

### Missing dependencies

If you get import errors, install dependencies manually:

```bash
pip install requests beautifulsoup4 lxml click python-dotenv anthropic
```

### TTS model download

On first run with audio, Coqui TTS will download ~100MB model. This is normal and only happens once.

To skip audio generation:
```bash
wsws-bulletin generate --no-audio
```

### API key errors

Make sure your `.env` file is in the current directory or home directory (`~/.wsws-bulletin.env`).

Check with:
```bash
wsws-bulletin check
```
