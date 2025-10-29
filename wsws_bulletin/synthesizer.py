"""AI-powered synthesis and summarization of WSWS articles."""

import logging
from typing import Dict, List, Optional
import os

from anthropic import Anthropic
from openai import OpenAI

logger = logging.getLogger(__name__)


class ArticleSynthesizer:
    """Synthesize and summarize WSWS articles using AI."""

    SYSTEM_PROMPT = """You are an expert analyst of socialist and Trotskyist political analysis,
with deep knowledge of Marxist theory, historical materialism, and the Fourth International's
political perspective. Your task is to synthesize multiple articles from the World Socialist
Web Site (WSWS) into a comprehensive daily bulletin for advanced readers.

Focus on:
1. The most important political developments and their class character
2. Theoretical and historical lessons that emerge from current events
3. Connections between different struggles and events globally
4. The strategic implications for the international working class
5. Historical parallels and the development of contradictions in capitalism

Your analysis should be sophisticated, assuming the reader is familiar with Marxist concepts
and the political perspective of the International Committee of the Fourth International (ICFI)."""

    def __init__(self, provider: str = "anthropic", api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the synthesizer.

        Args:
            provider: AI provider ("openai" or "anthropic")
            api_key: API key for the chosen provider
            model: Model name (optional, uses default for provider if not specified)
        """
        self.provider = provider.lower()

        if self.provider == "anthropic":
            self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
            self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
        elif self.provider == "openai":
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _format_articles_for_prompt(self, content: Dict[str, any]) -> str:
        """Format article content into a prompt string.

        Args:
            content: Dictionary with 'articles' and 'perspective' keys

        Returns:
            Formatted string for the AI prompt
        """
        parts = []

        # Add perspective first (most important)
        if content.get('perspective'):
            p = content['perspective']
            parts.append(f"=== PERSPECTIVE (FEATURED ANALYSIS) ===\n")
            parts.append(f"Title: {p['title']}\n")
            parts.append(f"Author: {p['author']}\n")
            parts.append(f"Date: {p['date']}\n")
            parts.append(f"URL: {p['url']}\n\n")
            parts.append(f"{p['text']}\n\n")

        # Add recent articles
        if content.get('articles'):
            parts.append(f"=== RECENT ARTICLES ({len(content['articles'])} articles) ===\n\n")
            for i, article in enumerate(content['articles'], 1):
                parts.append(f"--- Article {i} ---\n")
                parts.append(f"Title: {article['title']}\n")
                parts.append(f"Author: {article['author']}\n")
                parts.append(f"Date: {article['date']}\n")
                parts.append(f"URL: {article['url']}\n\n")
                parts.append(f"{article['text']}\n\n")

        return "".join(parts)

    def synthesize(self, content: Dict[str, any]) -> str:
        """Synthesize and summarize the article content.

        Args:
            content: Dictionary with 'articles' and 'perspective' keys

        Returns:
            Synthesized summary text
        """
        articles_text = self._format_articles_for_prompt(content)

        user_prompt = f"""Please analyze and synthesize the following WSWS articles into a
comprehensive daily bulletin. Structure your analysis as follows:

1. **Executive Summary**: A brief overview of the most critical developments (2-3 paragraphs)

2. **Major Political Developments**: Detailed analysis of the most important events, organized
   by region or theme, with focus on:
   - The class forces involved
   - The political trajectory and implications
   - Connection to broader historical processes

3. **Theoretical and Historical Insights**: Draw out the key theoretical lessons, including:
   - Historical parallels and precedents
   - Development of class contradictions
   - Strategic questions for the working class
   - Significance for socialist perspective

4. **International Connections**: How different events and struggles relate to each other
   as part of global class struggle

5. **Key Takeaways**: 3-5 essential points for revolutionary socialists to understand

Here are the articles:

{articles_text}"""

        logger.info("Generating synthesis using AI...")

        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            synthesis = response.content[0].text

        else:  # openai
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4096
            )
            synthesis = response.choices[0].message.content

        logger.info("Synthesis complete!")
        return synthesis

    def generate_bulletin(self, content: Dict[str, any], title: Optional[str] = None) -> str:
        """Generate a complete bulletin with header and synthesis.

        Args:
            content: Dictionary with 'articles' and 'perspective' keys
            title: Optional custom title

        Returns:
            Complete bulletin text with formatting
        """
        from datetime import datetime

        if title is None:
            title = f"WSWS Daily Bulletin - {datetime.now().strftime('%B %d, %Y')}"

        synthesis = self.synthesize(content)

        # Format the complete bulletin
        bulletin_parts = [
            "=" * 80,
            title.center(80),
            "=" * 80,
            "",
            synthesis,
            "",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Source Articles:",
        ]

        # Add article links
        if content.get('perspective'):
            bulletin_parts.append(f"  • [PERSPECTIVE] {content['perspective']['title']}")
            bulletin_parts.append(f"    {content['perspective']['url']}")

        for article in content.get('articles', []):
            bulletin_parts.append(f"  • {article['title']}")
            bulletin_parts.append(f"    {article['url']}")

        bulletin_parts.append("=" * 80)

        return "\n".join(bulletin_parts)
