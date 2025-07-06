#!/usr/bin/env python3
"""
Word Counter for Intellectual Analysis
Counts words with precision to prevent hallucination about length
"""

def count_words(text):
    """Count words in text, excluding markdown formatting"""
    import re
    
    # Remove markdown formatting
    text = re.sub(r'#+\s+', '', text)  # Remove headers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Remove italic
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Remove code
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Remove links
    
    # Split into words and count
    words = text.split()
    return len(words)

def count_file_words(filepath):
    """Count words in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return count_words(content)
    except Exception as e:
        print(f"Error reading file: {e}")
        return 0

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        word_count = count_file_words(filepath)
        print(f"📊 Word count: {word_count:,}")
        
        if word_count >= 3000:
            print(f"✅ Target achieved: {word_count:,} words (target: 3,000)")
        else:
            print(f"⚠️ Below target: {word_count:,} words (need {3000-word_count:,} more)")
    else:
        print("Usage: python3 word_counter.py <filepath>")