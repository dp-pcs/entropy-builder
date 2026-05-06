#!/usr/bin/env python3
"""
LLM-powered analysis for inbox items

Supports Anthropic Claude and OpenAI GPT models for semantic understanding
"""
import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class LLMAnalysis:
    """Result of LLM analysis on an inbox item"""
    main_topics: List[str]
    key_insight: str
    suggested_mocs: List[str]
    suggested_frameworks: List[str]
    confidence: float
    new_moc_suggestion: Optional[str]
    reasoning: str


class LLMAnalyzer:
    """Analyzes content using LLM APIs"""

    def __init__(self, provider: str = "anthropic", api_key: str = None, model: str = None):
        """
        Initialize LLM analyzer

        Args:
            provider: "anthropic" or "openai"
            api_key: API key for the provider
            model: Optional model override
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.environ.get(
            "ANTHROPIC_API_KEY" if self.provider == "anthropic" else "OPENAI_API_KEY"
        )

        if not self.api_key:
            raise ValueError(f"No API key provided for {provider}")

        # Set default models
        if model:
            self.model = model
        elif self.provider == "anthropic":
            self.model = "claude-3-5-sonnet-20241022"
        else:
            self.model = "gpt-4o"  # or gpt-4o-mini for cheaper

        self._client = None

    def _get_client(self):
        """Lazy-load API client"""
        if self._client:
            return self._client

        if self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")

        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        return self._client

    def analyze_item(
        self,
        content: str,
        existing_mocs: List[str],
        existing_frameworks: List[str]
    ) -> LLMAnalysis:
        """Analyze an inbox item using LLM

        Args:
            content: Full markdown content of the item
            existing_mocs: List of existing MOC names
            existing_frameworks: List of existing framework names

        Returns:
            LLMAnalysis with topics, insights, and suggestions
        """
        # Truncate content if too long (keep first 4000 chars)
        truncated_content = content[:4000] if len(content) > 4000 else content

        prompt = f"""Analyze this article/note for integration into a personal knowledge base.

CONTENT:
{truncated_content}

EXISTING STRUCTURE:
- MOCs (navigation hubs): {', '.join(existing_mocs[:20]) if existing_mocs else 'None'}
- Frameworks (methodologies): {', '.join(existing_frameworks[:20]) if existing_frameworks else 'None'}

Analyze and return ONLY valid JSON (no markdown, no explanation):

{{
  "main_topics": ["topic1", "topic2", "topic3"],
  "key_insight": "One sentence capturing the main point",
  "suggested_mocs": ["ExistingMOC1", "ExistingMOC2"],
  "suggested_frameworks": ["ExistingFramework1"],
  "confidence": 0.85,
  "new_moc_suggestion": "Suggested New MOC Name" or null,
  "reasoning": "Brief explanation of relationships"
}}

Rules:
- main_topics: Extract 2-4 key topics/keywords
- key_insight: One clear sentence, not just summary
- suggested_mocs/frameworks: ONLY suggest if content clearly relates (>70% confidence)
- confidence: 0.0-1.0 score for relationship strength
- new_moc_suggestion: Suggest NEW MOC only if content doesn't fit existing ones
- Return ONLY the JSON object, nothing else
"""

        try:
            response = self._call_llm(prompt)
            return self._parse_response(response)
        except Exception as e:
            print(f"  ⚠️  LLM analysis failed: {e}")
            # Return empty analysis on failure
            return LLMAnalysis(
                main_topics=[],
                key_insight="",
                suggested_mocs=[],
                suggested_frameworks=[],
                confidence=0.0,
                new_moc_suggestion=None,
                reasoning=f"Error: {str(e)}"
            )

    def _call_llm(self, prompt: str) -> str:
        """Call the appropriate LLM API"""
        client = self._get_client()

        if self.provider == "anthropic":
            message = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return message.content[0].text

        else:  # openai
            response = client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=1024,
                temperature=0.3
            )
            return response.choices[0].message.content

    def _parse_response(self, response: str) -> LLMAnalysis:
        """Parse LLM response into LLMAnalysis"""
        # Strip markdown code blocks if present
        response = response.strip()
        if response.startswith("```"):
            # Remove ```json and ``` markers
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]

        data = json.loads(response.strip())

        return LLMAnalysis(
            main_topics=data.get("main_topics", []),
            key_insight=data.get("key_insight", ""),
            suggested_mocs=data.get("suggested_mocs", []),
            suggested_frameworks=data.get("suggested_frameworks", []),
            confidence=float(data.get("confidence", 0.0)),
            new_moc_suggestion=data.get("new_moc_suggestion"),
            reasoning=data.get("reasoning", "")
        )


def test_llm_connection(provider: str, api_key: str, model: str = None) -> Dict:
    """Test LLM connection and return status

    Returns:
        {
            "success": True/False,
            "message": "Connection successful" or error message,
            "model": model name used
        }
    """
    try:
        analyzer = LLMAnalyzer(provider=provider, api_key=api_key, model=model)

        # Simple test prompt
        test_content = "# Test Article\n\nThis is a test article about AI agents and federation."
        result = analyzer.analyze_item(
            content=test_content,
            existing_mocs=["AI-MOC"],
            existing_frameworks=["Agentic-Framework"]
        )

        return {
            "success": True,
            "message": f"Connection successful! Model: {analyzer.model}",
            "model": analyzer.model,
            "sample_analysis": {
                "topics": result.main_topics,
                "confidence": result.confidence
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "model": model or "unknown"
        }


if __name__ == "__main__":
    # Test script
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 llm_analyzer.py <provider> <api_key>")
        print("Example: python3 llm_analyzer.py anthropic sk-...")
        sys.exit(1)

    provider = sys.argv[1]
    api_key = sys.argv[2]

    print(f"Testing {provider} connection...")
    result = test_llm_connection(provider, api_key)

    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"\nSample analysis:")
        print(f"  Topics: {result['sample_analysis']['topics']}")
        print(f"  Confidence: {result['sample_analysis']['confidence']}")
    else:
        print(f"❌ {result['message']}")
        sys.exit(1)
