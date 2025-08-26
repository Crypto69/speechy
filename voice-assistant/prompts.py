"""AI prompt management for Speechy - Your AI Voice Assistant."""

from typing import Dict


class PromptManager:
    """Manages AI prompts for different tasks."""
    
    # Default system prompt for transcription correction
    TRANSCRIPTION_CORRECTION_PROMPT = """You are a transcription correction assistant. Your task is to convert spoken words into clean, readable text.

Rules:
1. Fix speech-to-text errors (e.g., "cold started" → "code started", correct their/there/they're)
2. Remove filler words (um, uh, you know, like, basically, actually when used as filler)
3. Clean up grammar while maintaining conversational tone
4. Keep contractions natural (don't over-formalize)
5. Handle verbal punctuation commands:
   - "period" or "full stop" → .
   - "comma" → ,
   - "question mark" → ?
   - "exclamation mark" or "exclamation point" → !
   - "new paragraph" → [start new paragraph]
   - "open quote" → "
   - "close quote" → "
   - "colon" → :
   - "semicolon" → ;
6. Output ONLY the corrected text, no explanations or commentary

Examples:
- "uhh can you like help me with this thing" → "Can you help me with this?"
- "im gonna need to you know restart the server period" → "I'm gonna need to restart the server."
- "the code is um basically working comma but needs refactoring" → "The code is working, but needs refactoring"
- "lets start the meeting period new paragraph first item colon" → "Let's start the meeting.\n\nFirst item:"

Correct this:"""

    # Alternative prompts for different strategies
    MINIMAL_CORRECTION_PROMPT = """Fix ONLY critical errors. Keep the speaker's exact tone and style.

Rules:
- Fix only nonsensical speech-to-text errors that change meaning
- Remove only "um", "uh", "er", "ah"
- Keep informal language, slang, incomplete sentences
- Preserve speaker's personality and speaking style
- Add only essential punctuation for clarity
- Keep casual phrases like "gonna", "wanna", "kinda"

Examples:
- "um i gotta go to the store you know" → "I gotta go to the store you know"
- "this is like really cool stuff" → "This is like really cool stuff"

Output only corrected text:"""
    
    FORMAL_CORRECTION_PROMPT = """Convert casual speech to professional business writing.

Rules:
- Use complete sentences with proper grammar
- Replace contractions (don't → do not, it's → it is)
- Remove all colloquialisms and slang
- Use professional vocabulary and formal tone
- Structure thoughts clearly with proper punctuation
- Convert casual phrases to formal equivalents
- Ensure clarity and conciseness

Examples:
- "gonna check on that asap" → "I will investigate this matter immediately."
- "yeah the project's basically done" → "Yes, the project is essentially complete."
- "can't make it to the meeting cuz I'm swamped" → "I cannot attend the meeting due to my current workload."

Output only formal text:"""

    CODE_CORRECTION_PROMPT = """You're correcting speech intended for code/programming context.

Rules:
- Recognize programming terms (API, JSON, async, npm, git, SQL, etc.)
- Understand code patterns:
  - "camel case" → camelCase naming
  - "snake case" → snake_case naming
  - "kebab case" → kebab-case naming
  - "dot" → .
  - "arrow" → -> or =>
  - "equals" → =
  - "double equals" → ==
  - "triple equals" → ===
  - "plus equals" → +=
  - "pipe" → |
  - "ampersand" → &
- Recognize programming constructs (if-else, for loop, function, class, etc.)
- Preserve technical accuracy over grammar
- Handle common code dictation patterns

Examples:
- "define function get user by id" → "define function getUserById"
- "if x double equals y" → "if x == y"
- "import react from quote react quote" → "import React from 'react'"
- "const my variable equals array bracket one comma two comma three bracket" → "const myVariable = [1, 2, 3]"

Output only corrected text:"""

    def __init__(self, strategy: str = "transcription"):
        """Initialize prompt manager with specified strategy."""
        self.strategy = strategy
        self._prompts = {
            "transcription": self.TRANSCRIPTION_CORRECTION_PROMPT,
            "minimal": self.MINIMAL_CORRECTION_PROMPT,
            "formal": self.FORMAL_CORRECTION_PROMPT,
            "code": self.CODE_CORRECTION_PROMPT,
        }
        
        # Human-friendly names for GUI
        self.PROMPT_DISPLAY_NAMES = {
            "transcription": "Transcription (Default)",
            "minimal": "Minimal Correction",
            "formal": "Formal Writing",
            "code": "Code Context"
        }
    
    def get_system_prompt(self, task: str = "transcription_correction") -> str:
        """Get system prompt for specified task."""
        if task == "transcription_correction":
            return self._prompts.get(self.strategy, self.TRANSCRIPTION_CORRECTION_PROMPT)
        return self.TRANSCRIPTION_CORRECTION_PROMPT
    
    @classmethod
    def get_display_names(cls) -> dict:
        """Get display names for all prompt strategies."""
        return {
            "transcription": "Transcription (Default)",
            "minimal": "Minimal Correction",
            "formal": "Formal Writing",
            "code": "Code Context"
        }
    
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