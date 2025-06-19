import sqlite3
import unicodedata
import re
from collections import defaultdict

# Normalize and compare words
def normalize(word):
    # Normalize to NFD to split base and diacritics
    word = unicodedata.normalize('NFD', word)
    
    # Remove combining characters (diacritics like tonos)
    word = ''.join(c for c in word if not unicodedata.combining(c))

    # Remove superscripts and subscripts using Unicode category
    # Superscripts/subscripts often fall under categories 'No' (Number, Other) or specific ranges
    word = ''.join(
        c for c in word
        if not ('SUPERSCRIPT' in unicodedata.name(c, '') or
                'SUBSCRIPT' in unicodedata.name(c, '') or
                'MODIFIER LETTER SMALL' in unicodedata.name(c, ''))
    )
    
    # Normalize again to NFC to recompose (optional)
    word = unicodedata.normalize('NFC', word)
    
    # Casefold for lowercase Unicode-aware matching
    word = word.casefold()
    
    # Remove punctuation
    word = re.sub(r'[^\w\s]', '', word)
    return word

def is_ascii(word):
    return all(ord(char) < 128 for char in word)

# Print the word and its Unicode code points
def describeWord(word):
    if isinstance(word, str):
        print(f"Word: {word}")
        print("Unicode code points:", ' '.join(f"U+{ord(char):04X}" for char in word))
        print()

def main():
    #print(f"ά normalized is {normalize('ά')}")

    # Connect to a database (or create it)
    conn = sqlite3.connect('WordGuide.db')
    cursor = conn.cursor()

    # Drop old table (important if changing schema)
    cursor.execute('DROP TABLE IF EXISTS words')
    #cursor.execute('DROP TABLE IF EXISTS derivations')

    # Create a table
    cursor.execute('''CREATE TABLE IF NOT EXISTS words (word TEXT UNIQUE PRIMARY KEY, count INTEGER)''')

    #cursor.execute('''CREATE TABLE IF NOT EXISTS derivations (id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT, root TEXT)''')

    # Normalize all words and add them to a hash map (dict)
    word_dict = defaultdict(int)
    # Open the file in read mode with UTF-8 encoding
    with open('robinson-pierpont-2018-gnt-edition.txt', 'r', encoding='utf-8') as file:
        # Read the entire file content and split it into words
        words = file.read().split()
        for word in words:
            key = normalize(word)
            if(not is_ascii(key)):
                word_dict[key] += 1
    for key in word_dict:
        # Insert data
        cursor.execute('''
                    INSERT INTO words (word, count)
                    VALUES (?, ?)
                    ON CONFLICT(word) DO UPDATE SET count = count + excluded.count
                    ''', (key, word_dict[key]))
        # for other_key in word_dict:
        #     if key != other_key and key in other_key:
        #         cursor.execute('''
        #                     INSERT INTO derivations (word, root)
        #                     VALUES (?, ?)
        #                     ''', (other_key, key))
        

    # Query data
    cursor.execute('SELECT * FROM words ORDER BY word ASC')
    word_rows = cursor.fetchall()

    # cursor.execute('SELECT word, root FROM derivations ORDER BY word ASC')
    # deriv_rows = cursor.fetchall()

    # Write the results to a text file
    with open('WordCounts.txt', 'w', encoding='utf-8') as out_file:
        for row in word_rows:
            out_file.write(f"{row}\n")  # word: count

    # with open('DerivationCounts.txt', 'w', encoding='utf-8') as out_file:
    #     for row in deriv_rows:
    #         out_file.write(f"{row}\n") 


    # Always close the connection
    conn.commit()
    conn.close()


main()
