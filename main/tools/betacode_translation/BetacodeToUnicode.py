import sqlite3
import unicodedata
import re
import pandas as pd
from pathlib import Path

# Used info from https://en.wikipedia.org/wiki/Beta_Code

alphabet_map = {}

punctuation_map = {}

diacritic_map = {}

# basic removes ? which denote start of paragraphs,
# removes variants (in between {}),
# and ensures words at the end and beginning of lines aren't stuck together
def clean_betacode(text, basic=True):
    # must be run with load_alphabet_map, load_diacritic_map
    if basic:
        text = text.replace("?", "")
        lines = text.splitlines()
        joined = " ".join(line.strip() for line in lines if line.strip())
        cleaned = re.sub(r"\{[^}]*\}", "", joined)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned
    return text

def is_consonant(char):
    vowels = "aeiouAEIOU"
    return char.isalpha() and char not in vowels

def make_alphabet(conn):
    df = pd.read_csv(Path(Path(__file__).parent / "betacode_alphabet.csv"), usecols=[0, 1, 3, 4])

    uppercase = df.iloc[:, :2]
    lowercase = df.iloc[:, -2:]

    # Rename columns to be the same before concatenation
    uppercase.columns = ['letter', 'betacode']
    lowercase.columns = ['letter', 'betacode']

    # Stack row-wise
    new_df = pd.concat([uppercase, lowercase], axis=0).reset_index(drop=True)

    # Choose the first value of ',' seperated values
    # Can do this because the source files don't distinguish between medial and final sigmas
    new_df['betacode'] = new_df['betacode'].str.split(',').str[0]

    new_df = new_df.dropna(how='all')

    new_df.to_sql('alphabet', conn, if_exists='replace', index=False)

def test_alphabet(conn):
    df = pd.read_sql_query('SELECT * FROM alphabet', conn)
    df.to_csv(Path(__file__).parent / "..\\..\\..\\output\\betacode_to_unicode\\alphabet.csv", index=False, encoding="utf-8-sig")

def make_punctuation(conn):
    # Wikipedia uses — 	and _ for unicode and beta code respectively, byzantine-majority-text uses - for both as does this program
    df = pd.read_csv(Path(Path(__file__).parent / "betacode_punctuation.csv"), usecols=[0, 1])

    df.columns = ['punctuation', 'betacode']

    df.to_sql('punctuation', conn, if_exists='replace', index=False)

def test_punctuation(conn):
    df = pd.read_sql_query('SELECT * FROM punctuation', conn)
    df.to_csv(Path(__file__).parent / "..\\..\\..\\output\\betacode_to_unicode\\punctuation.csv", index=False, encoding="utf-8-sig")

def make_diacritics(conn):
    df = pd.read_csv(Path(Path(__file__).parent / "betacode_diacritics.csv"), usecols=[0, 1])

    # Ignores last row which contains the coding for the breve, which is not in the ancient text
    df = df[:-1]

    df.columns = ['diacritic', 'betacode']

    df.to_sql('diacritics', conn, if_exists='replace', index=False)

def test_diacritics(conn):
    df = pd.read_sql_query('SELECT * FROM diacritics', conn)
    df.to_csv(Path(__file__).parent / "..\\..\\..\\output\\betacode_to_unicode\\diacritics.csv", index=False, encoding="utf-8-sig")

def load_alphabet_map(cursor):
    global alphabet_map
    # exclude ς because of dict uniqueness
    cursor.execute("SELECT betacode, letter FROM alphabet WHERE letter != 'ς'")
    alphabet_map = dict(cursor.fetchall())

def load_punctuation_map(cursor):
    global punctuation_map
    cursor.execute("SELECT betacode, punctuation FROM punctuation")
    punctuation_map = dict(cursor.fetchall())

def load_diacritic_map(cursor):
    global diacritic_map
    cursor.execute("SELECT betacode, diacritic FROM diacritics")
    diacritic_map = dict(cursor.fetchall())

def make_betacode_bible(cursor): 
    cursor.execute('DROP TABLE IF EXISTS betacode_bible')

    cursor.execute('''CREATE TABLE IF NOT EXISTS betacode_bible (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER
                   )''')
    
    base = Path(Path(__file__).parent / "..\\..\\..\\external_sources\\byzantine-majority-text-master\\source\\ccat")
    book_file_names = [
        base / "01_MAT.TXT",   # Matthew
        base / "02_MAR.TXT",   # Mark
        base / "03_LUK.TXT",   # Luke
        base / "04_JOH.TXT",   # John
        base / "05_ACT.TXT",   # Acts
        base / "06_ROM.TXT",   # Romans
        base / "07_1CO.TXT",   # 1 Corinthians
        base / "08_2CO.TXT",   # 2 Corinthians
        base / "09_GAL.TXT",   # Galatians
        base / "10_EPH.TXT",   # Ephesians
        base / "11_PHP.TXT",   # Philippians
        base / "12_COL.TXT",   # Colossians
        base / "13_1TH.TXT",   # 1 Thessalonians
        base / "14_2TH.TXT",   # 2 Thessalonians
        base / "15_1TI.TXT",   # 1 Timothy
        base / "16_2TI.TXT",   # 2 Timothy
        base / "17_TIT.TXT",   # Titus
        base / "18_PHM.TXT",   # Philemon
        base / "19_HEB.TXT",   # Hebrews
        base / "20_JAM.TXT",   # James
        base / "21_1PE.TXT",   # 1 Peter
        base / "22_2PE.TXT",   # 2 Peter
        base / "23_1JO.TXT",   # 1 John
        base / "24_2JO.TXT",   # 2 John
        base / "25_3JO.TXT",   # 3 John
        base / "26_JUD.TXT",   # Jude
        base / "27_REV.TXT"    # Revelation
    ]

    total_word_index = 1
    for file_name in book_file_names:
        with open(file_name, "r", encoding="utf-8") as file:
            contents = file.read()
            cleaned = clean_betacode(contents, True)
            words = cleaned.split(" ")
            book = ""
            name = str(file_name.relative_to(base))
            book = name[3:].split('.')[0]
            chapter = 1
            verse = 1
            word_index = 1
            for word in words:
                # chapter and verse is now in form Chapter:Verse
                if len(word) == 5 and (word.replace(":", "")).isdigit() and word[2] == ":":
                    last_chapter = chapter
                    last_verse = verse
                    chapter = int(word[:2])
                    verse = int(word[3:])
                    if chapter != last_chapter or verse != last_verse:
                        word_index = 1
                else:
                    cursor.execute('''
                            INSERT INTO betacode_bible (word, book, chapter, verse, word_index, total_word_index)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ''',
                            (word, book, chapter, verse, word_index, total_word_index)
                            )
                    word_index += 1
                    total_word_index += 1

def test_betacode_bible(conn):
    df = pd.read_sql_query('SELECT * FROM betacode_bible', conn)
    df.to_csv(Path(__file__).parent / "..\\..\\..\\output\\betacode_to_unicode\\betacode_bible.csv", index=False, encoding="utf-8-sig")

def make_sample_betacode_bible(cursor): 
    cursor.execute('DROP TABLE IF EXISTS sample_betacode_bible')

    cursor.execute('''CREATE TABLE IF NOT EXISTS sample_betacode_bible (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER
                   )''')
    
    base = Path(Path(__file__).parent / "..\\..\\testing")
    book_file_names = [
        base / "Test Matthew.txt",   # Matthew
    ]

    total_word_index = 1
    for file_name in book_file_names:
        with open(file_name, "r", encoding="utf-8") as file:
            contents = file.read()
            cleaned = clean_betacode(contents, True)
            words = cleaned.split(" ")
            book = "MAT"
            chapter = 1
            verse = 1
            word_index = 1
            for word in words:
                # chapter and verse is now in form Chapter:Verse
                if len(word) == 5 and (word.replace(":", "")).isdigit() and word[2] == ":":
                    last_chapter = chapter
                    last_verse = verse
                    chapter = int(word[:2])
                    verse = int(word[3:])
                    if chapter != last_chapter or verse != last_verse:
                        word_index = 1
                else:
                    cursor.execute('''
                            INSERT INTO sample_betacode_bible (word, book, chapter, verse, word_index, total_word_index)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ''',
                            (word, book, chapter, verse, word_index, total_word_index)
                            )
                    word_index += 1
                    total_word_index += 1

def test_sample_betacode_bible(conn):
    df = pd.read_sql_query('SELECT * FROM sample_betacode_bible', conn)
    df.to_csv(Path(__file__).parent / "..\\..\\..\\output\\betacode_to_unicode\\sample_betacode_bible.csv", index=False, encoding="utf-8-sig")

def is_last_letter(word, index, alphabet_map):
    length = len(word)
    if index >= length:
        return True
    for i in range(index + 1, length):
        if word[i] in alphabet_map:
            return False
    return True

def capitalize(word, index, alphabet_map):
    if index >= len(word) - 1:
        raise ValueError("ERROR IN capitalize: * APPEARS AT END OF WORD OR INCORRECT INDEX")
    else:
        for i in range(index + 1, len(word)):
            if word[i] in alphabet_map:
                word[index] += word[i]
                del(word[i])
                return
    raise ValueError("ERROR IN capitalize: NO * IN WORD")
    # if i + 2 >= len(old_word_list):
    #     raise ValueError("ERROR IN make_bible: * APPEARS AT END OF WORD")
    # if old_word_list[i + 1] in diacritic_map and old_word_list[i + 2] in alphabet_map:
    #     temp = old_word_list[i + 1]
    #     old_word_list[i + 1] = old_word_list[i + 2]
    #     old_word_list[i + 2] = temp
    # capital = ''.join(old_word_list[i:i+2])

def is_after_consonant(word, index, alphabet_map):
    # with open(Path(__file__).parent / '..\\..\\..\\output\\betacode_to_unicode\\breve_test.txt', 'a', encoding='utf-8') as out_file:
    #     out_file.write(''.join(word) + '\n')
    for i in range(index - 1, -1, -1):
        if word[i] in alphabet_map:
            if is_consonant(word[i]):
                return True
            return False
    raise ValueError("ERROR IN is_after_consonant: NO LETTERS BEFORE INDEX")

def make_bible(cursor):
    # with open(Path(__file__).parent / '..\\..\\..\\output\\betacode_to_unicode\\capitalize_test.txt', 'w', encoding='utf-8') as out_file:
    #     out_file.write("HEY HEY \n")

    with open(Path(__file__).parent / '..\\..\\..\\output\\betacode_to_unicode\\dash_test.txt', 'w', encoding='utf-8') as out_file:
        out_file.write("HEY HEY \n")

    # Must be run with load_alphabet_map, load_punctuation_map, and load_diacritic_map
    cursor.execute('DROP TABLE IF EXISTS bible')

    cursor.execute('''CREATE TABLE IF NOT EXISTS bible (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER
                   )''')
    
    global alphabet_map, punctuation_map, diacritic_map

    cursor.execute("SELECT word, book, chapter, verse, word_index, total_word_index FROM betacode_bible")

    rows = cursor.fetchall()
    for row in rows:
        old_word = row[0]
        letters = [""] * len(old_word)
        i = 0
        old_word_list = list(old_word)

        star_index = old_word.find('*')
        if star_index != -1:
            capitalize(old_word_list, star_index, alphabet_map)

        while i < len(old_word_list):
            char = None
            char = alphabet_map.get(old_word_list[i])
            if char is not None:
                if is_last_letter(old_word_list, i, alphabet_map) and old_word_list[i] == "S":
                    char = "ς"
            else:
                char = diacritic_map.get(old_word_list[i])
                # print(f"diacritic char {char}")
                if char is None:
                    char = punctuation_map.get(old_word_list[i])
                    # print(f"punctuation char {char}")
                    if char is None:
                        # with open(Path(__file__).parent / '..\\..\\..\\output\\betacode_to_unicode\\dash_test.txt', 'a', encoding='utf-8') as out_file:
                        #     out_file.write(char + " " + ''.join(old_word_list) + '\n')
                        char = "!" # Test to see if any errors

            letters[i] = char
            i += 1
        word = ''.join(letters)
        word = re.sub(r"\s+", "", word)
        # if capitalized:
        #     with open(Path(__file__).parent / '..\\..\\..\\output\\betacode_to_unicode\\capitalize_test.txt', 'a', encoding='utf-8') as out_file:
        #                 out_file.write(word + '\n')
        word = unicodedata.normalize('NFC', word)
        # if capitalized:
        #     with open(Path(__file__).parent / '..\\..\\..\\output\\betacode_to_unicode\\capitalize_test.txt', 'a', encoding='utf-8') as out_file:
        #                 out_file.write(word + '\n')
        book = row[1]
        chapter = row[2]
        verse = row[3]
        word_index = row[4]
        total_word_index = row[5]

        cursor.execute('''INSERT INTO bible (word, book, chapter, verse, word_index, total_word_index)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''',
                        (word, book, chapter, verse, word_index, total_word_index)
                    )

def test_bible(conn):
    df = pd.read_sql_query('SELECT * FROM bible', conn)
    df.to_csv(Path(__file__).parent / "..\\..\\..\\output\\betacode_to_unicode\\bible.csv", index=False, encoding="utf-8-sig")

def main():
    # Connect to a database (or create it)
    conn = sqlite3.connect('WordGuide.db')
    cursor = conn.cursor()

    make_alphabet(conn)
    test_alphabet(conn)

    make_punctuation(conn)
    test_punctuation(conn)

    make_diacritics(conn)
    test_diacritics(conn)

    make_betacode_bible(cursor)
    test_betacode_bible(conn)

    load_alphabet_map(cursor)

    load_punctuation_map(cursor)

    load_diacritic_map(cursor)

    # Must be run with load_alphabet_map, load_punctuation_map, and load_diacritic_map
    make_bible(cursor)

    test_bible(conn)

    # Always close the connection
    conn.commit()
    conn.close()


main()