"""AI prompt management for Speechy - Your AI Voice Assistant."""

from typing import Dict, Optional


class PromptManager:
    """Manages AI prompts for different tasks."""
    
    # Default system prompt for transcription correction
    TRANSCRIPTION_CORRECTION_PROMPT = """You are a transcription correction assistant. Your job is to:
1. Fix any obvious speech-to-text errors (like "cold started" instead of "called started")
2. Remove filler words (um, uh, you know, like, etc.)
3. Clean up grammar and make the text more readable
4. Understand and preserve the original intent and meaning
5. Return ONLY the corrected text, nothing else
6. Your output should be a clean, corrected version of the input text without any additional commentary or explanations.
7. Add punctuation where are use specifies it, but do not add any additional punctuation. For example:
- if the user says "Full stop" or "period" then you should add a full stop at that point.
- if the user says "comma" then you should add a comma at that point.
- if the user says "question mark" then you should add a question mark at that point.

Examples:
- "I called started the server" → "I cold started the server"
- "I would like to um, start you know the server" → "I would like to start the server"
- "Can you uh, help me with this thing" → "Can you help me with this"
- "I think we should comma like, go now full stop" → "I think we should, go now."

Fix this transcription:"""

    # Alternative prompts for different strategies
    MINIMAL_CORRECTION_PROMPT = """Fix only obvious errors and remove filler words. Preserve original style:"""
    
    FORMAL_CORRECTION_PROMPT = """Convert to formal business writing while preserving meaning:"""
    
    def __init__(self, strategy: str = "default"):
        """Initialize prompt manager with specified strategy."""
        self.strategy = strategy
        self._prompts = {
            "default": self.TRANSCRIPTION_CORRECTION_PROMPT,
            "minimal": self.MINIMAL_CORRECTION_PROMPT,
            "formal": self.FORMAL_CORRECTION_PROMPT,
        }
    
    def get_system_prompt(self, task: str = "transcription_correction") -> str:
        """Get system prompt for specified task."""
        if task == "transcription_correction":
            return self._prompts.get(self.strategy, self.TRANSCRIPTION_CORRECTION_PROMPT)
        return self.TRANSCRIPTION_CORRECTION_PROMPT
    
    def set_strategy(self, strategy: str) -> None:
        """Set the prompt strategy."""
        if strategy in self._prompts:
            self.strategy = strategy
        else:
            raise ValueError(f"Unknown strategy: {strategy}. Available: {list(self._prompts.keys())}")
    
    def add_custom_prompt(self, name: str, prompt: str) -> None:
        """Add a custom prompt strategy."""
        self._prompts[name] = prompt
    
    def get_available_strategies(self) -> list:
        """Get list of available prompt strategies."""
        return list(self._prompts.keys())