"""
Dictionary parser for CC-CEDICT format
Parses the cedict_ts.u8 file and provides lookup functionality
"""

import re
from typing import Dict, List, Optional, Tuple
from huggingface_hub import InferenceClient
import os
import boto3


def get_huggingface_token():
    LOCAL_ENV_VAR_NAME = "HF_INFERENCE_TOKEN"
    SSM_PARAMETER_NAME = "/chinese-reader/HF_INFERENCE_TOKEN"

    local_token = os.environ.get(LOCAL_ENV_VAR_NAME)
    if local_token:
        print("Token retrieved from local environment variable.")
        return local_token

    try:
        ssm = boto3.client("ssm")

        response = ssm.get_parameter(Name=SSM_PARAMETER_NAME, WithDecryption=True)

        ssm_token = response["Parameter"]["Value"]
        print("Token retrieved successfully from SSM.")

        return ssm_token

    except Exception as e:
        print(f"ERROR: Could not retrieve token from SSM: {e}")
        raise RuntimeError(
            "Hugging Face API token not found in local environment or AWS SSM."
        )


client = InferenceClient(
    provider="hf-inference",
    api_key=get_huggingface_token(),
)


class ChineseDictionary:
    """Chinese-English dictionary with pinyin lookup"""

    def __init__(self, dict_file: str = "resources/cedict_ts.u8"):
        """
        Initialize the dictionary by parsing the CC-CEDICT file

        Args:
            dict_file: Path to the CC-CEDICT dictionary file
        """
        self.dict_file = dict_file
        self.entries: Dict[str, List[Dict]] = {}
        self._load_dictionary()
        self.phrases = set[str](self.entries.keys())

    def is_phrase_in_dictionary(self, phrase: str) -> bool:
        """Check if a phrase is in the dictionary"""
        return phrase in self.phrases

    def _load_dictionary(self):
        """Load and parse the dictionary file"""
        print(f"Loading dictionary from {self.dict_file}...")

        try:
            with open(self.dict_file, "r", encoding="utf-8") as f:
                entry_count = 0
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse the line: Traditional Simplified [pinyin] /definition/
                    # Format: 中文 中文 [zhong1 wen2] /Chinese (language)/
                    match = re.match(r"^(.+?)\s+(.+?)\s+\[(.+?)\]\s+/(.+?)/$", line)
                    if match:
                        traditional, simplified, pinyin, definition = match.groups()

                        # Store entry for both traditional and simplified
                        entry = {
                            "text": simplified,  # Use simplified as default
                            "traditional": traditional,
                            "simplified": simplified,
                            "pinyin": self._format_pinyin(pinyin),
                            "pinyin_raw": pinyin,
                            "definition": self._format_definition_pinyin(definition),
                        }

                        # Index by both traditional and simplified
                        if simplified not in self.entries:
                            self.entries[simplified] = []
                        self.entries[simplified].append(entry)

                        if traditional != simplified:
                            if traditional not in self.entries:
                                self.entries[traditional] = []
                            self.entries[traditional].append(entry)

                        entry_count += 1

                print(
                    f"Dictionary loaded: {entry_count} entries, {len(self.entries)} unique phrases"
                )
        except FileNotFoundError:
            print(
                f"Warning: Dictionary file {self.dict_file} not found. Dictionary will be empty."
            )
            self.entries = {}

    def _format_pinyin(self, pinyin_raw: str) -> str:
        """
        Convert pinyin with tone numbers to readable format
        e.g., "zhong1 wen2" -> "zhōng wén"

        Args:
            pinyin_raw: Pinyin string with tone numbers (e.g., "zhong1 wen2")

        Returns:
            Formatted pinyin with tone marks
        """
        # Tone marks mapping
        tone_marks = {
            "a": ["ā", "á", "ǎ", "à", "a"],
            "e": ["ē", "é", "ě", "è", "e"],
            "i": ["ī", "í", "ǐ", "ì", "i"],
            "o": ["ō", "ó", "ǒ", "ò", "o"],
            "u": ["ū", "ú", "ǔ", "ù", "u"],
            "ü": ["ǖ", "ǘ", "ǚ", "ǜ", "ü"],
        }

        def add_tone(syllable: str) -> str:
            """Add tone mark to a single syllable"""
            # Extract tone number
            tone_match = re.search(r"(\d)", syllable)
            if not tone_match:
                return syllable

            tone_num = int(tone_match.group(1)) - 1  # Convert 1-5 to 0-4
            syllable_no_tone = re.sub(r"\d", "", syllable)

            # Find the vowel to add tone mark to
            # Priority: a, e, o, then i/u/ü
            for vowel in ["a", "e", "o", "i", "u", "ü"]:
                if vowel in syllable_no_tone:
                    idx = syllable_no_tone.index(vowel)
                    vowel_char = syllable_no_tone[idx]
                    if vowel_char in tone_marks:
                        new_vowel = tone_marks[vowel_char][tone_num]
                        return (
                            syllable_no_tone[:idx]
                            + new_vowel
                            + syllable_no_tone[idx + 1 :]
                        )

            return syllable_no_tone

        # Split into syllables and process each
        syllables = pinyin_raw.split()
        formatted = [add_tone(syl) for syl in syllables]
        return " ".join(formatted)

    def _format_definition_pinyin(self, definition: str) -> str:
        """
        Convert pinyin in definitions from [pan2] format to accented format
        e.g., "see [pan2]" -> "see pán"

        Args:
            definition: Definition string that may contain pinyin in brackets

        Returns:
            Definition with pinyin converted to accented format
        """
        # Pattern to match pinyin in brackets like [pan2], [zhong1 wen2], etc.
        pinyin_pattern = r"\[([a-züA-ZÜ]+\d+(?:\s+[a-züA-ZÜ]+\d+)*)\]"

        def replace_pinyin(match):
            pinyin_in_brackets = match.group(1)
            formatted = self._format_pinyin(pinyin_in_brackets)
            return formatted

        # Replace all pinyin patterns in the definition
        return re.sub(pinyin_pattern, replace_pinyin, definition)

    def lookup(self, phrase: str) -> Optional[List[Dict]]:
        """
        Look up a Chinese phrase in the dictionary

        Args:
            phrase: Chinese phrase to look up

        Returns:
            List of matching entries, or None if not found
        """
        return self.entries.get(phrase)

    def lookup_best(self, phrase: str) -> Optional[Dict]:
        """
        Look up a phrase and return the first (best) match

        Args:
            phrase: Chinese phrase to look up

        Returns:
            First matching entry, or None if not found
        """
        matches = self.lookup(phrase)
        if matches:
            return matches[0]
        return None

    def entry(self, phrase: str) -> Optional[Dict]:
        matches = self.lookup_best(phrase)
        if matches:
            return matches[0]

        print("DEBUG: client translating", phrase)

        result = client.translation(
            phrase,
            model="Helsinki-NLP/opus-mt-zh-en",
        )

        # TODO: add traditional/simplified conversion
        pinyin = self.get_pinyin(phrase)
        pinyin = pinyin if pinyin is not None else ""
        entry = {
            "text": phrase,
            "traditional": phrase,
            "simplified": phrase,
            "pinyin": self._format_pinyin(pinyin),
            "pinyin_raw": pinyin,
            "definition": result.translation_text,
        }

        return entry

    def get_pinyin(self, phrase: str) -> Optional[str]:
        """Get pinyin for a phrase"""
        if not phrase:
            return ""

        for end_index in range(len(phrase), 0, -1):
            segment = phrase[:end_index]
            entry = self.lookup_best(segment)

            if entry is not None:
                remaining_phrase = phrase[end_index:]

                recursive_pinyin = self.get_pinyin(remaining_phrase)

                if recursive_pinyin is not None:
                    return entry["pinyin"] + " " + recursive_pinyin

        return None  # Return None to indicate failure

    def get_definition(self, phrase: str) -> Optional[str]:
        """Get English definition for a phrase"""
        entry = self.lookup_best(phrase)
        if entry:
            return entry["definition"]
        return None


# Global dictionary instance (lazy loaded)
_dictionary_instance: Optional[ChineseDictionary] = None


def get_dictionary() -> ChineseDictionary:
    """Get or create the global dictionary instance"""
    global _dictionary_instance
    if _dictionary_instance is None:
        _dictionary_instance = ChineseDictionary()
    return _dictionary_instance
