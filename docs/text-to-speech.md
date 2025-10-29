# Text to speech

## Alternative libraries

The best choice depends on your specific needs, but here are the most popular open source text-to-speech libraries:

- **gTTS (Google Text-to-Speech)** is probably the easiest to get started with. It's a simple wrapper around Google's text-to-speech API, so the quality is good and it supports many languages. Installation is straightforward (`pip install gtts`), and basic usage is just a few lines of code. The downside is it requires an internet connection.
- **pyttsx3** is a good choice if you want offline, cross-platform synthesis. It works on Windows, Mac, and Linux, and uses the system's built-in TTS engines (SAPI5 on Windows, NSSpeechSynthesizer on Mac, espeak on Linux). It's lightweight and doesn't require external dependencies beyond the system libraries.
- **Coqui TTS** (based on the open source Coqui project) offers higher-quality synthesis with more natural-sounding voices. It's more computationally intensive but produces better results. It gives you more control over voice characteristics and supports multiple languages and speakers.
- **Festival** and **eSpeak** are older, lighter-weight options that are less polished but very stable and minimal in resource usage. They're often used as backends for other tools.
