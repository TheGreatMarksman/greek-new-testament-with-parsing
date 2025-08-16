import sqlite3
import unicodedata
import re
from collections import defaultdict
import pandas as pd
from pathlib import Path
import string

# Link to the grammar tables: https://en.wiktionary.org/wiki/Appendix:Ancient_Greek_grammar_tables
# GitHub Repo for Betacode files: https://github.com/byztxt/byzantine-majority-text

book_abbrevs = []
book_dfs = []
betacode_book_file_names = []

def is_int(i):
    try:
        int(i)
        return True
    except ValueError:
        return False

def remove_curly_sections(text):
    while True:
        start = text.find("{")
        end = text.find("}", start)
        if start != -1 and end != -1 and end > start:
            text = text[:start] + text[end + 1:]
        else:
            break
    return text

# Pass conn not cursor to this function
def make_articles(conn):
    # Loading csv file of morphologies into SQLite db
    df = pd.read_csv('../grammar_tables/Articles.csv')
    df['Morphology'] = df['Morphology'].apply(simplify)
    df.to_sql('articles', conn, if_exists='replace', index=False)

def test_article(cursor):
    # Write the results to a text file
    cursor.execute('SELECT * FROM articles ORDER BY Morphology ASC')
    article_rows = cursor.fetchall()
    with open('../output/test_articles.txt', 'w', encoding='utf-8') as out_file:
        for row in article_rows:
            out_file.write(f"{row}\n")  # word: count


# OLD rp_pdf FUNCTIONALITY - USES SIMILAR FUNCTIONS SO MUST INTEGRATE WITH CAUTION

# def make_rp_pdf_verses(cursor):
#     #rp stands for Robinson-Pierpont
#     cursor.execute('DROP TABLE IF EXISTS rp_pdf_verses')
    
#     cursor.execute('''CREATE TABLE IF NOT EXISTS rp_pdf_verses (
#                    id INTEGER PRIMARY KEY AUTOINCREMENT,
#                    book VARCHAR(45),
#                    chapter INTEGER,
#                    verse INTEGER,
#                    content TEXT
#                    )''')

#     # Mt for Matthew, Mk for Mark, etc.
#     book_abbrevs = []
#     with open('rp_pdf_book_abbrevs.txt', 'r', encoding='utf-8') as file:
#         content = file.read()
#         book_abbrevs = [word.strip() for word in content.split(',')]

#     with open('../external_sources/Robinson_Pierpont_GNT.txt', 'r', encoding='utf-8') as file:
#         # Read the entire file content and split it into verses
#         pattern = '|'.join(re.escape(book) for book in book_abbrevs)
#         content = file.read()
#         verses = re.split(pattern, content)
#         book_index = 0
#         for verse in verses:
#             words = verse.split()
#             chapter_verse = words[0].split(':')
#             if len(chapter_verse) == 2 and is_int(chapter_verse[0]) and is_int(chapter_verse[1]):
#                 if int(chapter_verse[0]) == 1 and int(chapter_verse[1]) == 1 and book_abbrevs[book_index] != "Mt" and book_abbrevs[book_index] != "Rv":
#                     book_index += 1
#                     if book_index >= len(book_abbrevs):
#                         break
#                 raw_verse = " ".join(words[1:])
#                 if book_abbrevs[book_index] == "Rv" and int(chapter_verse[0]) == 6 and int(chapter_verse[1]) == 4:
#                     print(raw_verse)
#                 # Robinson-Pierpoint has textual variants in "{}" - this line removes them
#                 raw_verse = remove_curly_sections(raw_verse)
#                 raw_verse = raw_verse.replace("•", "")
#                 raw_verse = raw_verse.replace("¶", "")
#                 # Remove URLs
#                 raw_verse = re.sub(r"https?://\S+", "", raw_verse)
#                 # Remove multiple spaces
#                 raw_verse = re.sub(r"\s+", " ", raw_verse).strip()
#                 cursor.execute('''
#                         INSERT INTO rp_pdf_verses (book, chapter, verse, content)
#                         VALUES (?, ?, ?, ?)
#                         ''', (book_abbrevs[book_index], chapter_verse[0], chapter_verse[1], raw_verse))
#                 if book_abbrevs[book_index] == "Mt" and int(chapter_verse[0]) == 28 and int(chapter_verse[1]) == 20:
#                     book_index += 1
#                 if book_abbrevs[book_index] == "Rv" and int(chapter_verse[0]) == 22 and int(chapter_verse[1]) == 21:
#                     break

# def test_one_rp_pdf_verse(cursor):
#     # Write the results to a text file
#     cursor.execute('SELECT book, chapter, verse, content FROM rp_pdf_verses WHERE chapter = ?', (1,))
#     row = cursor.fetchone()
#     if row:
#         with open('../output/test_verse.txt', 'w', encoding='utf-8') as out_file:
#             out_file.write(f"{row}\n")
#     else:
#         print("ERROR IN MAKING VERSES DB")

# def test_rp_pdf_verses(cursor):
#     # Write the results to a text file
#     cursor.execute('SELECT book, chapter, verse, content FROM rp_pdf_verses')
#     rows = cursor.fetchall()
#     with open('../output/test_verses.txt', 'w', encoding='utf-8') as out_file:
#         for row in rows:
#             out_file.write(f"{row}\n")

# def curly_brace_test(cursor):
#     cursor.execute('SELECT book, chapter, verse, content FROM rp_pdf_verses WHERE book = ? AND chapter = ? AND verse = ?', ("Mt", 1, 5))
#     row = cursor.fetchone()
#     if row:
#         print(repr(row))
#     else:
#         print("ERROR IN curly_brace_test")

# def make_word_info_and_word_instances(cursor):
#     # Making word db
#     # Drop old table (important if changing schema)
#     cursor.execute('DROP TABLE IF EXISTS word_info')
    
#     # count means how many times it appears, pos means part of speech, number means singular, plural etc.
#     # Use [case] because case is reserved keyword in sql
#     cursor.execute('''CREATE TABLE IF NOT EXISTS word_info (
#                    id INTEGER PRIMARY KEY AUTOINCREMENT,
#                    word VARCHAR(45) UNIQUE,
#                    count INTEGER,
#                    pos VARCHAR(45),
#                    gender VARCHAR(45),
#                    number VARCHAR(45),
#                    [case] VARCHAR(45)
#                    )''')

#     cursor.execute('DROP TABLE IF EXISTS word_instances')

#     cursor.execute('''CREATE TABLE IF NOT EXISTS word_instances (
#                    id INTEGER PRIMARY KEY AUTOINCREMENT,
#                    info_id INTEGER,
#                    book VARCHAR(45),
#                    chapter INTEGER,
#                    verse INTEGER,
#                    FOREIGN KEY (info_id) REFERENCES word_info(id)
#                    )''')
    



#     # APPLICATION



#     # Normalize all words and add them to a hash map (dict)
#     word_counts = defaultdict(int)
#     # Open the file in read mode with UTF-8 encoding
#     with open('Robinson_Pierpont_GNT.txt', 'r', encoding='utf-8') as file:
#         # Read the entire file content and split it into words
#         words = file.read().split()
#         for word in words:
#             key = normalize(word)
#             if(not is_ascii(key)):
#                 word_counts[key] += 1
#     for key in word_counts:
#         cursor.execute("SELECT Gender, Number, [Case] FROM articles WHERE Morphology = ?", (key,))
#         row = cursor.fetchone()
#         pos = "N/A"
#         gender = "N/A"
#         number = "N/A"
#         case = "N/A"
#         if row:
#             pos = "Article"
#             gender = row[0]
#             number = row[1]
#             case = row[2]
#         cursor.execute('''
#                     INSERT INTO word_info (word, count, pos, gender, number, [case])
#                     VALUES (?, ?, ?, ?, ?, ?)
#                     ON CONFLICT(word) DO UPDATE SET count = count + excluded.count
#                     ''', (key, word_counts[key], pos, gender, number, case))

# def test_word_info(cursor):
#     # Query data
#     cursor.execute('SELECT * FROM word_info ORDER BY word ASC')
#     word_rows = cursor.fetchall()

#     # Write the results to a text file
#     with open('../output/test_word_info.txt', 'w', encoding='utf-8') as out_file:
#         for row in word_rows:
#             out_file.write(f"{row}\n")  # word: count

# def test_word_instances(cursor):
#     # Query data
#     cursor.execute('SELECT * FROM word_instances')
#     word_rows = cursor.fetchall()

#     # Write the results to a text file
#     with open('../output/test_word_instances.txt', 'w', encoding='utf-8') as out_file:
#         for row in word_rows:
#             out_file.write(f"{row}\n")  # word: count


# END OF OLD rp_pdf FUNCTIONALITY

def simplify(word, remove_capitals = True, remove_scripts = True, remove_accents = True, remove_punctuation = True, remove_pilcrow = True):
    if remove_accents:
        # Normalize to NFD to split base and diacritics
        word = unicodedata.normalize('NFD', word)
        
        # Remove combining characters (diacritics like tonos)
        word = ''.join(c for c in word if not unicodedata.combining(c))

        # Normalize again to NFC to recompose (optional)
        word = unicodedata.normalize('NFC', word)

    if remove_scripts:
        # Remove superscripts and subscripts using Unicode category
        # Superscripts/subscripts often fall under categories 'No' (Number, Other) or specific ranges
        word = ''.join(
            c for c in word
            if not ('SUPERSCRIPT' in unicodedata.name(c, '') or
                    'SUBSCRIPT' in unicodedata.name(c, '') or
                    'MODIFIER LETTER SMALL' in unicodedata.name(c, ''))
        )
    
    if remove_capitals:
        # Casefold for lowercase Unicode-aware matching
        word = word.casefold()

        if word[-1] == 'σ':
            word = word[:-1] + 'ς'
    
    if remove_punctuation:
        # Remove punctuation
        word = re.sub(r'[^\w\s]', '', word)

    if remove_pilcrow:
        word = word.replace("¶", "")

    return word

def clean_betacode(word):
    # Remove everything in between {}
    word = re.sub(r"\{[^}]*\}", "", word)

    word = remove_apostrophe_after_consonant(word)

    # Remove only . , : ; _ #
    word = re.sub(r"[.,:;_#?]", "", word)
    # Collapse multiple spaces and strip edges
    word = re.sub(r"\s+", " ", word).strip()
    return word

def remove_apostrophe_after_consonant(word):
    result = []
    i = 0
    while i < len(word):
        if word[i] == "'" and i > 0 and is_consonant(word[i-1]):
            # Skip this apostrophe
            i += 1
            continue
        else:
            result.append(word[i])
            i += 1
    return ''.join(result)

def is_consonant(char):
    vowels = "aeiouAEIOU"
    return char.isalpha() and char not in vowels

# converts to standard polytonic form - no capitals unless word is a proper noun, keep accents but grave accents turned into accute
def to_std_poly_form(word, is_proper_noun = False):
    if word == "Disputed word":
        return ""
    if is_proper_noun:
        word = word[0] + simplify(word[1:], True, True, False, True)
    word = simplify(word, True, True, False, True)

    # Decompose characters into base + combining marks
    decomposed = unicodedata.normalize("NFD", word)
    # Replace combining grave accent (U+0300) with  acute accent (U+0301)
    replaced = decomposed.replace('\u0300', '\u0301')
    # Recompose characters
    return unicodedata.normalize("NFC", replaced)

# converts to monotonic uppercase form - all caps, sigma is converted to C, no diacritics
def to_mono_UC_form(word):
    if word == "Disputed word":
        return ""
    word = simplify(word, False)
    word = word.upper()
    word = word.replace('Σ', 'C')
    return word

def is_ascii(word):
    return all(ord(char) < 128 for char in word)

# Print the word and its Unicode code points
def describeWord(word):
    if isinstance(word, str):
        print(f"Word: {word}")
        print("Unicode code points:", ' '.join(f"U+{ord(char):04X}" for char in word))
        print()


def load_test_book_abbrevs():
    global book_abbrevs
    book_abbrevs = ["MAT"]

def load_book_abbrevs():
    with open(Path(__file__).parent / 'tools\\rp_book_abbrevs.txt', 'r', encoding='utf-8') as file:
        global book_abbrevs
        content = file.read()
        book_abbrevs = [word.strip() for word in content.split(',')]

def load_book_dfs():
    global book_dfs
    base = Path(Path(__file__).parent / "..\\external_sources\\byzantine-majority-text-master\\csv-unicode\\strongs\\no-parsing")
    # Makes list of all csv files in folder: book_dfs = [pd.read_csv(file) for file in folder_path.glob("*.csv")]
    book_dfs = [
        pd.read_csv(base / "MAT.csv"),   # Matthew
        pd.read_csv(base / "MAR.csv"),   # Mark
        pd.read_csv(base / "LUK.csv"),   # Luke
        pd.read_csv(base / "JOH.csv"),   # John
        pd.read_csv(base / "ACT.csv"),   # Acts
        pd.read_csv(base / "ROM.csv"),   # Romans
        pd.read_csv(base / "1CO.csv"),   # 1 Corinthians
        pd.read_csv(base / "2CO.csv"),   # 2 Corinthians
        pd.read_csv(base / "GAL.csv"),   # Galatians
        pd.read_csv(base / "EPH.csv"),   # Ephesians
        pd.read_csv(base / "PHP.csv"),   # Philippians
        pd.read_csv(base / "COL.csv"),   # Colossians
        pd.read_csv(base / "1TH.csv"),   # 1 Thessalonians
        pd.read_csv(base / "2TH.csv"),   # 2 Thessalonians
        pd.read_csv(base / "1TI.csv"),   # 1 Timothy
        pd.read_csv(base / "2TI.csv"),   # 2 Timothy
        pd.read_csv(base / "TIT.csv"),   # Titus
        pd.read_csv(base / "PHM.csv"),   # Philemon
        pd.read_csv(base / "HEB.csv"),   # Hebrews
        pd.read_csv(base / "JAM.csv"),   # James
        pd.read_csv(base / "1PE.csv"),   # 1 Peter
        pd.read_csv(base / "2PE.csv"),   # 2 Peter
        pd.read_csv(base / "1JO.csv"),   # 1 John
        pd.read_csv(base / "2JO.csv"),   # 2 John
        pd.read_csv(base / "3JO.csv"),   # 3 John
        pd.read_csv(base / "JUD.csv"),   # Jude
        pd.read_csv(base / "REV.csv")    # Revelation
    ]

def load_parsed_book_dfs():
    global book_dfs
    base = Path(Path(__file__).parent / "..\\external_sources\\byzantine-majority-text-master\\csv-unicode\\strongs\\with-parsing")
    # Makes list of all csv files in folder: book_dfs = [pd.read_csv(file) for file in folder_path.glob("*.csv")]
    book_dfs = [
        pd.read_csv(base / "MAT.csv"),   # Matthew
        pd.read_csv(base / "MAR.csv"),   # Mark
        pd.read_csv(base / "LUK.csv"),   # Luke
        pd.read_csv(base / "JOH.csv"),   # John
        pd.read_csv(base / "ACT.csv"),   # Acts
        pd.read_csv(base / "ROM.csv"),   # Romans
        pd.read_csv(base / "1CO.csv"),   # 1 Corinthians
        pd.read_csv(base / "2CO.csv"),   # 2 Corinthians
        pd.read_csv(base / "GAL.csv"),   # Galatians
        pd.read_csv(base / "EPH.csv"),   # Ephesians
        pd.read_csv(base / "PHP.csv"),   # Philippians
        pd.read_csv(base / "COL.csv"),   # Colossians
        pd.read_csv(base / "1TH.csv"),   # 1 Thessalonians
        pd.read_csv(base / "2TH.csv"),   # 2 Thessalonians
        pd.read_csv(base / "1TI.csv"),   # 1 Timothy
        pd.read_csv(base / "2TI.csv"),   # 2 Timothy
        pd.read_csv(base / "TIT.csv"),   # Titus
        pd.read_csv(base / "PHM.csv"),   # Philemon
        pd.read_csv(base / "HEB.csv"),   # Hebrews
        pd.read_csv(base / "JAM.csv"),   # James
        pd.read_csv(base / "1PE.csv"),   # 1 Peter
        pd.read_csv(base / "2PE.csv"),   # 2 Peter
        pd.read_csv(base / "1JO.csv"),   # 1 John
        pd.read_csv(base / "2JO.csv"),   # 2 John
        pd.read_csv(base / "3JO.csv"),   # 3 John
        pd.read_csv(base / "JUD.csv"),   # Jude
        pd.read_csv(base / "REV.csv")    # Revelation
    ]

def load_acc_cap_book_dfs():
    global book_dfs
    base = Path(Path(__file__).parent / "..\\external_sources\\byzantine-majority-text-master\\csv-unicode\\ccat\\no-variants")
    book_dfs = [
        pd.read_csv(base / "MAT.csv"),   # Matthew
        pd.read_csv(base / "MAR.csv"),   # Mark
        pd.read_csv(base / "LUK.csv"),   # Luke
        pd.read_csv(base / "JOH.csv"),   # John
        pd.read_csv(base / "ACT.csv"),   # Acts
        pd.read_csv(base / "ROM.csv"),   # Romans
        pd.read_csv(base / "1CO.csv"),   # 1 Corinthians
        pd.read_csv(base / "2CO.csv"),   # 2 Corinthians
        pd.read_csv(base / "GAL.csv"),   # Galatians
        pd.read_csv(base / "EPH.csv"),   # Ephesians
        pd.read_csv(base / "PHP.csv"),   # Philippians
        pd.read_csv(base / "COL.csv"),   # Colossians
        pd.read_csv(base / "1TH.csv"),   # 1 Thessalonians
        pd.read_csv(base / "2TH.csv"),   # 2 Thessalonians
        pd.read_csv(base / "1TI.csv"),   # 1 Timothy
        pd.read_csv(base / "2TI.csv"),   # 2 Timothy
        pd.read_csv(base / "TIT.csv"),   # Titus
        pd.read_csv(base / "PHM.csv"),   # Philemon
        pd.read_csv(base / "HEB.csv"),   # Hebrews
        pd.read_csv(base / "JAM.csv"),   # James
        pd.read_csv(base / "1PE.csv"),   # 1 Peter
        pd.read_csv(base / "2PE.csv"),   # 2 Peter
        pd.read_csv(base / "1JO.csv"),   # 1 John
        pd.read_csv(base / "2JO.csv"),   # 2 John
        pd.read_csv(base / "3JO.csv"),   # 3 John
        pd.read_csv(base / "JUD.csv"),   # Jude
        pd.read_csv(base / "REV.csv")    # Revelation
    ]

def load_test_parsed_book_dfs():
    global book_dfs
    book_dfs = [
        pd.read_csv(Path(Path(__file__).parent / "testing\\Test Matthew.csv"))
    ]

def load_betacode_book_file_names():
    global betacode_book_file_names
    base = Path(Path(__file__).parent / "..\\external_sources\\byzantine-majority-text-master\\source\\ccat")
    betacode_book_file_names = [
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



# OLD
# def load_rp_code_info():
#     rp_code_info = pd.read_csv(Path(__file__).parent / "tools\\rp_code_info.csv")

# def load_rp_code_info_tables():
#     csv_dir = Path(__file__).parent / "tools\\rp_code_info\\rp_code_info_tables"

#     for csv_file in csv_dir.glob("*.csv"):
#         key = csv_file.stem  # filename without extension
#         df = pd.read_csv(csv_file)
#         rp_code_info_tables[key] = df



def make_rp_code_tables(cursor):
    # Must be run with load_book_abbrevs and load_parsed_book_dfs
    cursor.execute('DROP TABLE IF EXISTS rp_codes')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS rp_codes (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   code VARCHAR(45),
                   pos VARCHAR(45),
                   info_length INTEGER,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER
                   )''')
    
    cursor.execute('DROP TABLE IF EXISTS rp_pos_combos')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS rp_pos_combos (
                   pos VARCHAR(45) NOT NULL,
                   info_length INTEGER NOT NULL,
                   example_code VARCHAR(45),
                   count INTEGER NOT NULL DEFAULT 1,
                   PRIMARY KEY (pos, info_length)
                   )''')
    

    book_counter = 0
    for df in book_dfs:
        for _, row in df.iterrows():
            book = book_abbrevs[book_counter]
            chapter = int(row["chapter"])
            verse = int(row["verse"])
            text = row["text"]
            words = text.split()
            i = 2
            while i < len(words):
                code = words[i].replace("{", "").replace("}", "")
                breakdown = code.split("-", 1)
                pos = get_rp_pos(breakdown[0])
                info_length = 0
                word_index = i
                if len(breakdown) == 2:
                    info_length = len(breakdown[1].replace("-", ""))
                cursor.execute('''
                               INSERT INTO rp_codes (code, pos, info_length, book, chapter, verse, word_index)
                               VALUES (?, ?, ?, ?, ?, ?, ?)
                               ''',
                               (code, pos, info_length, book, chapter, verse, word_index)
                            )
                cursor.execute('''
                               INSERT INTO rp_pos_combos (pos, info_length, example_code)
                               VALUES (?, ?, ?)
                               ON CONFLICT (pos, info_length)
                               DO UPDATE SET count = count + excluded.count
                               ''',
                               (pos, info_length, code)
                            )
                
                # Check if there's a "γη 1093 {N-NSF} 1093 {N-VSF}" situation
                if i + 2 < len(words):
                    if "{" in words[i + 2]:
                        i -= 1

                i += 3
        book_counter += 1

def test_rp_code_tables(conn):
    # df = pd.read_sql_query('SELECT code, pos, info_length, book, chapter, verse, word_index FROM rp_codes', conn)
    # df.to_csv("rp_codes.csv", index=False, encoding="utf-8-sig")

    # df = pd.read_sql_query('SELECT pos, info_length, example_code, count FROM rp_pos_combos ORDER BY pos ASC', conn)
    # df.to_csv("rp_pos_combos.csv", index=False, encoding="utf-8-sig")
    
    # df = pd.read_sql_query('SELECT code, pos, info_length, book, chapter, verse, word_index FROM rp_codes WHERE pos = "Unknown"', conn)
    # df.to_csv("unknown_rp_codes.csv", index=False, encoding="utf-8-sig")

    # df = pd.read_sql_query('SELECT DISTINCT pos, code, info_length FROM rp_codes ORDER BY pos ASC, info_length ASC', conn)
    # df.to_csv("distinct_rp_codes.csv", index=False, encoding="utf-8-sig")
    
    df = pd.read_sql_query('SELECT pos, code, book, chapter, verse, word_index FROM rp_codes WHERE pos = "Adjective" AND code LIKE "%-N" ORDER BY pos ASC', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\adjective_n_rp_codes.csv", index=False, encoding="utf-8-sig")

def make_rp_code_info(conn):
    df = pd.read_csv(Path(__file__).parent / "tools\\rp_code_info.csv")
    df.to_sql('rp_code_info', conn, if_exists='replace', index=False)

def test_rp_code_info(conn):
    df = pd.read_sql_query('SELECT * FROM rp_code_info', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\test_rp_code_info.csv", index=False, encoding="utf-8-sig")

def make_pos_abbrevs(cursor):
    # Must be run with load_book_abbrevs and load_parsed_book_dfs
    cursor.execute('DROP TABLE IF EXISTS pos_abbrevs')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS pos_abbrevs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   abbrev VARCHAR(45) UNIQUE,
                   count INTEGER NOT NULL DEFAULT 1,
                   example_code VARCHAR(45)
                   )''')
    
    book_counter = 0
    for df in book_dfs:
        for _, row in df.iterrows():
            book = book_abbrevs[book_counter]
            chapter = int(row["chapter"])
            verse = int(row["verse"])
            text = row["text"]
            words = text.split()
            i = 2
            while i < len(words):
                code = words[i].replace("{", "").replace("}", "")
                breakdown = code.split("-", 1)
                abbrev = breakdown[0]
                cursor.execute('''
                               INSERT INTO pos_abbrevs (abbrev, example_code)
                               VALUES (?, ?)
                               ON CONFLICT (abbrev)
                               DO UPDATE SET count = count + excluded.count
                               ''',
                               (abbrev, code)
                            )
                
                # Check if there's a "γη 1093 {N-NSF} 1093 {N-VSF}" situation
                if i + 2 < len(words):
                    if "{" in words[i + 2]:
                        i -= 1

                i += 3
        book_counter += 1

def test_pos_abbrevs(conn):
    df = pd.read_sql_query('SELECT abbrev, count, example_code FROM pos_abbrevs', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\pos_abbrevs.csv", index=False, encoding="utf-8-sig")

def make_traits(cursor):
    # Must be run with load_book_abbrevs and load_parsed_book_dfs
    cursor.execute('DROP TABLE IF EXISTS traits')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS traits (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name VARCHAR(45) UNIQUE,
                   abbrev VARCHAR(45),
                   count INTEGER NOT NULL DEFAULT 1,
                   example_code VARCHAR(45)
                   )''')
    
    cursor.execute("SELECT * FROM long_trait_codes")
    long_trait_codes_rows = cursor.fetchall()
    long_trait_codes = []
    for trait_row in long_trait_codes_rows:
        # trait_row[1] is column trait_code
        long_trait_codes.append(trait_row[1])

    book_counter = 0
    for df in book_dfs:
        for _, info_row in df.iterrows():
            text = info_row["text"]
            words = text.split()
            i = 2
            while i < len(words):
                code = words[i]
                code = code.replace("{", "")
                code = code.replace("}", "")
                code_parts = code.split("-")
                info  = "".join(code_parts[1:])
                traits = []
                trait_codes = []

                # making trait_codes, a list of abbreviations for traits
                j = 0
                while j < len(info):
                    matched = False
                    for sub in long_trait_codes:
                        if info.startswith(sub, j):
                            trait_codes.append(sub)
                            j += len(sub)
                            matched = True
                            break
                    if not matched:
                        trait_codes.append(info[j])
                        j += 1

                cursor.execute("SELECT * FROM rp_code_info WHERE abbreviation = ?", (code_parts[0],))
                info_rows = cursor.fetchall()
                for info_row in info_rows:
                    num_traits = int(info_row[2])
                    # We check this because num_traits is the number of possible traits
                    if len(trait_codes) > num_traits:
                        continue
                    for j in range(1, num_traits + 1):
                        # trait1 is at column 3
                        trait_index = 2 + j
                        traits.append(info_row[trait_index])
                    
                # print(traits)
                # print(trait_codes)
                # we use length of trait_codes because traits stores the maximum possible traits

                # if len(trait_codes) > len(traits):
                #     print(f"UNEQUAL: trait_codes: {trait_codes} traits {traits}")

                for j in range(0, min(len(trait_codes), len(traits))):
                    cursor.execute('''
                               INSERT INTO traits (name, abbrev, example_code) 
                               VALUES (?, ?, ?) 
                               ON CONFLICT(name) DO UPDATE SET count = count + excluded.count
                               ''',
                               (traits[j], trait_codes[j], code)
                            )
                
                # Check if there's a "γη 1093 {N-NSF} 1093 {N-VSF}" situation
                if i + 2 < len(words):
                    if "{" in words[i + 2]:
                        i -= 1

                i += 3
        book_counter += 1
    

def test_traits(conn):
    df = pd.read_sql_query('SELECT name, abbrev, count, example_code FROM traits', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\traits.csv", index=False, encoding="utf-8-sig")

def make_rp_code_trait_tables(cursor, conn):
    cursor.execute('DROP TABLE IF EXISTS long_trait_codes')
    
    # "long" here means more than one letter ex. ATT
    cursor.execute('''CREATE TABLE IF NOT EXISTS long_trait_codes (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   trait_code VARCHAR(45),
                   trait VARCHAR(45),
                   origin_table VARCHAR(45)
                   )''')
    

    csv_dir = Path(__file__).parent / "tools\\rp_code_trait_tables"
    for csv_file in csv_dir.glob("*.csv"):
        name = csv_file.stem  # filename without extension
        pd.read_csv(csv_file).to_sql(name, conn, if_exists='replace', index=False)
        cursor.execute(f'SELECT * FROM "{name}" WHERE LENGTH(Abbreviation) > 1')
        rows = cursor.fetchall()
        for row in rows:
            cursor.execute("INSERT INTO long_trait_codes (trait_code, trait, origin_table) VALUES (?,?,?)", (row[1], row[0], name))

def test_rp_code_trait_tables(conn):
    df = pd.read_sql_query('SELECT * FROM word_case', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\test_word_case.csv", index=False, encoding="utf-8-sig")

    df = pd.read_sql_query('SELECT * FROM long_trait_codes', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\long_trait_codes.csv", index=False, encoding="utf-8-sig")

def make_books(cursor):
    cursor.execute('DROP TABLE IF EXISTS books')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS books (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   book VARCHAR(45)
                   )''')
    
    for abbrev in book_abbrevs:
        cursor.execute("INSERT INTO books (book) VALUES (?)", (abbrev,))

def test_books(conn):
    df = pd.read_sql_query('SELECT * FROM books', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\books.csv", index=False, encoding="utf-8-sig")
    

def make_word_info(cursor):
    # Must be run with load_book_dfs
    cursor.execute('DROP TABLE IF EXISTS word_info')
    
    # count means how many times it appears, pos means part of speech, number means singular, plural etc.
    cursor.execute('''CREATE TABLE IF NOT EXISTS word_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45) UNIQUE,
                   count INTEGER,
                   pos VARCHAR(45),
                   gender VARCHAR(45),
                   number VARCHAR(45),
                   word_case VARCHAR(45)
                   )''')
    book_counter = 0
    for df in book_dfs:
        for _, row in df.iterrows():
            text = row["text"]
            words = text.split()
            for word in words:
                cursor.execute('''
                               INSERT INTO word_info (word, count)
                               VALUES (?, ?)
                               ON CONFLICT (word) DO UPDATE SET count = count + excluded.count
                               ''',
                               (word, 1)
                            )
                
        book_counter += 1

def test_word_info(cursor):
    # Query data
    cursor.execute('SELECT id, word, count FROM word_info')
    word_rows = cursor.fetchall()

    # Write the results to a text file
    with open('../output/word_info.txt', 'w', encoding='utf-8') as out_file:
        for row in word_rows:
            out_file.write(f"{row}\n")

def make_parsed_word_info(cursor):
    # Must be run with load_book_abbrevs and load_parsed_book_dfs
    # Make sure that make_rp_code_info and make_rp_code_trait_tables have been run before


    #TESTING
    # with open(Path(__file__).parent / "..\\output\\unknown_traits_log.txt", 'w', encoding='utf-8') as out_file:
    #     out_file.write("")

    # with open(Path(__file__).parent / "..\\output\\known_traits_log.txt", 'w', encoding='utf-8') as out_file:
    #     out_file.write("")

    # with open(Path(__file__).parent / "..\\output\\long_trait_code_info.txt", 'w', encoding='utf-8') as out_file:
    #     out_file.write("")

    cursor.execute('DROP TABLE IF EXISTS parsed_word_info')
    
    # count means how many times it appears, pos means part of speech, number means singular, plural etc.

    cursor.execute('''CREATE TABLE IF NOT EXISTS parsed_word_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45) UNIQUE,
                   count INTEGER,
                   str_num INTEGER,
                   rp_code VARCHAR(45),
                   rp_pos VARCHAR(45),
                   rp_gender VARCHAR(45),
                   rp_number VARCHAR(45),
                   rp_word_case VARCHAR(45),
                   rp_tense VARCHAR(45),
                   rp_type VARCHAR(45),
                   rp_voice VARCHAR(45),
                   rp_mood VARCHAR(45),
                   rp_person VARCHAR(45),
                   rp_indeclinable VARCHAR(45),
                   rp_why_indeclinable VARCHAR(45),
                   rp_kai_crasis VARCHAR(45),
                   rp_attic_greek_form VARCHAR(45)
                   )''')

    book_counter = 0
    for df in book_dfs:
        for _, info_row in df.iterrows():
            text = info_row["text"]
            words = text.split()
            i = 2
            while i < len(words):
                word = words[i - 2]
                count = 1

                try:
                    str_num = int(words[i - 1])
                except ValueError:
                    str_num = -1
                
                rp_dict = defaultdict(lambda: "")

                code = words[i]
                code = code.replace("{", "")
                code = code.replace("}", "")
                code_parts = code.split("-")
                info  = "".join(code_parts[1:])
                possible_traits = []
                trait_code_list = []


                cursor.execute("SELECT * FROM rp_code_info WHERE abbreviation = ?", (code_parts[0],))
                info_rows = cursor.fetchall()
                for info_row in info_rows:
                    cursor.execute("SELECT * FROM long_trait_codes")
                    long_trait_codes_rows = cursor.fetchall()
                    long_trait_codes = set()
                    for trait_row in long_trait_codes_rows:
                        # trait_row[1] is trait_code, trait_row[3] is the table it comes from
                        if trait_row[3] in info_row:
                            long_trait_codes.add(trait_row[1])

                    # making an element of trait_code_list, a list of lists of abbreviations for traits
                    trait_codes = []
                    j = 0
                    while j < len(info):
                        matched = False
                        for sub in long_trait_codes:
                            # info_row[0] is the pos
                            if info.startswith(sub, j):
                                trait_codes.append(sub)
                                j += len(sub)
                                matched = True
                                break
                        if not matched:
                            trait_codes.append(info[j])
                            j += 1
                    num_traits = int(info_row[2])
                    if len(trait_codes) != num_traits:
                        continue
                    # Append to trait_code_list after above statement to prevent adding an invalid set of codes
                    trait_code_list.append(trait_codes)
                    rp_pos = info_row[0]
                    traits = []
                    for j in range(1, num_traits + 1):
                        # trait1 is at column 3
                        trait_index = 2 + j
                        traits.append(info_row[trait_index])
                    possible_traits.append(traits)
                    # with open(Path(__file__).parent / "..\\output\\long_trait_code_info.txt", 'a', encoding='utf-8') as out_file:
                    #     out_file.write(f"{code} {info} {long_trait_codes} {trait_codes}\n")
                    
                for j in range(0, len(possible_traits)):
                    valid = True
                    if len(trait_code_list[j]) != len(possible_traits[j]):
                        raise ValueError(f"ERROR in make_parsed_word_info: different lengths - trait_code_list[j]: {trait_code_list[j]} possible_traits[j]: {possible_traits[j]}")
                    for k in range(0, len(possible_traits[j])):
                        cursor.execute(f"SELECT * FROM \"{possible_traits[j][k]}\" WHERE abbreviation = ?", (trait_code_list[j][k],))
                        result = cursor.fetchone()
                        if result:
                            # result[0] is the name of the trait
                            rp_dict[possible_traits[j][k]] = result[0]
                        else:
                            rp_dict[possible_traits[j][k]] = "Unknown"
                            valid = False
                            # with open(Path(__file__).parent / "..\\output\\unknown_traits_log.txt", 'a', encoding='utf-8') as out_file:
                            #     out_file.write(f"{code} {info} {trait_code_list} {possible_traits}\n")
                    if valid:
                        # with open(Path(__file__).parent / "..\\output\\known_traits_log.txt", 'a', encoding='utf-8') as out_file:
                        #         out_file.write(f"{code} {info} {trait_code_list} {possible_traits}\n")
                        for k, v in rp_dict.items():
                            if str(v).lower() == "unknown":
                                rp_dict[k] = ""
                        break
                        

                    

                cursor.execute('''
                               INSERT INTO parsed_word_info (word, count, str_num, rp_code, rp_pos, rp_gender, rp_number, rp_word_case, rp_tense, rp_type, rp_voice, rp_mood,
                               rp_person, rp_indeclinable, rp_why_indeclinable, rp_kai_crasis, rp_attic_greek_form) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
                               ON CONFLICT(word) DO UPDATE SET count = count + excluded.count
                               ''',
                               (word, count, str_num, code, rp_pos, rp_dict["gender"], rp_dict["number"], rp_dict["word_case"], rp_dict["tense"], rp_dict["type"], rp_dict["voice"],
                                rp_dict["mood"], rp_dict["person"], rp_dict["indeclinable"], rp_dict["why_indeclinable"], rp_dict["kai_crasis"], rp_dict["attic_greek_form"])
                            )

                # Check if there's a "γη 1093 {N-NSF} 1093 {N-VSF}" situation
                if i + 2 < len(words):
                    if "{" in words[i + 2]:
                        i -= 1

                i += 3
        book_counter += 1

def test_parsed_word_info(conn):
    df = pd.read_sql_query('SELECT * FROM parsed_word_info', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\parsed_word_info.csv", index=False, encoding="utf-8-sig")

    # Unknown words
    # query = '''
    #     SELECT * FROM parsed_word_info
    #     WHERE word = 'Unknown'
    #     OR rp_code = 'Unknown'
    #     OR rp_pos = 'Unknown'
    #     OR rp_gender = 'Unknown'
    #     OR rp_number = 'Unknown'
    #     OR rp_word_case = 'Unknown'
    #     OR rp_tense = 'Unknown'
    #     OR rp_type = 'Unknown'
    #     OR rp_voice = 'Unknown'
    #     OR rp_mood = 'Unknown'
    #     OR rp_person = 'Unknown'
    #     OR rp_indeclinable = 'Unknown'
    #     OR rp_why_indeclinable = 'Unknown'
    #     OR rp_kai_crasis = 'Unknown'
    #     OR rp_attic_greek_form = 'Unknown' ORDER BY rp_code ASC;
    # '''
    # df = pd.read_sql_query(query, conn)
    # df.to_csv(Path(__file__).parent / "..\\output\\testing\\unknown_words.csv", index=False, encoding="utf-8-sig")

def test_make_parsed_word_info(cursor):
    text = "οπως 3704 {ADV} καγω 2504 {P-1NS-K} ελθων 2064 {V-2AAP-NSM}"
    words = text.split()
    i = 2
    while i < len(words):
        word = words[i - 2]
        count = 1

        try:
            str_num = int(words[i - 1])
        except ValueError:
            str_num = -1
        
        rp_dict = defaultdict(lambda: "")

        code = words[i]
        code = code.replace("{", "")
        code = code.replace("}", "")
        code_parts = code.split("-")
        info  = "".join(code_parts[1:])
        possible_traits = []
        trait_code_list = []


        cursor.execute("SELECT * FROM rp_code_info WHERE abbreviation = ?", (code_parts[0],))
        info_rows = cursor.fetchall()
        for info_row in info_rows:
            cursor.execute("SELECT * FROM long_trait_codes")
            long_trait_codes_rows = cursor.fetchall()
            long_trait_codes = set()
            for trait_row in long_trait_codes_rows:
                # trait_row[1] is trait_code, trait_row[3] is the table it comes from
                if trait_row[3] in info_row:
                    long_trait_codes.add(trait_row[1])

            # making an element of trait_code_list, a list of lists of abbreviations for traits
            trait_codes = []
            j = 0
            while j < len(info):
                matched = False
                for sub in long_trait_codes:
                    # info_row[0] is the pos
                    if info.startswith(sub, j):
                        trait_codes.append(sub)
                        j += len(sub)
                        matched = True
                        break
                if not matched:
                    trait_codes.append(info[j])
                    j += 1
            num_traits = int(info_row[2])
            if len(trait_codes) != num_traits:
                continue
            # Append to trait_code_list after above statement to prevent adding an invalid set of codes
            trait_code_list.append(trait_codes)
            rp_pos = info_row[0]
            traits = []
            for j in range(1, num_traits + 1):
                # trait1 is at column 3
                trait_index = 2 + j
                traits.append(info_row[trait_index])
            possible_traits.append(traits)
            # with open(Path(__file__).parent / "..\\output\\long_trait_code_info.txt", 'a', encoding='utf-8') as out_file:
            #     out_file.write(f"{code} {info} {long_trait_codes} {trait_codes}\n")
            
        for j in range(0, len(possible_traits)):
            valid = True
            if len(trait_code_list[j]) != len(possible_traits[j]):
                raise ValueError(f"ERROR in make_parsed_word_info: different lengths - trait_code_list[j]: {trait_code_list[j]} possible_traits[j]: {possible_traits[j]}")
            for k in range(0, len(possible_traits[j])):
                cursor.execute(f"SELECT * FROM \"{possible_traits[j][k]}\" WHERE abbreviation = ?", (trait_code_list[j][k],))
                result = cursor.fetchone()
                if result:
                    # result[0] is the name of the trait
                    rp_dict[possible_traits[j][k]] = result[0]
                else:
                    rp_dict[possible_traits[j][k]] = "Unknown"
                    valid = False
                    # with open(Path(__file__).parent / "..\\output\\unknown_traits_log.txt", 'a', encoding='utf-8') as out_file:
                    #     out_file.write(f"{code} {info} {trait_code_list} {possible_traits}\n")
            if valid:
                # with open(Path(__file__).parent / "..\\output\\known_traits_log.txt", 'a', encoding='utf-8') as out_file:
                #         out_file.write(f"{code} {info} {trait_code_list} {possible_traits}\n")
                for k, v in rp_dict.items():
                    if str(v).lower() == "unknown":
                        rp_dict[k] = ""
                break
                

            
        print(word)
        print(rp_dict)

        # Check if there's a "γη 1093 {N-NSF} 1093 {N-VSF}" situation
        if i + 2 < len(words):
            if "{" in words[i + 2]:
                i -= 1

        i += 3

def make_parsed_word_instances(cursor):
    # Must be run with load_book_abbrevs and load_parsed_book_dfs
    # Make sure that make_rp_code_info, make_rp_code_trait_tables, and make_parsed_word_info have been run before

    cursor.execute('DROP TABLE IF EXISTS parsed_word_instances')

    cursor.execute('''CREATE TABLE IF NOT EXISTS parsed_word_instances (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   info_id INTEGER,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER,
                   FOREIGN KEY (info_id) REFERENCES parsed_word_info(id)
                   )''')

    book_counter = 0
    total_word_index = 1
    for df in book_dfs:
        for _, info_row in df.iterrows():
            book = book_abbrevs[book_counter]
            chapter = int(info_row["chapter"])
            verse = int(info_row["verse"])
            text = info_row["text"]
            words = text.split()
            word_index = 1
            i = 2
            while i < len(words):
                word = words[i - 2]
                
                cursor.execute('SELECT id FROM parsed_word_info WHERE word = ?', (word,))
                result = cursor.fetchone()
                word_id = -1
                if result:
                    word_id = result[0]
                else:
                    raise ValueError("ERROR in make_parsed_word_instances(cursor): parsed_word_info word key should be unique")
                cursor.execute('''
                            INSERT INTO parsed_word_instances (info_id, book, chapter, verse, word_index, total_word_index)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ''',
                            (word_id, book, chapter, verse, word_index, total_word_index)
                            )
                word_index += 1
                total_word_index += 1

                # Check if there's a "γη 1093 {N-NSF} 1093 {N-VSF}" situation
                if i + 2 < len(words):
                    if "{" in words[i + 2]:
                        i -= 1

                i += 3
        book_counter += 1

def test_parsed_word_instances(conn):
    df = pd.read_sql_query('SELECT * FROM parsed_word_instances', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\parsed_word_instances.csv", index=False, encoding="utf-8-sig")

def make_strongs_word_instances(cursor):
    # No capitals, accents, variants
    cursor.execute('DROP TABLE IF EXISTS strongs_word_instances')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS strongs_word_instances (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   info_id INTEGER,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   FOREIGN KEY (info_id) REFERENCES word_info(id)
                   )
                   '''
                )

    book_counter = 0
    for df in book_dfs:
        for _, row in df.iterrows():
            book = book_abbrevs[book_counter]
            chapter = int(row["chapter"])
            verse = int(row["verse"])
            text = row["text"]
            words = text.split()
            word_index = 1
            for word in words:
                cursor.execute('SELECT id FROM word_info WHERE word = ?', (word,))
                result = cursor.fetchone()
                word_id = -1
                if result:
                    word_id = result[0]
                else:
                    raise ValueError("ERROR in make_strongs_word_instances(cursor): word_info word key should be unique")
                cursor.execute('''
                               INSERT INTO strongs_word_instances (info_id, book, chapter, verse, word_index)
                               VALUES (?, ?, ?, ?, ?)
                               ''',
                               (word_id, book, chapter, verse, word_index)
                            )
                word_index += 1
                
        book_counter += 1

def test_strongs_word_instances(cursor):
    # Query data
    cursor.execute('SELECT info_id, book, chapter, verse, word_index FROM strongs_word_instances')
    word_rows = cursor.fetchall()

    # Write the results to a text file
    with open('../output/strongs_word_instances.txt', 'w', encoding='utf-8') as out_file:
        for row in word_rows:
            out_file.write(f"{row}\n")

def make_disputed_acc_cap_words(cursor):
    cursor.execute('DROP TABLE IF EXISTS disputed_acc_cap_words')

    cursor.execute('''CREATE TABLE IF NOT EXISTS disputed_acc_cap_words (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER
                   )''')

    disputed_book_abbrevs = ["JOH", "ACT"]
    base = Path(Path(__file__).parent / "..\\external_sources\\byzantine-majority-text-master\\csv-unicode\\ccat\\no-variants")
    disputed_book_dfs = [
        pd.read_csv(base / "PA.csv"),    # John 7:53 - 8:11
        pd.read_csv(base / "ACT24.csv") # Acts 24:6-8
    ]

    book_counter = 0
    for df in disputed_book_dfs:
        for _, row in df.iterrows():
            book = disputed_book_abbrevs[book_counter]
            chapter = int(row["chapter"])
            verse = int(row["verse"])
            text = row["text"]
            words = text.split()
            word_index = 1
            for word in words:
                cleaned_word = simplify(word, False, False, False, True)

                cursor.execute('''
                            INSERT INTO disputed_acc_cap_words (word, book, chapter, verse, word_index)
                            VALUES (?, ?, ?, ?, ?)
                            ''',
                            (cleaned_word, book, chapter, verse, word_index)
                            )
                word_index += 1
        book_counter += 1

def test_disputed_acc_cap_words(conn):
    df = pd.read_sql_query('SELECT * FROM disputed_acc_cap_words', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\disputed_acc_cap_words.csv", index=False, encoding="utf-8-sig")

# Accented, capitalized
def make_acc_cap_word_info(cursor):
    # Must be run with load_book_abbrevs and load_acc_cap_book_dfs

    cursor.execute('DROP TABLE IF EXISTS acc_cap_word_info')

    cursor.execute('''CREATE TABLE IF NOT EXISTS acc_cap_word_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   parsed_id INTEGER,
                   word VARCHAR(45) UNIQUE,
                   simplified_word VARCHAR(45),
                   count INTEGER,
                   FOREIGN KEY (parsed_id) REFERENCES parsed_word_info(id)
                   )''')

    for df in book_dfs:
        for _, row in df.iterrows():
            text = row["text"]
            words = text.split()
            for word in words:
                cleaned_word = simplify(word, False, False, False, True)
                parsed_id = -1
                simplified_word = simplify(cleaned_word)
                cursor.execute("SELECT id FROM parsed_word_info WHERE word = ?", (simplified_word,))
                parsed_row = cursor.fetchone()
                if parsed_row:
                    parsed_id = parsed_row[0]
                else:
                    raise ValueError("ERROR in make_acc_cap_word_info: should have matching word in parsed_word_info table")
                count = 1
                cursor.execute('''
                            INSERT INTO acc_cap_word_info (parsed_id, word, simplified_word, count)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT (word) DO UPDATE SET count = count + excluded.count
                            ''',
                            (parsed_id, cleaned_word, simplified_word, count)
                            )
                

def test_acc_cap_word_info(conn):
    df = pd.read_sql_query('SELECT * FROM acc_cap_word_info', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\acc_cap_word_info.csv", index=False, encoding="utf-8-sig")

def make_acc_cap_word_instances(cursor):
    # Must be run with load_book_abbrevs and load_acc_cap_book_dfs
    # Make sure that make_rp_code_info, make_rp_code_trait_tables, make_parsed_word_info, make_acc_cap_word_info have been run before

    cursor.execute('DROP TABLE IF EXISTS acc_cap_word_instances')

    cursor.execute('''CREATE TABLE IF NOT EXISTS acc_cap_word_instances (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   info_id INTEGER,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER,
                   FOREIGN KEY (info_id) REFERENCES acc_cap_word_info(id)
                   )''')

    book_counter = 0
    total_word_index = 1
    for df in book_dfs:
        for _, info_row in df.iterrows():
            book = book_abbrevs[book_counter]
            chapter = int(info_row["chapter"])
            verse = int(info_row["verse"])
            text = info_row["text"]
            words = text.split()
            word_index = 1
            for word in words:
                cleaned_word = simplify(word, False, False, False, True)
                cursor.execute('SELECT id FROM acc_cap_word_info WHERE word = ?', (cleaned_word,))
                result = cursor.fetchone()
                word_id = -1
                if result:
                    word_id = result[0]
                else:
                    raise ValueError("ERROR in make_acc_cap_word_instances(cursor): acc_cap_word_info word key should be unique")
                
                cursor.execute('''
                            INSERT INTO acc_cap_word_instances (info_id, book, chapter, verse, word_index, total_word_index)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ''',
                            (word_id, book, chapter, verse, word_index, total_word_index)
                            )
                word_index += 1
                total_word_index += 1
                
        book_counter += 1


def test_acc_cap_word_instances(conn):
    df = pd.read_sql_query('SELECT * FROM acc_cap_word_instances', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\acc_cap_word_instances.csv", index=False, encoding="utf-8-sig")


# Both disputed and non_disputed word instances
def make_unified_word_instances(cursor):
    cursor.execute('DROP TABLE IF EXISTS unified_word_instances')

    cursor.execute('''CREATE TABLE IF NOT EXISTS unified_word_instances
                   AS
                   SELECT ins.info_id, ins.book, ins.chapter, ins.verse, ins.word_index, ins.total_word_index, alt.word AS disputed_alt
                   FROM acc_cap_word_instances ins
                   LEFT JOIN disputed_acc_cap_words alt
                   ON ins.book = alt.book AND ins.chapter = alt.chapter AND ins.verse = alt.verse AND ins.word_index = alt.word_index
                   ''')
    
    cursor.execute('''INSERT INTO unified_word_instances (book, chapter, verse, word_index, total_word_index, disputed_alt)
                   SELECT a.book, a.chapter, a.verse, a.word_index, a.word FROM disputed_acc_cap_words a
                   WHERE NOT EXISTS (
                        SELECT 1 FROM acc_cap_word_instances b WHERE a.book = b.book
                        AND a.chapter = b.chapter
                        AND a.verse = b.verse
                        AND a.word_index = b.word_index
                   )
                   ''')

def test_unified_word_instances(conn):
    df = pd.read_sql_query('SELECT * FROM unified_word_instances', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\unified_word_instances.csv", index=False, encoding="utf-8-sig")

    # df = pd.read_sql_query('''SELECT * FROM disputed_acc_cap_words a
    #                             WHERE NOT EXISTS (
    #                                 SELECT 1 FROM acc_cap_word_instances b WHERE a.book = b.book
    #                                 AND a.chapter = b.chapter
    #                                 AND a.verse = b.verse
    #                                 AND a.word_index = b.word_index
    #                             )
    #                        ''', conn)
    # df.to_csv(Path(__file__).parent / "..\\output\\test_file.csv", index=False, encoding="utf-8-sig")
    

# Word info and instances
def make_words_no_disputes(cursor):
    cursor.execute('DROP TABLE IF EXISTS words_no_disputes')

    cursor.execute('''CREATE TABLE IF NOT EXISTS words_no_disputes 
                   AS
                    SELECT ins.book, ins.chapter, ins.verse, ins.word_index, total_word_index,
                                ac.word AS source_form,
                                ac.count AS source_form_count,
                                inf.word AS mono_LC_form,
                                inf.count AS mono_LC_form_count,
                                inf.str_num, inf.rp_code, inf.rp_pos,
                                inf.rp_gender, inf.rp_number, inf.rp_word_case, inf.rp_tense, inf.rp_type, inf.rp_voice, inf.rp_mood,
                                inf.rp_person, inf.rp_indeclinable, inf.rp_why_indeclinable, inf.rp_kai_crasis, inf.rp_attic_greek_form
                        FROM acc_cap_word_instances ins
                            JOIN acc_cap_word_info ac ON ins.info_id = ac.id
                        JOIN parsed_word_info inf ON ac.parsed_id = inf.id
                   ''')
    
def test_words_no_disputes(conn):
    df = pd.read_sql_query('SELECT * FROM words_no_disputes', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\words_no_disputes.csv", index=False, encoding="utf-8-sig")

# Word info and instances with disputed words
def make_words_with_disputes(cursor):
    # Must be run with make_words_no_disputes
    cursor.execute('DROP TABLE IF EXISTS words_with_disputes')

    cursor.execute('''CREATE TABLE IF NOT EXISTS words_with_disputes 
                   AS
                    SELECT * FROM words_no_disputes
                   ''')
    
    cursor.execute('''INSERT INTO words_with_disputes (disputed)
                   AS
                    SELECT * FROM words_no_disputes
                   ''')
    
def test_words_with_disputes(conn):
    df = pd.read_sql_query('SELECT * FROM words_with_disputes', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\words_with_disputes.csv", index=False, encoding="utf-8-sig")


def make_betacode_words(cursor): 
    # Must be run with load_betacode_book_file_names

    cursor.execute('DROP TABLE IF EXISTS betacode_words')

    cursor.execute('''CREATE TABLE IF NOT EXISTS betacode_words (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER
                   )''')
    
    total_word_index = 1
    global betacode_book_file_names
    for file_name in betacode_book_file_names:
        with open(file_name, "r", encoding="utf-8") as file:
            contents = file.read()
            cleaned = clean_betacode(contents)
            words = cleaned.split(" ")
            book = ""
            base = Path(Path(__file__).parent / "..\\external_sources\\byzantine-majority-text-master\\source\\ccat")
            name = str(file_name.relative_to(base))
            book = name[3:].split('.')[0]
            chapter = 1
            verse = 1
            word_index = 1
            for word in words:
                # chapter and verse is now in form ChapterVerse
                if len(word) == 4 and word.isdigit():
                    last_chapter = chapter
                    last_verse = verse
                    chapter = int(word[:2])
                    verse = int(word[2:])
                    if chapter != last_chapter or verse != last_verse:
                        word_index = 1
                else:
                    cursor.execute('''
                            INSERT INTO betacode_words (word, book, chapter, verse, word_index)
                            VALUES (?, ?, ?, ?, ?)
                            ''',
                            (word, book, chapter, verse, word_index)
                            )
                    word_index += 1
                    total_word_index += 1
                

def test_betacode_words(conn):
    df = pd.read_sql_query('SELECT * FROM betacode_words', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\betacode_words.csv", index=False, encoding="utf-8-sig")

def make_disputed_betacode_words(cursor):
    cursor.execute('DROP TABLE IF EXISTS disputed_betacode_words')

    cursor.execute('''CREATE TABLE IF NOT EXISTS disputed_betacode_words (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER
                   )''')

    disputed_book_abbrevs = ["JOH", "ACT"]
    base = Path(Path(__file__).parent / "..\\external_sources\\byzantine-majority-text-master\\source\\ccat")
    disputed_betacode_book_file_names = [
        base / "04a_PA.TXT",
        base / "05a_ACT24.TXT"
    ]
    book_counter = 0
    for file_name in disputed_betacode_book_file_names:
        with open(file_name, "r", encoding="utf-8") as file:
            contents = file.read()
            # Remove everything between curly braces including the braces
            cleaned = clean_betacode(contents)
            words = cleaned.split(" ")
            book = disputed_book_abbrevs[book_counter]
            chapter = 1
            verse = 1
            word_index = 1
            for word in words:
                # chapter and verse is now in form ChapterVerse
                if len(word) == 4 and word.isdigit():
                    last_chapter = chapter
                    last_verse = verse
                    chapter = int(word[:2])
                    verse = int(word[2:])
                    if chapter != last_chapter or verse != last_verse:
                        word_index = 1
                else:
                    cursor.execute('''
                            INSERT INTO disputed_betacode_words (word, book, chapter, verse, word_index)
                            VALUES (?, ?, ?, ?, ?)
                            ''',
                            (word, book, chapter, verse, word_index)
                            )
                    word_index += 1
        book_counter += 1

def test_disputed_betacode_words(conn):
    df = pd.read_sql_query('SELECT * FROM disputed_betacode_words', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\disputed_betacode_words.csv", index=False, encoding="utf-8-sig")

# Both disputed and non_disputed betacode words
def make_unified_betacode_words(cursor):
    cursor.execute('DROP TABLE IF EXISTS unified_betacode_words')

    cursor.execute('''CREATE TABLE IF NOT EXISTS unified_betacode_words
                   AS
                   SELECT beta.word, beta.book, beta.chapter, beta.verse, beta.word_index, beta.total_word_index, balt.word AS disputed_betacode_alt
                   FROM betacode_words beta
                   LEFT JOIN disputed_betacode_words balt
                   ON beta.book = balt.book AND beta.chapter = balt.chapter AND beta.verse = balt.verse AND beta.word_index = balt.word_index
                   ''')
    
    cursor.execute('''INSERT INTO unified_betacode_words (book, chapter, verse, word_index, total_word_index, disputed_betacode_alt)
                   SELECT a.book, a.chapter, a.verse, a.word_index, a.word FROM disputed_betacode_words a
                   WHERE NOT EXISTS (
                        SELECT 1 FROM betacode_words b WHERE a.book = b.book
                        AND a.chapter = b.chapter
                        AND a.verse = b.verse
                        AND a.word_index = b.word_index
                   )
                   ''')

def test_unified_betacode_words(conn):
    df = pd.read_sql_query('SELECT * FROM unified_betacode_words', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\unified_betacode_words.csv", index=False, encoding="utf-8-sig")

def make_unknown_betacode_symbols(cursor):
    cursor.execute('DROP TABLE IF EXISTS unknown_betacode_symbols')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unknown_betacode_symbols AS
        SELECT word, book, chapter, verse, word_index
        FROM betacode_words
        WHERE word GLOB '*[^a-zA-Z*()/=+|&\\-]*'
        AND word NOT LIKE '%''%'
        AND word NOT LIKE '%\\\\%'
    ''')



def test_unknown_betacode_symbols(conn):
    df = pd.read_sql_query('SELECT * FROM unknown_betacode_symbols', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\unknown_betacode_symbols.csv", index=False, encoding="utf-8-sig")

def make_betacode_apostrophes(cursor):
    # requires load_betacode_book_file_names
    cursor.execute('DROP TABLE IF EXISTS betacode_apostrophes')

    cursor.execute('''CREATE TABLE IF NOT EXISTS betacode_apostrophes (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45) UNIQUE
                   )''')
    
    global betacode_book_file_names
    for file_name in betacode_book_file_names:
        with open(file_name, "r", encoding="utf-8") as file:
            contents = file.read()
            words = contents.split(" ")
            for word in words:
                if "'" in word:
                    cursor.execute('''INSERT OR IGNORE INTO betacode_apostrophes (word) VALUES (?)''', (word,))

def test_betacode_apostrophes(conn):
    df = pd.read_sql_query('SELECT * FROM betacode_apostrophes', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\betacode_apostrophes.csv", index=False, encoding="utf-8-sig")

def make_kjv_word_instances(cursor):
    # KJV
    cursor.execute('DROP TABLE IF EXISTS strongs_word_instances')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS strongs_word_instances (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   info_id INTEGER,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER,
                   FOREIGN KEY (info_id) REFERENCES word_info(id)
                   )
                   '''
                )

    book_counter = 0
    total_word_index = 1
    for df in book_dfs:
        for _, row in df.iterrows():
            book = book_abbrevs[book_counter]
            chapter = int(row["chapter"])
            verse = int(row["verse"])
            text = row["text"]
            words = text.split()
            word_index = 1
            for word in words:
                cursor.execute('SELECT id FROM word_info WHERE word = ?', (word,))
                result = cursor.fetchone()
                word_id = -1
                if result:
                    word_id = result[0]
                else:
                    raise ValueError("ERROR in make_strongs_word_instances(cursor): word_info word key should be unique")
                cursor.execute('''
                               INSERT INTO strongs_word_instances (info_id, book, chapter, verse, word_index)
                               VALUES (?, ?, ?, ?, ?)
                               ''',
                               (word_id, book, chapter, verse, word_index)
                            )
                word_index += 1
                total_word_index += 1
                
        book_counter += 1

def test_kjv_word_instances(cursor):
    # Query data
    cursor.execute('SELECT info_id, book, chapter, verse, word_index FROM strongs_word_instances')
    word_rows = cursor.fetchall()

    # Write the results to a text file
    with open('../output/strongs_word_instances.txt', 'w', encoding='utf-8') as out_file:
        for row in word_rows:
            out_file.write(f"{row}\n")


def make_betacode_translator_differences(cursor):
    # Must be run with load_book_abbrevs and load_acc_cap_book_dfs
    # Uses "bible" table generated in tools\\BetacodeToUnicode\\BetacodeToUnicode.py
    cursor.execute('DROP TABLE IF EXISTS betacode_translator_differences')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS betacode_translator_differences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word VARCHAR(45),
                   diff_word VARCHAR(45),
                    book VARCHAR(45),
                    chapter INTEGER,
                    verse INTEGER,
                    word_index INTEGER,
                    total_word_index INTEGER
                   )
                   '''
                )
    
    cursor.execute("SELECT word, book, chapter, verse, word_index, total_word_index FROM bible")
    translated_rows = cursor.fetchall()
    translated_index = 0

    book_counter = 0
    total_word_index = 1
    for df in book_dfs:
        for _, info_row in df.iterrows():
            book = book_abbrevs[book_counter]
            chapter = int(info_row["chapter"])
            verse = int(info_row["verse"])
            text = info_row["text"]
            words = text.split()
            word_index = 1
            for word in words:
                word = simplify(word, False, False, False, False, True)

                tr_word = translated_rows[translated_index][0]
                tr_book = translated_rows[translated_index][1]
                tr_chapter = translated_rows[translated_index][2]
                tr_verse = translated_rows[translated_index][3]
                tr_word_index = translated_rows[translated_index][4]

                # print(f"word {word} book {book} chapter {chapter} verse {verse} word_index {word_index}")
                # print(f"tr_word {tr_word} tr_book {tr_book} tr_chapter {tr_chapter} tr_verse {tr_verse} tr_word_index {tr_word_index}")
                # return


                if book == tr_book and chapter == tr_chapter and verse == tr_verse and word_index == tr_word_index:
                    if word != tr_word:
                        cursor.execute('''INSERT INTO betacode_translator_differences (word, diff_word, book, chapter, verse, word_index)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                       ''',
                                       (word, tr_word, book, chapter, verse, word_index)
                                       )
                    # else:
                    #     cursor.execute('''INSERT INTO betacode_translator_differences (word, diff_word, book, chapter, verse, word_index)
                    #                     VALUES (?, ?, ?, ?, ?, ?)
                    #                    ''',
                    #                    (word, "Correct", book, chapter, verse, word_index)
                    #                    )
                else:
                    cursor.execute('''INSERT INTO betacode_translator_differences (word, diff_word, book, chapter, verse, word_index)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                       ''',
                                       (word, "error", book, chapter, verse, word_index)
                                       )
                
                word_index += 1
                total_word_index += 1
                translated_index += 1
                
        book_counter += 1
    
def test_betacode_translator_differences(conn):
    df = pd.read_sql_query('''SELECT * FROM betacode_translator_differences btd
                           INNER JOIN betacode_bible bb ON
                           btd.book = bb.book AND btd.chapter = bb.chapter AND btd.verse = bb.verse AND btd.word_index = bb.word_index''', conn)
    df.to_csv(Path(__file__).parent / "..\\output\\betacode_translator_differences.csv", index=False, encoding="utf-8-sig")

def make_word_classification(conn):
    df = pd.read_sql_query("""
    SELECT
        uni.book, uni.chapter, uni.verse, uni.word_index, uni.total_word_index,
        ac.word AS source_form,
        ac.count AS source_form_count,
        inf.word AS mono_LC_form,
        inf.count AS mono_LC_form_count,
        uni.disputed_alt,
        buni.word AS betacode,
        buni.disputed_betacode_alt,
        inf.str_num, inf.rp_code, inf.rp_pos,
        inf.rp_gender, inf.rp_number, inf.rp_word_case, inf.rp_tense, inf.rp_type, inf.rp_voice, inf.rp_mood,
        inf.rp_person, inf.rp_indeclinable, inf.rp_why_indeclinable, inf.rp_kai_crasis, inf.rp_attic_greek_form                     
    FROM unified_word_instances uni
    JOIN unified_betacode_words buni ON uni.book = buni.book AND uni.chapter = buni.chapter AND uni.verse = buni.verse AND uni.word_index = buni.word_index
    JOIN books boo ON uni.book = boo.book
    LEFT JOIN acc_cap_word_info ac ON uni.info_id = ac.id
    LEFT JOIN parsed_word_info inf ON ac.parsed_id = inf.id
    ORDER BY boo.id, uni.book, uni.chapter, uni.verse, uni.word_index
    """, conn)

    # Makes any blank cell source_form cell 'Disputed word'
    df.loc[df['disputed_alt'].notnull() & df['source_form'].isnull(), 'source_form'] = 'Disputed word'

    df["std_poly_form"] = df.apply(
        lambda row: to_std_poly_form(row["source_form"], True) if row["rp_why_indeclinable"] == "proper noun" else to_std_poly_form(row["source_form"]), axis=1
    )
    df["mono_UC_form"] = df["source_form"].apply(to_mono_UC_form)

    # Reorder columns to put 'std_poly_form' ninth and 'mono_UC_form' tenth
    cols = df.columns.tolist()
    cols.insert(8, cols.pop(cols.index("std_poly_form")))
    cols.insert(9, cols.pop(cols.index("mono_UC_form")))
    df = df[cols]

    # Export DataFrame to CSV (no index column)
    df.to_csv(Path(__file__).parent / "..\\output\\word_classification.csv", index=False, encoding="utf-8-sig")
    

# Works but more practical to make tables as secondary steps
def old_make_word_classification(conn):
    df = pd.read_sql_query("""
                           SELECT combined.book, combined.chapter, combined.verse, combined.word_index,
                            combined.source_form, combined.source_form_count,
                            combined.mono_LC_form, combined.mono_LC_form_count,
                            combined.disputed_alt,
                            combined.betacode,
                            combined.disputed_betacode_alt,
                            combined.str_num, combined.rp_code, combined.rp_pos,
                            combined.rp_gender, combined.rp_number, combined.rp_word_case,
                            combined.rp_tense, combined.rp_type, combined.rp_voice, combined.rp_mood,
                            combined.rp_person, combined.rp_indeclinable, combined.rp_why_indeclinable,
                            combined.rp_kai_crasis, combined.rp_attic_greek_form FROM
                           (
                                SELECT 
                                ins.book, ins.chapter, ins.verse, ins.word_index,
                                ac.word AS source_form,
                                ac.count AS source_form_count,
                                inf.word AS mono_LC_form,
                                inf.count AS mono_LC_form_count,
                                alt.word AS disputed_alt,
                                beta.word AS betacode,
                                balt.word AS disputed_betacode_alt,
                                inf.str_num, inf.rp_code, inf.rp_pos,
                                inf.rp_gender, inf.rp_number, inf.rp_word_case, inf.rp_tense, inf.rp_type, inf.rp_voice, inf.rp_mood,
                                inf.rp_person, inf.rp_indeclinable, inf.rp_why_indeclinable, inf.rp_kai_crasis, inf.rp_attic_greek_form
                        FROM acc_cap_word_instances ins
                            JOIN acc_cap_word_info ac ON ins.info_id = ac.id
                        JOIN parsed_word_info inf ON ac.parsed_id = inf.id
                           JOIN betacode_words beta ON ins.book = beta.book AND ins.chapter = beta.chapter AND ins.verse = beta.verse AND ins.word_index = beta.word_index
                            LEFT JOIN disputed_acc_cap_words alt ON ins.book = alt.book AND ins.chapter = alt.chapter AND ins.verse = alt.verse AND ins.word_index = alt.word_index
                           LEFT JOIN disputed_betacode_words balt ON ins.book = balt.book AND ins.chapter = balt.chapter AND ins.verse = balt.verse AND ins.word_index = balt.word_index
                                
                                UNION ALL

                                SELECT
                                alt.book, alt.chapter, alt.verse, alt.word_index,
                                'Disputed word' AS source_form,
                                NULL AS source_form_count,
                                NULL AS mono_LC_form,
                                NULL AS mono_LC_form_count,
                                alt.word AS disputed_alt,
                                NULL AS betacode,
                                balt.word AS disputed_betacode_alt,
                                NULL AS str_num, NULL AS rp_code, NULL AS rp_pos,
                                NULL AS rp_gender, NULL AS rp_number, NULL AS rp_word_case, NULL AS rp_tense, NULL AS rp_type, NULL AS rp_voice, NULL AS rp_mood,
                                NULL AS rp_person, NULL AS rp_indeclinable, NULL AS rp_why_indeclinable, NULL AS rp_kai_crasis, NULL AS rp_attic_greek_form
                                FROM disputed_acc_cap_words alt
                           
                                LEFT JOIN disputed_betacode_words balt ON alt.book = balt.book AND alt.chapter = balt.chapter AND alt.verse = balt.verse AND alt.word_index = balt.word_index

                                LEFT JOIN acc_cap_word_instances ins ON alt.book = ins.book AND alt.chapter = ins.chapter AND alt.verse = ins.verse AND alt.word_index = ins.word_index
                                WHERE ins.book IS NULL
                            )
                           AS combined
                           LEFT JOIN books b ON combined.book = b.book ORDER BY b.id, combined.chapter, combined.verse, combined.word_index
                    """, conn
                   )



    df["std_poly_form"] = df.apply(
        lambda row: to_std_poly_form(row["source_form"], True) if row["rp_why_indeclinable"] == "proper noun" else to_std_poly_form(row["source_form"]), axis=1
    )
    df["mono_UC_form"] = df["source_form"].apply(to_mono_UC_form)

    # Reorder columns to put 'std_poly_form' ninth and 'mono_UC_form' tenth
    cols = df.columns.tolist()
    cols.insert(8, cols.pop(cols.index("std_poly_form")))
    cols.insert(9, cols.pop(cols.index("mono_UC_form")))
    df = df[cols]

    # Export DataFrame to CSV (no index column)
    df.to_csv(Path(__file__).parent / "..\\output\\old_word_classification.csv", index=False, encoding="utf-8-sig")
    
def run_tests(conn):
    # df = pd.read_sql_query("SELECT * FROM parsed_word_info WHERE rp_why_indeclinable = 'cardinal_number'", conn)
    # df.to_csv(Path(__file__).parent / "..\\output\\testing\\cardinal_number_word_instances.csv", index=False, encoding="utf-8-sig")

    df = pd.read_sql_query("SELECT * FROM parsed_word_info WHERE rp_kai_crasis IS NOT NULL", conn)
    df.to_csv(Path(__file__).parent / "..\\output\\testing\\kai_crasis_word_instances.csv", index=False, encoding="utf-8-sig")

def main():
    # Connect to a database (or create it)
    conn = sqlite3.connect('WordGuide.db')
    cursor = conn.cursor()

    # Necessary to run make_parsed_word_info, make_acc_cap_word_info, make_acc_cap_word_instances, make_books
    load_book_abbrevs()
    # Necessary to run make_parsed_word_info
    load_parsed_book_dfs()

    make_rp_code_info(conn)
    test_rp_code_info(conn)

    make_rp_code_trait_tables(cursor, conn)
    test_rp_code_trait_tables(conn)

    make_parsed_word_info(cursor)
    test_parsed_word_info(conn)

    # test_make_parsed_word_info(cursor)

    # Necessary to run make_acc_cap_word_info, make_acc_cap_word_instances
    # load_acc_cap_book_dfs()

    # make_acc_cap_word_info(cursor)
    # test_acc_cap_word_info(conn)

    # make_acc_cap_word_instances(cursor)
    # test_acc_cap_word_instances(conn)

    # make_disputed_acc_cap_words(cursor)
    # test_disputed_acc_cap_words(conn)

    # Necessary to run make_betacode_words
    # load_betacode_book_file_names()

    # make_betacode_apostrophes(cursor)
    # test_betacode_apostrophes(conn)

    # make_betacode_words(cursor)
    # test_betacode_words(conn)

    # make_disputed_betacode_words(cursor)
    # test_disputed_betacode_words(conn)

    # make_unified_word_instances(cursor)
    # test_unified_word_instances(conn)

    # make_unified_betacode_words(cursor)
    # test_unified_betacode_words(conn)

    # make_books(cursor)
    # test_books(conn)

    # make_word_classification(conn)

    # make_unknown_betacode_symbols(cursor)
    # test_unknown_betacode_symbols(conn)

    # make_betacode_translator_differences(cursor)
    # test_betacode_translator_differences(conn)

    # Always close the connection
    conn.commit()
    conn.close()


main()
