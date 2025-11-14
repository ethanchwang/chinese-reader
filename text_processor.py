import hanlp
import unicodedata
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from resources.utils import get_hsk_level
from resources.dictionary import cedict_lookup, get_pinyin, hf_translate
from concurrent.futures import ThreadPoolExecutor, Future


tok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH, devices=["cpu"])
executor = ThreadPoolExecutor(max_workers=3)


@dataclass
class Phrase:
    """Represents a processed Chinese phrase with pinyin, definition, and metadata."""

    text: str
    pinyin: str = ""
    definition: str = ""
    hsk_level: str = "N/A"
    all_entries: List[Dict[str, Any]] = field(default_factory=list)
    traditional: Optional[str] = None
    simplified: Optional[str] = None
    pinyin_raw: Optional[str] = None
    is_sentence_end: bool = False

    def __post_init__(self):
        """Set traditional/simplified to text if not provided."""
        # if self.traditional is None:
        #     self.traditional = self.text
        # if self.simplified is None:
        #     self.simplified = self.text
        self.populate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert Phrase instance to dictionary for JSON serialization."""
        result = {
            "text": self.text,
            "pinyin": self.pinyin,
            "definition": self.definition,
            "hsk_level": self.hsk_level,
            "all_entries": self.all_entries,
            # "traditional": self.traditional,
            # "simplified": self.simplified,
            # "pinyin_raw": self.pinyin_raw,
        }

        if self.is_sentence_end:
            result["is_sentence_end"] = True

        return result

    def populate(self):
        if self.is_sentence_end:
            self.definition = executor.submit(hf_translate, self.text)
            return

        if not all(is_chinese_ideograph(w) for w in self.text):
            return

        entries = cedict_lookup(self.text)

        if entries:
            all_pinyin = []
            all_definitions = []
            for entry in entries:
                if entry["pinyin"] and entry["pinyin"] not in all_pinyin:
                    all_pinyin.append(entry["pinyin"])
                if entry["definition"] and entry["definition"] not in all_definitions:
                    all_definitions.append(entry["definition"])
            self.pinyin = (" / ".join(all_pinyin) if all_pinyin else "[Not found]",)
            self.definition = (
                " | ".join(all_definitions) if all_definitions else "[Not found]",
            )
        else:
            self.pinyin = get_pinyin(self.text)
            self.definition = executor.submit(hf_translate, self.text)

        self.all_entries = entries
        self.hsk_level = get_hsk_level(self.text)

    def resolve_translation(self):
        if isinstance(self.definition, Future):
            self.definition = self.definition.result()


def is_chinese_ideograph(char):
    """
    Checks if a character is classified as a CJK Ideograph ('Lo').
    This excludes all standard punctuation, spaces, and numbers.
    """
    return unicodedata.category(char) == "Lo"


def segment_chinese_text(text):
    """
    Segment Chinese text into phrases.

    Returns:
        List[str]
    """
    return tok(text)


def process_chinese_text(text):
    """
    Process Chinese text and return phrases with pinyin and definitions.

    Args:
        text (str): The Chinese text to process
        dictionary: ChineseDictionary instance for lookups

    Returns:
        dict: Dictionary containing 'phrases' list and 'original_text'
              Each phrase has 'text', 'pinyin', and 'definition' keys
    """
    if not text:
        return {"phrases": [], "original_text": text}

    processed_phrases: List[Phrase] = []

    phrases = segment_chinese_text(text)

    # Track sentence phrases
    sentence_phrases = []

    for i, phrase_text in enumerate(phrases):
        phrase = Phrase(text=phrase_text)

        if phrase_text == "。":
            # This period ends a sentence
            # Join all phrases from sentence start to current (excluding the period)
            sentence_text = "".join(p.text for p in sentence_phrases)
            full_sentence = sentence_text.strip()
            if full_sentence:
                phrase = Phrase(text=full_sentence, is_sentence_end=True)
            # Reset for next sentence
            sentence_phrases = []
        else:
            # Add this phrase to the current sentence
            sentence_phrases.append(phrase)

        processed_phrases.append(phrase)

    for phrase in processed_phrases:
        phrase.resolve_translation()

    # Convert Phrase objects to dictionaries for JSON serialization
    phrases_dict = [phrase.to_dict() for phrase in processed_phrases]

    return {"phrases": phrases_dict, "original_text": text}
