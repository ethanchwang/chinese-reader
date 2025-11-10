#!/usr/bin/env python3
"""Quick test script for dictionary lookup"""

from dictionary import get_dictionary

def test_lookups():
    """Test dictionary lookups"""
    print("Loading dictionary...")
    d = get_dictionary()
    
    test_phrases = [
        '你好',
        '中国',
        '学习',
        '中文',
        '谢谢',
        '再见'
    ]
    
    print("\nTesting lookups:")
    print("-" * 60)
    for phrase in test_phrases:
        entry = d.lookup_best(phrase)
        if entry:
            print(f"{phrase}: {entry['pinyin']} - {entry['definition']}")
        else:
            print(f"{phrase}: Not found")
    
    print("\n" + "-" * 60)
    print("Dictionary ready to use!")

if __name__ == '__main__':
    test_lookups()
