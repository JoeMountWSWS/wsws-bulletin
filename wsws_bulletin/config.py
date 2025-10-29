"""Configuration management for WSWS Bulletin."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Config:
    """Configuration for WSWS Bulletin."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration.

        Args:
            env_file: Path to .env file (default: .env in current directory)
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from common locations
            for location in ['.env', Path.home() / '.wsws-bulletin.env']:
                if Path(location).exists():
                    load_dotenv(location)
                    break

    @property
    def ai_provider(self) -> str:
        """Get AI provider (openai or anthropic)."""
        return os.getenv("AI_PROVIDER", "anthropic").lower()

    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        return os.getenv("OPENAI_API_KEY")

    @property
    def anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic API key."""
        return os.getenv("ANTHROPIC_API_KEY")

    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return os.getenv("OUTPUT_DIR", "./output")

    @property
    def tts_engine(self) -> str:
        """Get TTS engine (coqui or openai)."""
        return os.getenv("TTS_ENGINE", "coqui").lower()

    @property
    def cache_enabled(self) -> bool:
        """Get whether HTTP caching is enabled."""
        return os.getenv("CACHE_ENABLED", "true").lower() in ("true", "1", "yes")

    @property
    def cache_expire_minutes(self) -> int:
        """Get cache expiration time in minutes."""
        try:
            return int(os.getenv("CACHE_EXPIRE_MINUTES", "30"))
        except ValueError:
            return 30

    @property
    def anthropic_model(self) -> str:
        """Get Anthropic model name."""
        return os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    @property
    def openai_model(self) -> str:
        """Get OpenAI model name."""
        return os.getenv("OPENAI_MODEL", "gpt-4o")

    def get_api_key(self) -> Optional[str]:
        """Get API key for the configured AI provider."""
        if self.ai_provider == "openai":
            return self.openai_api_key
        elif self.ai_provider == "anthropic":
            return self.anthropic_api_key
        return None

    def validate(self) -> list:
        """Validate configuration.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check AI provider and key
        if self.ai_provider not in ["openai", "anthropic"]:
            errors.append(f"Invalid AI_PROVIDER: {self.ai_provider}")

        api_key = self.get_api_key()
        if not api_key:
            errors.append(
                f"Missing API key for provider '{self.ai_provider}'. "
                f"Set {self.ai_provider.upper()}_API_KEY in .env file"
            )

        # Check TTS engine
        if self.tts_engine not in ["coqui", "openai"]:
            errors.append(f"Invalid TTS_ENGINE: {self.tts_engine}")

        if self.tts_engine == "openai" and not self.openai_api_key:
            errors.append("TTS_ENGINE is 'openai' but OPENAI_API_KEY is not set")

        return errors
