import hanlp
import unicodedata


tok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH, devices=["cpu"])


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


def process_chinese_text(text, dictionary):
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

    processed_phrases = []

    phrases = segment_chinese_text(text)
    print(phrases)

    for phrase in phrases:
        if not all(is_chinese_ideograph(w) for w in phrase):
            processed_phrases.append({"text": phrase, "pinyin": "", "definition": ""})
            continue

        entries = dictionary.lookup(phrase)

        if not entries:
            entry = dictionary.entry(phrase)
            processed_phrases.append(entry)
            continue

        all_pinyin = []
        all_definitions = []
        for entry in entries:
            if entry["pinyin"] and entry["pinyin"] not in all_pinyin:
                all_pinyin.append(entry["pinyin"])
            if entry["definition"] and entry["definition"] not in all_definitions:
                all_definitions.append(entry["definition"])

        processed_phrases.append(
            {
                "text": phrase,
                "pinyin": " / ".join(all_pinyin) if all_pinyin else "[Not found]",
                "definition": " | ".join(all_definitions)
                if all_definitions
                else "[Not found]",
                "all_entries": entries,  # Store all entries for detailed view
            }
        )

    return {"phrases": processed_phrases, "original_text": text}
