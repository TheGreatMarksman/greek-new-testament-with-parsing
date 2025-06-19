import sqlite3
import unicodedata
import re
from collections import defaultdict
import pandas as pd
from pathlib import Path

# Link to the grammar tables: https://en.wiktionary.org/wiki/Appendix:Ancient_Greek_grammar_tables
# GitHub Repo for Betacode files: https://github.com/byztxt/byzantine-majority-text

rp_book_abbrevs = []
strongs_dfs = []

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
    df['Morphology'] = df['Morphology'].apply(normalize)
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

def get_rp_pos(string):
    match string:
        case "N":
            return "Noun"
        case "V":
            return "Verb"
        case "T":
            return "Article"
        case "A":
            return "Adjective"
        case "P":
            return "Personal Pronoun"
        case "Q":
            return "Correlative Pronoun"
        case "K":
            return "Correlative or Interrogative or Relative Pronoun"
        case "D":
            return "Demonstrative Pronoun"
        case "X":
            return "Indefinite Pronoun"
        case "I":
            return "Interrogative Pronoun"
        case "S":
            return "Possessive Pronoun"
        case "C":
            return "Reciprocal Pronoun"
        case "R":
            return "Relative Pronoun"
        case "F":
            return "Reflexive Pronoun"
        case "CONJ":
            return "Conjunction"
        case "COND":
            return "Conditional particle or conjunction"
        case "ADV":
            return "Adverb"
        case "CONJ":
            return "Conjunction"
        case "PREP":
            return "Preposition"
        case "PRT":
            return "Particle"
        case "INJ":
            return "Interjection"
        case "HEB":
            return "Hebraism"
        case "ARAM":
            return "Aramaism"
        case _:
            return "Unknown"

def load_test_rp_book_abbrevs():
    global rp_book_abbrevs
    rp_book_abbrevs = ["MAT"]

def load_rp_book_abbrevs():
    with open(Path(__file__).parent / 'rp_book_abbrevs.txt', 'r', encoding='utf-8') as file:
        global rp_book_abbrevs
        content = file.read()
        rp_book_abbrevs = [word.strip() for word in content.split(',')]

def load_strongs_dfs():
    global strongs_dfs
    base = Path(Path(__file__).parent / "..\\external_sources\\byzantine-majority-text-master\\csv-unicode\\strongs\\no-parsing")
    # Makes list of all csv files in folder: strongs_dfs = [pd.read_csv(file) for file in folder_path.glob("*.csv")]
    strongs_dfs = [
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

def load_parsed_strongs_dfs():
    global strongs_dfs
    base = Path(Path(__file__).parent / "..\\external_sources\\byzantine-majority-text-master\\csv-unicode\\strongs\\with-parsing")
    # Makes list of all csv files in folder: strongs_dfs = [pd.read_csv(file) for file in folder_path.glob("*.csv")]
    strongs_dfs = [
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

def load_test_parsed_strongs_dfs():
    global strongs_dfs
    strongs_dfs = [
        pd.read_csv(Path(Path(__file__).parent / "testing\\Test Matthew.csv"))
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
    # Must be run with load_rp_book_abbrevs and load_parsed_strongs_dfs
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
    for df in strongs_dfs:
        for _, row in df.iterrows():
            book = rp_book_abbrevs[book_counter]
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
    # Must be run with load_rp_book_abbrevs and load_parsed_strongs_dfs
    cursor.execute('DROP TABLE IF EXISTS pos_abbrevs')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS pos_abbrevs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   abbrev VARCHAR(45) UNIQUE,
                   count INTEGER NOT NULL DEFAULT 1,
                   example_code VARCHAR(45)
                   )''')
    
    book_counter = 0
    for df in strongs_dfs:
        for _, row in df.iterrows():
            book = rp_book_abbrevs[book_counter]
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
    # Must be run with load_rp_book_abbrevs and load_parsed_strongs_dfs
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
    for df in strongs_dfs:
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

def make_word_info(cursor):
    # Must be run with load_strongs_dfs
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
    for df in strongs_dfs:
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
    # Must be run with load_rp_book_abbrevs and load_parsed_strongs_dfs
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
                   rp_description VARCHAR(45),
                   rp_kai_incrasis VARCHAR(45),
                   rp_extra VARCHAR(45)
                   )''')

    book_counter = 0
    for df in strongs_dfs:
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
                               rp_person, rp_indeclinable, rp_description, rp_kai_incrasis, rp_extra) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
                               ON CONFLICT(word) DO UPDATE SET count = count + excluded.count
                               ''',
                               (word, count, str_num, code, rp_pos, rp_dict["gender"], rp_dict["number"], rp_dict["word_case"], rp_dict["tense"], rp_dict["type"], rp_dict["voice"],
                                rp_dict["mood"], rp_dict["person"], rp_dict["indeclinable"], rp_dict["description"], rp_dict["kai_incrasis"], rp_dict["extra"])
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
    query = '''
        SELECT * FROM parsed_word_info
        WHERE word = 'Unknown'
        OR rp_code = 'Unknown'
        OR rp_pos = 'Unknown'
        OR rp_gender = 'Unknown'
        OR rp_number = 'Unknown'
        OR rp_word_case = 'Unknown'
        OR rp_tense = 'Unknown'
        OR rp_type = 'Unknown'
        OR rp_voice = 'Unknown'
        OR rp_mood = 'Unknown'
        OR rp_person = 'Unknown'
        OR rp_indeclinable = 'Unknown'
        OR rp_description = 'Unknown'
        OR rp_kai_incrasis = 'Unknown'
        OR rp_extra = 'Unknown' ORDER BY rp_code ASC;
    '''
    df = pd.read_sql_query(query, conn)
    df.to_csv(Path(__file__).parent / "..\\output\\unknown_words.csv", index=False, encoding="utf-8-sig")

def make_parsed_word_instances(cursor):
    # Must be run with load_rp_book_abbrevs and load_parsed_strongs_dfs
    # Make sure that make_rp_code_info, make_rp_code_trait_tables, and make_parsed_word_info have been run before

    cursor.execute('DROP TABLE IF EXISTS parsed_word_instances')

    cursor.execute('''CREATE TABLE IF NOT EXISTS parsed_word_instances (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   info_id INTEGER,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   FOREIGN KEY (info_id) REFERENCES word_info(id)
                   )''')

    book_counter = 0
    for df in strongs_dfs:
        for _, info_row in df.iterrows():
            book = rp_book_abbrevs[book_counter]
            chapter = int(info_row["chapter"])
            verse = int(info_row["verse"])
            text = info_row["text"]
            words = text.split()
            word_index = 0
            i = 2
            while i < len(words):
                word = words[i - 2]
                
                cursor.execute('SELECT id FROM parsed_word_info WHERE word = ?', (word,))
                result = cursor.fetchone()
                word_id = -1
                if result:
                    word_id = result[0]
                else:
                    raise ValueError("ERROR in make_parsed_word_instances(cursor): word_info word key should be unique")
                cursor.execute('''
                            INSERT INTO parsed_word_instances (info_id, book, chapter, verse, word_index)
                            VALUES (?, ?, ?, ?, ?)
                            ''',
                            (word_id, book, chapter, verse, word_index)
                            )
                word_index += 1

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
    for df in strongs_dfs:
        for _, row in df.iterrows():
            book = rp_book_abbrevs[book_counter]
            chapter = int(row["chapter"])
            verse = int(row["verse"])
            text = row["text"]
            words = text.split()
            word_index = 0
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
                   FOREIGN KEY (info_id) REFERENCES word_info(id)
                   )
                   '''
                )

    book_counter = 0
    for df in strongs_dfs:
        for _, row in df.iterrows():
            book = rp_book_abbrevs[book_counter]
            chapter = int(row["chapter"])
            verse = int(row["verse"])
            text = row["text"]
            words = text.split()
            word_index = 0
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

def test_kjv_word_instances(cursor):
    # Query data
    cursor.execute('SELECT info_id, book, chapter, verse, word_index FROM strongs_word_instances')
    word_rows = cursor.fetchall()

    # Write the results to a text file
    with open('../output/strongs_word_instances.txt', 'w', encoding='utf-8') as out_file:
        for row in word_rows:
            out_file.write(f"{row}\n")


def make_word_classification(conn):
    df = pd.read_sql_query('''
                           SELECT 
                           ins.book, ins.chapter, ins.verse, ins.word_index,
                           inf.word, inf.count, inf.str_num, inf.rp_code, inf.rp_pos,
                           inf.rp_gender, inf.rp_number, inf.rp_word_case, inf.rp_tense, inf.rp_type, inf.rp_voice, inf.rp_mood,
                           inf.rp_person, inf.rp_indeclinable, inf.rp_description, inf.rp_kai_incrasis, inf.rp_extra
                   FROM parsed_word_instances ins
                   JOIN parsed_word_info inf
                   ON ins.info_id = inf.id''', conn
                   )

    # Export DataFrame to CSV (no index column)
    df.to_csv(Path(__file__).parent / "..\\output\\word_classification.csv", index=False, encoding="utf-8-sig")
    

def main():
    # Connect to a database (or create it)
    conn = sqlite3.connect('WordGuide.db')
    cursor = conn.cursor()

    # These 2 are necessary to run make_word_info and make_strongs_word_instances
    # load_rp_book_abbrevs()
    # load_parsed_strongs_dfs()

    # Make/update tables
    # make_rp_code_info(conn)
    # test_rp_code_info(conn)

    # Make/update tables
    # make_rp_code_trait_tables(cursor, conn)
    # test_rp_code_trait_tables(conn)

    # Make/update tables
    # make_parsed_word_info(cursor)
    # test_parsed_word_info(conn)

    # Make/update tables
    # make_parsed_word_instances(cursor)
    # test_parsed_word_instances(conn)

    make_word_classification(conn)
    
    # make_articles(conn)
    # test_article(cursor)



    # Always close the connection
    conn.commit()
    conn.close()


main()
