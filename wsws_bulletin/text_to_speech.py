"""Text-to-speech conversion for bulletins."""

import logging
import os
from pathlib import Path
from typing import Optional

try:
    from TTS.api import TTS as CoquiTTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Convert text to speech audio."""

    def __init__(self, engine: str = "coqui", api_key: Optional[str] = None):
        """Initialize TTS engine.

        Args:
            engine: TTS engine to use ("coqui" for local, "openai" for OpenAI TTS)
            api_key: API key for OpenAI (if using openai engine)
        """
        self.engine = engine.lower()

        if self.engine == "coqui":
            if not COQUI_AVAILABLE:
                raise ImportError(
                    "Coqui TTS not installed. Install with: pip install coqui-tts"
                )
            logger.info("Loading Coqui TTS model (this may take a moment)...")
            # Use a high-quality English model
            self.tts = CoquiTTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            logger.info("TTS model loaded!")

        elif self.engine == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "OpenAI library not installed. Install with: pip install openai"
                )
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.voice = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
            logger.info("OpenAI TTS engine initialized")

        else:
            raise ValueError(f"Unsupported TTS engine: {engine}")

    def convert(self, text: str, output_path: str) -> str:
        """Convert text to speech and save to file.

        Args:
            text: Text to convert
            output_path: Path to save the audio file

        Returns:
            Path to the saved audio file
        """
        # Remove whitespace
        # https://github.com/coqui-ai/TTS/issues/2336
        text = str(text).strip()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Converting text to speech using {self.engine} engine...")

        if self.engine == "coqui":
            # Coqui TTS with Tacotron2 requires minimum text length
            # Ensure text is long enough to avoid kernel size errors
            min_chars = 50
            if len(text) < min_chars:
                logger.warning(f"Text too short for TTS ({len(text)} chars). Minimum {min_chars} required.")
                raise ValueError(
                    f"Text must be at least {min_chars} characters long for Coqui TTS. "
                    f"Got {len(text)} characters. Consider using OpenAI TTS instead or adding more content."
                )

            # Coqui TTS saves directly to file
            self.tts.tts_to_file(text=text, file_path=str(output_path))

        elif self.engine == "openai":
            # OpenAI TTS returns audio data that we write to file
            response = self.client.audio.speech.with_streaming_response.create(
                model="tts-1-hd",  # or "tts-1" for faster/cheaper
                voice=self.voice,
                input=text
            )

            # Write the audio data to file
            response.stream_to_file(str(output_path))

        logger.info(f"Audio saved to: {output_path}")
        return str(output_path)

    def convert_bulletin(
        self,
        bulletin_text: str,
        output_dir: str = "./output",
        filename: Optional[str] = None
    ) -> str:
        """Convert a bulletin to speech.

        Args:
            bulletin_text: The bulletin text to convert
            output_dir: Directory to save the audio file
            filename: Optional filename (default: bulletin_YYYY-MM-DD.wav)

        Returns:
            Path to the saved audio file
        """
        from datetime import datetime

        if filename is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            ext = "mp3" if self.engine == "openai" else "wav"
            filename = f"bulletin_{date_str}.{ext}"

        output_path = os.path.join(output_dir, filename)
        return self.convert(bulletin_text, output_path)


def get_available_engines() -> list:
    """Get list of available TTS engines.

    Returns:
        List of available engine names
    """
    engines = []
    if COQUI_AVAILABLE:
        engines.append("coqui")
    if OPENAI_AVAILABLE:
        engines.append("openai")
    return engines
