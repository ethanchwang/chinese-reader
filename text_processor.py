"""
Chinese text processing module
Handles text segmentation, pinyin conversion, and definition lookup.
"""

import re


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
        return {
            'phrases': [],
            'original_text': text
        }

    
    phrases = []
    i = 0
    
    # Process text character by character, preserving punctuation
    while i < len(text):
        # Check if current character is Chinese
        if '\u4e00' <= text[i] <= '\u9fff':
            # Found Chinese character, try to match longest phrase
            chinese_start = i
            chinese_end = i + 1
            
            # Find the end of the Chinese character sequence
            while chinese_end < len(text) and '\u4e00' <= text[chinese_end] <= '\u9fff':
                chinese_end += 1
            
            # Now we have a Chinese phrase, try to match it
            chinese_phrase = text[chinese_start:chinese_end]
            to_lookup = chinese_phrase
            current_phrase = to_lookup
            
            # Try to match longest phrase from dictionary
            while len(to_lookup) > 0:
                current_phrase = to_lookup
                # Find longest matching phrase
                while len(current_phrase) > 0 and not dictionary.is_phrase_in_dictionary(current_phrase):
                    current_phrase = current_phrase[:-1]
                
                # Try to find the phrase in dictionary
                if len(current_phrase) > 0:
                    entries = dictionary.lookup(current_phrase)
                    
                    if entries:
                        # Get all entries (multiple pronunciations)
                        all_pinyin = []
                        all_definitions = []
                        for entry in entries:
                            if entry['pinyin'] and entry['pinyin'] not in all_pinyin:
                                all_pinyin.append(entry['pinyin'])
                            if entry['definition'] and entry['definition'] not in all_definitions:
                                all_definitions.append(entry['definition'])
                        
                        phrases.append({
                            'text': current_phrase,
                            'pinyin': ' / '.join(all_pinyin) if all_pinyin else '[Not found]',
                            'definition': ' | '.join(all_definitions) if all_definitions else '[Not found]',
                            'all_entries': entries  # Store all entries for detailed view
                        })
                    else:
                        # Character(s) not found, add without pinyin/definition
                        phrases.append({
                            'text': current_phrase,
                            'pinyin': '[Not found]',
                            'definition': '[Not found]',
                            'all_entries': []
                        })
                    
                    # Move to next part of phrase
                    to_lookup = to_lookup[len(current_phrase):]
                else:
                    # No match found, add single character and continue
                    phrases.append({
                        'text': to_lookup[0],
                        'pinyin': '[Not found]',
                        'definition': '[Not found]',
                        'all_entries': []
                    })
                    to_lookup = to_lookup[1:]
            
            i = chinese_end
        else:
            # Non-Chinese character (punctuation, space, etc.) - add as-is
            phrases.append({
                'text': text[i],
                'pinyin': '',
                'definition': ''
            })
            i += 1
        
    return {
        'phrases': phrases,
        'original_text': text
    }
