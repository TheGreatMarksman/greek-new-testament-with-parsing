import sqlite3
import unicodedata
import re
from collections import defaultdict
import pandas as pd
from pathlib import Path
import os

# GitHub Repo for Robinson-Pierpont files: https://github.com/byztxt/byzantine-majority-text
# GitHub Repo for SBLGNT files: https://github.com/LogosBible/SBLGNT
# Link to the grammar tables: https://en.wiktionary.org/wiki/Appendix:Ancient_Greek_grammar_tables
# Used info from https://en.wikipedia.org/wiki/Beta_Code


# GLOBALS

book_abbrevs = ["MAT", "MAR", "LUK", "JOH", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", 
         "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAM", 
         "1PE", "2PE", "1JO", "2JO", "3JO", "JUD", "REV"]


# TEST FUNCTIONS

def print_matched_indexes(normal_words, pericope_words):
    normal_list = normal_words.split(" ")
    pericope_list = pericope_words.split(" ")
    matched_indexes = [None] * len(normal_list)
    used_indexes = []
    highest_matched_index = -1
    for i in range(0, len(pericope_list)):
        if not used_indexes:
            curr_position = 0
        else:
            curr_position = highest_matched_index + 1
        if curr_position < len(normal_list):
            try:
                match_index = normal_list[curr_position:].index(pericope_list[i]) + curr_position
            except ValueError:
                match_index = -1
            if match_index != -1:
                # print(f"index {match_index} elem {normal_list[match_index]} {pericope_list[i]}")
                matched_indexes[match_index] = pericope_list[i]
                used_indexes.append(match_index)
                if match_index > highest_matched_index:
                    highest_matched_index = match_index
    print(matched_indexes)

def test_words_and_disp_words(conn):
    word_df = pd.read_csv((Path(__file__).parent / "testing" / "words_and_disp_words.csv").resolve(), skiprows=[0], usecols=[20, 21])
    word_df.columns = ['word', 'word_index']
    word_df.to_sql("test_words", conn, if_exists='replace', index=False)

    disp_df = pd.read_csv((Path(__file__).parent / "testing" / "words_and_disp_words.csv").resolve(), skiprows=[0], usecols=[22, 23, 24, 25])
    disp_df.columns = ['word', 'word_index', 'word_order', 'secondary_word_order']
    disp_df.to_sql("test_disp_words", conn, if_exists='replace', index=False)
    

    output_df = pd.read_sql_query('''
        SELECT word, word_index, disp_word FROM
        (
            SELECT w.word, w.word_index, dw.word AS disp_word, COALESCE(dw.word_order, w.word_index) AS final_word_order, dw.secondary_word_order FROM test_words w
                                LEFT JOIN test_disp_words dw ON w.word = disp_word AND w.word_index = dw.word_index
            
            UNION
                                    
            SELECT w.word, w.word_index, dw.word AS disp_word, COALESCE(dw.word_order, w.word_index) AS final_word_order, dw.secondary_word_order FROM test_disp_words dw
                                LEFT JOIN test_words w ON disp_word = w.word AND dw.word_index = w.word_index

        )
        WHERE word IS NOT NULL OR disp_word IS NOT NULL
        ORDER BY final_word_order, secondary_word_order
                                  
    ''', conn)

    output_df.to_csv(Path(__file__).parent / "testing" / "words_and_disp_words_output.csv", index=False, encoding="utf-8-sig")

def test_alt_words_and_disp_words(conn):
    word_df = pd.read_csv((Path(__file__).parent / "testing" / "words_and_disp_words.csv").resolve(), skiprows=[0], usecols=[0, 1])
    word_df.columns = ['word', 'word_index']
    word_df.to_sql("test_words", conn, if_exists='replace', index=False)

    disp_df = pd.read_csv((Path(__file__).parent / "testing" / "words_and_disp_words.csv").resolve(), skiprows=[0], usecols=[2, 3])
    disp_df.columns = ['word', 'word_index']
    disp_df.to_sql("test_disp_words", conn, if_exists='replace', index=False)
    

    output_df = pd.read_sql_query('''
        SELECT word, word_index, disp_word FROM
        (
            SELECT w.word, w.word_index, dw.word AS disp_word, COALESCE(dw.word_order, w.word_index) AS final_word_order FROM test_words w
                                LEFT JOIN test_disp_words dw ON w.word = disp_word AND w.word_index = dw.word_index
            
            UNION
                                    
            SELECT w.word, w.word_index, dw.word AS disp_word, COALESCE(dw.word_order, w.word_index) AS final_word_order FROM test_disp_words dw
                                LEFT JOIN test_words w ON disp_word = w.word AND dw.word_index = w.word_index

        )
        WHERE word IS NOT NULL OR disp_word IS NOT NULL
        ORDER BY final_word_order, word_index
                                  
    ''', conn)

    output_df.to_csv(Path(__file__).parent / "testing" / "alt_words_and_disp_words_output.csv", index=False, encoding="utf-8-sig")




# HELPER FUNCTIONS

# removes ? which denotes the start of paragraphs
# removes variants (in between {})
# and ensures words at the end and beginning of lines aren't stuck together
def clean_betacode(text):    
    lines = text.splitlines()
    joined = " ".join(line.strip() for line in lines if line.strip())
    cleaned = joined.replace("?", "")
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

# removes ¶ which denotes the start of paragraphs
# and ensures words at the end and beginning of lines aren't stuck together
def clean_unicode(text):  
    lines = text.splitlines()
    joined = " ".join(line.strip() for line in lines if line.strip())
    cleaned = joined.replace("¶", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def simplify_betacode(word, remove_capitals = False, diacritic_list = None, punctuation_list = None):
    if remove_capitals:
        word = word.replace("*", "")
    if diacritic_list is not None:
        for key in diacritic_list:
            word = word.replace(key, "")
    if punctuation_list is not None:
        for key in punctuation_list:
            word = word.replace(key, "")
    return word

def simplify_unicode(word, diacritic_list = None, punctuation_list = None):
    word = unicodedata.normalize('NFD', word)
    if diacritic_list is not None:
        for key in diacritic_list:
            word = word.replace(key, "")
    if punctuation_list is not None:
        for key in punctuation_list:
            word = word.replace(key, "")
    word = unicodedata.normalize('NFC', word)
    return word

def betacode_to_unicode(old_word, alphabet_map, diacritic_map = None, punctuation_map = None, has_capitals = False):
    letters = [""] * len(old_word)
    
    old_word_list = list(old_word)

    if has_capitals:
        star_index = old_word.find('*')
        if star_index != -1:
            capitalize(old_word_list, star_index, alphabet_map)

    i = 0
    while i < len(old_word_list):
        char = None
        char = alphabet_map.get(old_word_list[i])
        if char is not None:
            if is_last_letter(old_word_list, i, alphabet_map) and char == "σ":
                char = "ς"
        else:
            if diacritic_map is not None:
                char = diacritic_map.get(old_word_list[i])
            if punctuation_map is not None and char is None:
                char = punctuation_map.get(old_word_list[i])                    
                    
            if char is None:
                char = "!" # Test to see if any errors
        letters[i] = char
        i += 1
    word = ''.join(letters)
    word = re.sub(r"\s+", "", word)
    word = unicodedata.normalize('NFC', word)
    return word
    

def is_consonant(char):
    vowels = "aeiouAEIOU"
    return char.isalpha() and char not in vowels

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

def is_after_consonant(word, index, alphabet_map):
    for i in range(index - 1, -1, -1):
        if word[i] in alphabet_map:
            if is_consonant(word[i]):
                return True
            return False
    raise ValueError("ERROR IN is_after_consonant: NO LETTERS BEFORE INDEX")

def decode_rp_code(code, info_df, long_trait_df, trait_table_dfs):
    rp_dict = defaultdict(lambda: "")
    rp_pos = "!"
    code = code.replace("{", "")
    code = code.replace("}", "")
    code_parts = code.split("-")
    info  = "".join(code_parts[1:])
    possible_traits = []
    trait_code_list = []

    # All possible trait sequences for this part of speech
    matching_info_df = info_df[info_df['abbreviation'] == code_parts[0]]

    index_row = matching_info_df.iterrows()

    if not index_row:
        print(code_parts[0])

    for _, info_row in index_row:
        long_trait_codes_set = set()
        # Get all values from the info_row as a set of strings
        info_values = set(map(str, info_row.values))

        # Find trait rows where origin_table matches any value in info_row
        matching_traits = long_trait_df[long_trait_df['origin_table'].astype(str).isin(info_values)]

        long_trait_codes_set.update(matching_traits['code'])

        # making an element of trait_code_list, a list of lists of abbreviations for traits
        trait_codes = []
        j = 0
        while j < len(info):
            matched = False
            for sub in long_trait_codes_set:
                if info.startswith(sub, j):
                    trait_codes.append(sub)
                    j += len(sub)
                    matched = True
                    break
            if not matched:
                trait_codes.append(info[j])
                j += 1
        num_traits = int(info_row["num traits"])
        if len(trait_codes) != num_traits:
            continue
        # Append to trait_code_list after above statement to prevent adding an invalid set of codes
        trait_code_list.append(trait_codes)
        rp_pos = info_row['pos']
        traits = []
        for j in range(1, num_traits + 1):
            traits.append(info_row["trait " + str(j)])
        possible_traits.append(traits)
        # with open(Path(__file__).parent / ".." / "output" "long_trait_code_info.txt", 'a', encoding='utf-8') as out_file:
        #     out_file.write(f"{code} {info} {long_trait_codes} {trait_codes}\n")
        
    for j in range(0, len(possible_traits)):
        valid = True
        if len(trait_code_list[j]) != len(possible_traits[j]):
            raise ValueError(f"ERROR in decode_rp_code: different lengths - trait_code_list[j]: {trait_code_list[j]} possible_traits[j]: {possible_traits[j]}")
        for k in range(0, len(possible_traits[j])):
            possible_trait_df = trait_table_dfs[possible_traits[j][k]]
            matching_trait_df = possible_trait_df[possible_trait_df['Abbreviation'] == trait_code_list[j][k]]

            if not matching_trait_df.empty:
                rp_dict[possible_traits[j][k]] = matching_trait_df.iloc[0][possible_traits[j][k]]
            else:
                rp_dict[possible_traits[j][k]] = "Unknown"
                valid = False
            
                # with open((Path(__file__).parent / ".." / "output" / "testing" / "unknown_traits_log.txt").resolve(), 'a', encoding='utf-8') as out_file:
                #     out_file.write(f"{code} {trait_code_list[j][k]} {trait_code_list} {possible_traits[j][k]} {possible_traits} \n {possible_trait_df} \n")
        if valid:
            # with open(Path(__file__).parent / ".." / "output" / "known_traits_log.txt", 'a', encoding='utf-8') as out_file:
            #         out_file.write(f"{code} {info} {trait_code_list} {possible_traits}\n")
            for k, v in rp_dict.items():
                if str(v).lower() == "unknown":
                    rp_dict[k] = ""
            break

    return { "pos": rp_pos, "dict": rp_dict }
                            

def find_row_index_of_trait(trait, rows, trait_index):
    # print(f"rows {rows} trait {trait}")
    for i in range(len(rows)):
        if trait == rows[i][trait_index]:
            return i
    return None

# converts to standard polytonic form - no capitals unless word is a proper noun, keep accents but grave accents turned into accute
def to_std_poly_form(word, is_proper_noun = False, diacritic_map = None):
    if is_proper_noun:
        word = word[0] + word[1:].lower()
    else:
        word = word.lower()
    # Decompose characters into base + combining marks
    decomposed = unicodedata.normalize("NFD", word)
    replaced = decomposed.replace(diacritic_map["Grave accent"], diacritic_map["Acute accent"])
    # Recompose characters
    return unicodedata.normalize("NFC", replaced)

# converts to monotonic uppercase form - all caps, sigma is converted to C, no diacritics
def to_mono_UC_form(word):
    if word == "Disputed word":
        return ""
    word = simplify_unicode(word, False)
    word = word.upper()
    word = word.replace('Σ', 'C')
    return word

# DATABASE FUNCTIONS

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
    
    base = (Path(__file__).parent / ".." / "external_sources" / "byzantine-majority-text-master" / "source" / "ccat").resolve()
    book_file_paths = [
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

    # For Testing
    # book_file_paths = [(Path(__file__).parent / "testing" / "test matthew 1 2.txt").resolve()]

    total_word_index = 1
    book_counter = 0
    for file_path in book_file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            contents = file.read()
            cleaned = clean_betacode(contents)
            words = cleaned.split(" ")
            book = book_abbrevs[book_counter]
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
        book_counter += 1

def test_betacode_bible(conn):
    df = pd.read_sql_query('SELECT * FROM betacode_bible', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "betacode_bible.csv").resolve(), index=False, encoding="utf-8-sig")


def make_unicode_bible(cursor):
    cursor.execute('DROP TABLE IF EXISTS unicode_bible')

    cursor.execute('''CREATE TABLE IF NOT EXISTS unicode_bible (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER
                   )''')
    
    # Skips row 45 because that contains ς which only occurs at the end of words - the program adds it later
    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_alphabet.csv").resolve(), usecols=[0, 1], skiprows=[45])
    df.columns = ['letter', 'betacode']
    alphabet_map = dict(zip(df["betacode"], df["letter"]))

    # Wikipedia uses — 	and _ for unicode and beta code respectively, byzantine-majority-text uses - for both as does this program
    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_punctuation.csv").resolve(), usecols=[0, 1])
    df.columns = ['punctuation', 'betacode']
    punctuation_map = dict(zip(df["betacode"], df["punctuation"]))

    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_diacritics.csv").resolve(), usecols=[0, 1])
    # Ignores last row which contains the coding for the breve, which is not in the ancient text
    df = df[:-1]
    df.columns = ['diacritic', 'betacode']
    diacritic_map = dict(zip(df["betacode"], df["diacritic"]))


    cursor.execute("SELECT word, book, chapter, verse, word_index, total_word_index FROM betacode_bible")

    rows = cursor.fetchall()
    for row in rows:
        old_word = row[0]
        word = betacode_to_unicode(old_word, alphabet_map, diacritic_map, punctuation_map, True)

        book = row[1]
        chapter = row[2]
        verse = row[3]
        word_index = row[4]
        total_word_index = row[5]

        cursor.execute('''INSERT INTO unicode_bible (word, book, chapter, verse, word_index, total_word_index)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''',
                        (word, book, chapter, verse, word_index, total_word_index)
                    )

def test_unicode_bible(conn):
    df = pd.read_sql_query('SELECT * FROM unicode_bible', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "unicode_bible.csv").resolve(), index=False, encoding="utf-8-sig")

def make_external_unicode_bible(cursor):
    cursor.execute('DROP TABLE IF EXISTS external_unicode_bible')

    cursor.execute('''CREATE TABLE IF NOT EXISTS external_unicode_bible (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER
                   )''')
    
    base = Path(Path(__file__).parent / ".." / "external_sources" / "byzantine-majority-text-master" / "csv-unicode" / "ccat" / "no-variants")
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

    book_counter = 0
    total_word_index = 1
    for df in book_dfs:
        for _, row in df.iterrows():
            book = book_abbrevs[book_counter]
            chapter = int(row["chapter"])
            verse = int(row["verse"])
            text = clean_unicode(row["text"])
            words = text.split()
            word_index = 1
            for word in words:
                cursor.execute('''
                               INSERT INTO external_unicode_bible (word, book, chapter, verse, word_index, total_word_index)
                               VALUES (?, ?, ?, ?, ?, ?)
                               ''',
                               (word, book, chapter, verse, word_index, total_word_index)
                            )
                word_index += 1
                total_word_index += 1
                
        book_counter += 1

def test_external_unicode_bible(conn):
    df = pd.read_sql_query('SELECT * FROM external_unicode_bible', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "external_unicode_bible.csv").resolve(), index=False, encoding="utf-8-sig")

def make_word_instances(cursor):
    cursor.execute('DROP TABLE IF EXISTS word_instances')

    cursor.execute('''CREATE TABLE IF NOT EXISTS word_instances (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   mono_LC VARCHAR(45),
                   unicode VARCHAR(45),
                   std_poly_LC VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER
                   )''')
    
    # Skips row 45 because that contains ς which only occurs at the end of words - the program adds it later
    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_alphabet.csv").resolve(), usecols=[0, 1], skiprows=[45])
    df.columns = ['letter', 'betacode']
    alphabet_map = dict(zip(df["betacode"], df["letter"]))

    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_punctuation.csv").resolve(), usecols=[0, 1])
    df.columns = ['punctuation', 'betacode']
    punctuation_map = dict(zip(df["betacode"], df['punctuation']))

    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_diacritics.csv").resolve(), usecols=[0, 1, 2])
    # Ignores last row which contains the coding for the breve, which is not in the ancient text
    df = df[:-1]
    df.columns = ['diacritic', 'betacode', 'name']
    diacritic_map =  dict(zip(df["betacode"], df['diacritic']))

    name_diacritic_map =  dict(zip(df["name"], df['diacritic']))

    cursor.execute("SELECT word, book, chapter, verse, word_index, total_word_index FROM betacode_bible")
    rows = cursor.fetchall()

    total_word_index = 1

    for row in rows:
        # Get rid of punctuation
        word = simplify_betacode(row[0], False, None, punctuation_map.keys())

        # Get rid of diacritics and capitals - also do .lower() because the letters in parsed_word_info are lowercase,
        # whereas betacode_bible letters have * to denote a capital
        mono_LC = simplify_betacode(word, True, diacritic_map.keys()).lower()

        unicode = betacode_to_unicode(word, alphabet_map, diacritic_map, None, True)

        std_poly_LC = to_std_poly_form(unicode, False, name_diacritic_map)

        book = row[1]
        chapter = row[2]
        verse = row[3]
        word_index = row[4]
        total_word_index = row[5]

        cursor.execute('''
                    INSERT INTO word_instances (word, mono_LC, unicode, std_poly_LC, book, chapter, verse, word_index, total_word_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (word, mono_LC, unicode, std_poly_LC, book, chapter, verse, word_index, total_word_index)
                    )
    
def test_word_instances(conn):
    df = pd.read_sql_query('SELECT * FROM word_instances', conn)
    df.to_csv(Path(__file__).parent / ".." / "output" / "word_instances.csv", index=False, encoding="utf-8-sig")

# Accented, capitalized
def make_old_source_word_info(cursor):
    cursor.execute('DROP TABLE IF EXISTS source_word_info')

    cursor.execute('''CREATE TABLE IF NOT EXISTS source_word_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   parsed_id INTEGER,
                   word VARCHAR(45) UNIQUE,
                   mono_LC VARCHAR(45),
                   unicode VARCHAR(45),
                   count INTEGER,
                   FOREIGN KEY (parsed_id) REFERENCES parsed_word_info(id)
                   )''')
    
    # Skips row 45 because that contains ς which only occurs at the end of words - the program adds it later
    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_alphabet.csv").resolve(), usecols=[0, 1], skiprows=[45])
    df.columns = ['letter', 'betacode']
    alphabet_map = dict(zip(df["betacode"], df["letter"]))

    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_punctuation.csv").resolve(), usecols=[0, 1])
    df.columns = ['punctuation', 'betacode']
    punctuation_map = dict(zip(df["betacode"], df['punctuation']))

    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_diacritics.csv").resolve(), usecols=[0, 1])
    # Ignores last row which contains the coding for the breve, which is not in the ancient text
    df = df[:-1]
    df.columns = ['diacritic', 'betacode']
    diacritic_map =  dict(zip(df["betacode"], df['diacritic']))

    # Creates index on word column in parsed_word_info since it will be commonly queried
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parsed_word_info_word ON parsed_word_info(word)")

    cursor.execute("SELECT word FROM betacode_bible")
    rows = cursor.fetchall()

    for row in rows:
        # Get rid of punctuation
        word = simplify_betacode(row[0], False, punctuation_map)
        parsed_id = -1

        # Get rid of diacritics and capitals - also do .lower() because the letters in parsed_word_info are lowercase,
        # whereas betacode_bible letters have * to denote a capital
        mono_LC = simplify_betacode(word, True, diacritic_map).lower()

        unicode = betacode_to_unicode(word, alphabet_map, diacritic_map, None, True)

        cursor.execute("SELECT id FROM parsed_word_info WHERE word = ?", (mono_LC,))
        parsed_row = cursor.fetchone()
        if parsed_row:
            parsed_id = parsed_row[0]
        else:
            raise ValueError(f"ERROR in make_source_word_info: {mono_LC} should have matching word in parsed_word_info table")
        count = 1
        cursor.execute('''
                    INSERT INTO source_word_info (parsed_id, word, mono_LC, unicode, count)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (word) DO UPDATE SET count = count + excluded.count
                    ''',
                    (parsed_id, word, mono_LC, unicode, count)
                    )
            

def test_old_source_word_info(conn):
    df = pd.read_sql_query('SELECT * FROM source_word_info', conn)
    df.to_csv(Path(__file__).parent / ".." "output" / "source_word_info.csv", index=False, encoding="utf-8-sig")


def make_old_word_instances(cursor):
    cursor.execute('DROP TABLE IF EXISTS word_instances')

    cursor.execute('''CREATE TABLE IF NOT EXISTS word_instances (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   source_id INTEGER,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER,
                   FOREIGN KEY (source_id) REFERENCES source_word_info(id)
                   )''')
    
    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_punctuation.csv").resolve(), usecols=["Beta Code"])
    df.columns = ['betacode']
    punctuation_map = set(df["betacode"])

    # Creates index on word column in source_word_info since it will be commonly queried
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_word_info_word ON source_word_info(word)")

    cursor.execute("SELECT word, book, chapter, verse, word_index, total_word_index FROM betacode_bible")

    total_word_index = 1

    rows = cursor.fetchall()
    for row in rows:
        word = simplify_betacode(row[0], False, None, punctuation_map)
        book = row[1]
        chapter = row[2]
        verse = row[3]
        word_index = row[4]
        total_word_index = row[5]

        source_id = -1
        cursor.execute("SELECT id FROM source_word_info WHERE word = ?", (word,))

        source_row = cursor.fetchone()
        if source_row:
            source_id = source_row[0]
        else:
            raise ValueError(f"ERROR in make_word_instances: {word} should have matching word in parsed_word_info table")
        
        cursor.execute('''
                        INSERT INTO word_instances (source_id, book, chapter, verse, word_index, total_word_index)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''',
                        (source_id, book, chapter, verse, word_index, total_word_index)
                        )


def test_old_word_instances(conn):
    df = pd.read_sql_query('SELECT * FROM word_instances', conn)
    df.to_csv(Path(__file__).parent / ".." / "output" / "word_instances.csv", index=False, encoding="utf-8-sig")

def make_long_trait_codes():
    new_dfs = []

    csv_dir = (Path(__file__).parent / "tools" / "rp_code_trait_tables").resolve()
    for csv_file in csv_dir.glob("*.csv"):
        df = pd.read_csv(csv_file)
        new_long_traits = df[df['Abbreviation'].astype(str).str.len() > 1].copy()

        name = csv_file.stem

        new_long_traits['origin_table'] = name

        new_long_traits.columns = ['trait', 'code', 'origin_table']

        new_dfs.append(new_long_traits)
    
    long_trait_codes = pd.concat(new_dfs, ignore_index=True)
    long_trait_codes.to_csv((Path(__file__).parent / "tools" / "long_trait_codes.csv").resolve())

def test_make_parsed_word_info(cursor):
    base = (Path(__file__).parent / ".." / "external_sources" / "byzantine-majority-text-master" / "source" / "Strongs").resolve()
    book_file_paths = [
        base / "01_MAT.bp5",   # Matthew
        base / "02_MAR.bp5",   # Mark
        base / "03_LUK.bp5",   # Luke
        base / "04_JOH.bp5",   # John
        base / "05_ACT.bp5",   # Acts
        base / "06_ROM.bp5",   # Romans
        base / "07_1CO.bp5",   # 1 Corinthians
        base / "08_2CO.bp5",   # 2 Corinthians
        base / "09_GAL.bp5",   # Galatians
        base / "10_EPH.bp5",   # Ephesians
        base / "11_PHP.bp5",   # Philippians
        base / "12_COL.bp5",   # Colossians
        base / "13_1TH.bp5",   # 1 Thessalonians
        base / "14_2TH.bp5",   # 2 Thessalonians
        base / "15_1TI.bp5",   # 1 Timothy
        base / "16_2TI.bp5",   # 2 Timothy
        base / "17_TIT.bp5",   # Titus
        base / "18_PHM.bp5",   # Philemon
        base / "19_HEB.bp5",   # Hebrews
        base / "20_JAM.bp5",   # James
        base / "21_1PE.bp5",   # 1 Peter
        base / "22_2PE.bp5",   # 2 Peter
        base / "23_1JO.bp5",   # 1 John
        base / "24_2JO.bp5",   # 2 John
        base / "25_3JO.bp5",   # 3 John
        base / "26_JUD.bp5",   # Jude
        base / "27_REV.bp5"    # Revelation
    ]

    # For Testing
    book_file_paths = [(Path(__file__).parent / "testing" / "test mark 1 7.txt").resolve()]

    # Skips row 20 because that contains ς which only occurs at the end of words - the program adds it later
    alpha_df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_alphabet.csv").resolve(), usecols=[2, 3], skiprows=[20], nrows=26)
    alpha_df.columns = ['letter', 'betacode']
    alphabet_map = dict(zip(alpha_df["betacode"], alpha_df["letter"]))

    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_diacritics.csv").resolve(), usecols=[0, 2])
    # Ignores last row which contains the coding for the breve, which is not in the ancient text
    df = df[:-1]
    df.columns = ['diacritic', 'name']
    diacritic_map =  dict(zip(df["name"], df['diacritic']))
    diacritic_list = df['diacritic'].tolist()

    info_df = pd.read_csv((Path(__file__).parent / "tools" / "rp_code_info.csv").resolve())
    long_trait_df = pd.read_csv((Path(__file__).parent / "tools" / "long_trait_codes.csv").resolve())

    # Making a df for every rp code trait table
    trait_table_path = (Path(__file__).parent / "tools" / "rp_code_trait_tables").resolve()
    trait_table_files = [file for file in os.listdir(trait_table_path) if file.endswith('.csv')]
    trait_table_dfs = {}
    for file in trait_table_files:
        file_path = os.path.join(trait_table_path, file)
        file_name = os.path.splitext(file)[0]
        trait_table_dfs[file_name] = pd.read_csv(file_path, dtype=str)

    # with open((Path(__file__).parent / ".." / "output" / "testing" / "unknown_traits_log.txt").resolve(), 'w', encoding='utf-8') as out_file:
    #     out_file.write("HEY HEY\n")

    book_counter = 1
    for file_path in book_file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            contents = file.read()
            # Split by any whitespace (spaces, tabs, newlines)
            words = re.split(r'\s+', contents)
            # Remove any empty strings
            words = [w for w in words if w]

            book = book_abbrevs[book_counter]
            chapter = 1
            verse = 1
            word_index = 1

            i = 2
            while i < len(words):
                word = words[i-2]
                # chapter and verse is now in form Chapter.Verse
                if len(word) == 5 and (word.replace(".", "")).isdigit() and word[2] == ".":
                    i += 1
                    last_chapter = chapter
                    last_verse = verse
                    chapter = int(word[:2])
                    verse = int(word[3:])
                    if chapter != last_chapter or verse != last_verse:
                        word_index = 1
                else:
                    unicode = betacode_to_unicode(word, alphabet_map)

                    try:
                        str_num = int(words[i - 1])
                    except ValueError:
                        str_num = -1
                    
                    is_proper_noun = False
                    std_poly_form = None
                    std_poly_LC = None

                    cursor.execute("SELECT unicode FROM word_instances WHERE book = ? AND chapter = ? AND verse = ? AND word_index = ?", (book, chapter, verse, word_index))
                    instance_row = cursor.fetchone()
                    if instance_row:
                        std_poly_form = to_std_poly_form(instance_row[0], is_proper_noun, diacritic_map)
                        std_poly_LC = std_poly_form.lower()
                        test_poly = simplify_unicode(std_poly_LC, diacritic_list)
                        if unicode != test_poly:
                            std_poly_LC = "!!!"
                            std_poly_form = test_poly

                    if std_poly_form is None:
                        print(f"NO MATCH: book {book} chapter {chapter} verse {verse} word_index {word_index}")
                    
                    word_index += 1

                    i += 3

def make_parsed_word_info(cursor):
    cursor.execute('DROP TABLE IF EXISTS parsed_word_info')
    
    # pos means part of speech, number means singular, plural etc.
    cursor.execute('''CREATE TABLE IF NOT EXISTS parsed_word_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   unicode VARCHAR(45),
                   std_poly_form VARCHAR(45),
                   std_poly_LC VARCHAR(45),
                   str_num INTEGER,
                   rp_code VARCHAR(45),
                   rp_alt_code VARCHAR(45),
                   rp_pos VARCHAR(45),
                   rp_gender VARCHAR(45),
                   rp_alt_gender VARCHAR(45),
                   rp_number VARCHAR(45),
                   rp_word_case VARCHAR(45),
                   rp_alt_word_case VARCHAR(45),
                   rp_tense VARCHAR(45),
                   rp_type VARCHAR(45),
                   rp_voice VARCHAR(45),
                   rp_mood VARCHAR(45),
                   rp_alt_mood VARCHAR(45),
                   rp_person VARCHAR(45),
                   rp_indeclinable VARCHAR(45),
                   rp_why_indeclinable VARCHAR(45),
                   rp_kai_crasis VARCHAR(45),
                   rp_attic_greek_form VARCHAR(45)
                   )'''
    )

    base = (Path(__file__).parent / ".." / "external_sources" / "byzantine-majority-text-master" / "source" / "Strongs").resolve()
    book_file_paths = [
        base / "01_MAT.bp5",   # Matthew
        base / "02_MAR.bp5",   # Mark
        base / "03_LUK.bp5",   # Luke
        base / "04_JOH.bp5",   # John
        base / "05_ACT.bp5",   # Acts
        base / "06_ROM.bp5",   # Romans
        base / "07_1CO.bp5",   # 1 Corinthians
        base / "08_2CO.bp5",   # 2 Corinthians
        base / "09_GAL.bp5",   # Galatians
        base / "10_EPH.bp5",   # Ephesians
        base / "11_PHP.bp5",   # Philippians
        base / "12_COL.bp5",   # Colossians
        base / "13_1TH.bp5",   # 1 Thessalonians
        base / "14_2TH.bp5",   # 2 Thessalonians
        base / "15_1TI.bp5",   # 1 Timothy
        base / "16_2TI.bp5",   # 2 Timothy
        base / "17_TIT.bp5",   # Titus
        base / "18_PHM.bp5",   # Philemon
        base / "19_HEB.bp5",   # Hebrews
        base / "20_JAM.bp5",   # James
        base / "21_1PE.bp5",   # 1 Peter
        base / "22_2PE.bp5",   # 2 Peter
        base / "23_1JO.bp5",   # 1 John
        base / "24_2JO.bp5",   # 2 John
        base / "25_3JO.bp5",   # 3 John
        base / "26_JUD.bp5",   # Jude
        base / "27_REV.bp5"    # Revelation
    ]

    # For Testing
    # book_file_paths = [(Path(__file__).parent / "testing" / "Test Parsed Matthew 26 Verse 45.txt").resolve()]

    # Skips row 20 because that contains ς which only occurs at the end of words - the program adds it later
    alpha_df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_alphabet.csv").resolve(), usecols=[2, 3], skiprows=[20], nrows=26)
    alpha_df.columns = ['letter', 'betacode']
    alphabet_map = dict(zip(alpha_df["betacode"], alpha_df["letter"]))

    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_diacritics.csv").resolve(), usecols=[0, 2])
    # Ignores last row which contains the coding for the breve, which is not in the ancient text
    df = df[:-1]
    df.columns = ['diacritic', 'name']
    diacritic_map =  dict(zip(df["name"], df['diacritic']))
    diacritic_list = df['diacritic'].tolist()

    info_df = pd.read_csv((Path(__file__).parent / "tools" / "rp_code_info.csv").resolve())
    long_trait_df = pd.read_csv((Path(__file__).parent / "tools" / "long_trait_codes.csv").resolve())

    # Making a df for every rp code trait table
    trait_table_path = (Path(__file__).parent / "tools" / "rp_code_trait_tables").resolve()
    trait_table_files = [file for file in os.listdir(trait_table_path) if file.endswith('.csv')]
    trait_table_dfs = {}
    for file in trait_table_files:
        file_path = os.path.join(trait_table_path, file)
        file_name = os.path.splitext(file)[0]
        trait_table_dfs[file_name] = pd.read_csv(file_path, dtype=str)

    # with open((Path(__file__).parent / ".." / "output" / "testing" / "unknown_traits_log.txt").resolve(), 'w', encoding='utf-8') as out_file:
    #     out_file.write("HEY HEY\n")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_word_instances ON word_instances(book, chapter, verse, word_index)")

    book_counter = 0
    for file_path in book_file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            contents = file.read()
            # Split by any whitespace (spaces, tabs, newlines)
            words = re.split(r'\s+', contents)
            # Remove any empty strings
            words = [w for w in words if w]

            book = book_abbrevs[book_counter]
            chapter = 1
            verse = 1
            word_index = 1

            i = 2
            while i < len(words):
                word = words[i-2]
                # chapter and verse is now in form Chapter.Verse
                if len(word) == 5 and (word.replace(".", "")).isdigit() and word[2] == ".":
                    i += 1
                    last_chapter = chapter
                    last_verse = verse
                    chapter = int(word[:2])
                    verse = int(word[3:])
                    if chapter != last_chapter or verse != last_verse:
                        word_index = 1
                else:
                    unicode = betacode_to_unicode(word, alphabet_map)

                    try:
                        str_num = int(words[i - 1])
                    except ValueError:
                        str_num = -1

                    code = words[i]
                    alt_code = None
                    decoding = decode_rp_code(code, info_df, long_trait_df, trait_table_dfs)
                    rp_pos = decoding["pos"]
                    rp_dict = decoding["dict"]

                    two_codes = False
                    # Check if there's a "γη 1093 {N-NSF} 1093 {N-VSF}" situation
                    if i + 2 < len(words) and "{" in words[i + 2]:
                        two_codes = True
                        alt_code = words[i+2]
                        alt_decoding = decode_rp_code(alt_code, info_df, long_trait_df, trait_table_dfs)
                        alt_rp_pos = alt_decoding["pos"]
                        alt_rp_dict = alt_decoding["dict"]
                        if rp_pos != alt_rp_pos:
                            rp_pos += ", " + alt_rp_pos
                        for key in alt_rp_dict:
                            if key in rp_dict:
                                if rp_dict[key] != alt_rp_dict[key]:
                                    rp_dict["alt_" + key] = alt_rp_dict[key]
                            else:
                                rp_dict[key] = alt_rp_dict[key]
                    
                    is_proper_noun = False
                    if rp_dict["why_indeclinable"] == "proper noun":
                        is_proper_noun = True
                    std_poly_form = None
                    std_poly_LC = None

                    cursor.execute("SELECT unicode FROM word_instances WHERE book = ? AND chapter = ? AND verse = ? AND word_index = ?", (book, chapter, verse, word_index))
                    instance_row = cursor.fetchone()
                    if instance_row:
                        std_poly_form = to_std_poly_form(instance_row[0], is_proper_noun, diacritic_map)
                        std_poly_LC = std_poly_form.lower()
                        test_poly = simplify_unicode(std_poly_LC, diacritic_list)
                        if unicode != test_poly:
                            std_poly_LC = "!!!"

                    cursor.execute('''
                                    INSERT INTO parsed_word_info (word, unicode, std_poly_form, std_poly_LC, str_num, rp_code, rp_alt_code, rp_pos, rp_gender, rp_alt_gender, rp_number,
                                   rp_word_case, rp_alt_word_case, rp_tense, rp_type, rp_voice, rp_mood, rp_alt_mood, rp_person, rp_indeclinable, rp_why_indeclinable, rp_kai_crasis,
                                   rp_attic_greek_form) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
                                    ''',
                                    (word, unicode, std_poly_form, std_poly_LC, str_num, code, alt_code, rp_pos, rp_dict["gender"], rp_dict["alt_gender"], rp_dict["number"], rp_dict["word_case"],
                                     rp_dict["alt_word_case"], rp_dict["tense"], rp_dict["type"], rp_dict["voice"], rp_dict["mood"], rp_dict["alt_mood"], rp_dict["person"],
                                     rp_dict["indeclinable"], rp_dict["why_indeclinable"], rp_dict["kai_crasis"], rp_dict["attic_greek_form"])
                                )
                    
                    word_index += 1

                    if two_codes:
                        i += 2

                    i += 3
        book_counter += 1


def test_parsed_word_info(conn):
    df = pd.read_sql_query('SELECT * FROM parsed_word_info', conn)
    df.to_csv(Path(__file__).parent / ".." / "output" / "parsed_word_info.csv", index=False, encoding="utf-8-sig")

def make_strongs_info(cursor):
    cursor.execute('DROP TABLE IF EXISTS strongs_info')

    cursor.execute('''CREATE TABLE IF NOT EXISTS strongs_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   str_num INTEGER,
                   def VARCHAR(45),
                   root_1 VARCHAR(45),
                   root_2 VARCHAR(45),
                   root_3 VARCHAR(45)
                   )''')
    
    df = pd.read_csv((Path(__file__).parent / ".." / "external_sources" / "Greek Strongs from Matthias Mueller 20250623.csv").resolve(),
                     usecols=[1, 2, 3, 11, 13, 15])
    df.columns = ['str_num', 'word', 'gloss', 'root_1', 'root_2', 'root_3']
    to_insert = []
    # print(f"gloss 1 {next(df.iterrows())['gloss']}")
    for _, row in df.iterrows():
        if row['word'] == "not used":
            continue
        try:

            definition = str(row['gloss']).split("KJV: ")[1]
            definition = re.split(r"See also:|Compare:|Root\(s\):", definition)[0].strip()
            definition.replace("+", "")
        except IndexError:
            definition = None
        to_insert.append((row['word'], row['str_num'], definition, row["root_1"], row['root_2'], row['root_3']))
    cursor.executemany('INSERT INTO strongs_info (word, str_num, def, root_1, root_2, root_3) VALUES (?, ?, ?, ?, ?, ?)', (to_insert))

def test_strongs_info(conn):
    df = pd.read_sql_query('SELECT * FROM strongs_info', conn)
    df.to_csv(Path(__file__).parent / ".." / "output" / "strongs_info.csv", index=False, encoding="utf-8-sig")

def make_pericope_words(cursor):
    cursor.execute('DROP TABLE IF EXISTS pericope_words')

    cursor.execute('''CREATE TABLE IF NOT EXISTS pericope_words (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   unicode VARCHAR(45),
                   std_poly_LC VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   )''')
    
    base = (Path(__file__).parent / ".." / "external_sources" / "byzantine-majority-text-master" / "source" / "ccat").resolve()
    book_file_paths = [
        base / "04a_PA.TXT",   # John 7:53-8:11 which is a pericope
        base / "05a_ACT24.TXT"    # Acts 24:6-8 which is a pericope
    ]
    
    pericope_book_abbrevs = ["JOH", "ACT"]
    book_counter = 0

    # Skips row 45 because that contains ς which only occurs at the end of words - the program adds it later
    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_alphabet.csv").resolve(), usecols=[0, 1], skiprows=[45])
    df.columns = ['letter', 'betacode']
    alphabet_map = dict(zip(df["betacode"], df["letter"]))

    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_punctuation.csv").resolve(), usecols=[0, 1])
    df.columns = ['punctuation', 'betacode']
    punctuation_map = dict(zip(df["betacode"], df['punctuation']))

    df = pd.read_csv((Path(__file__).parent / "tools" / "betacode_translation" / "betacode_diacritics.csv").resolve(), usecols=[0, 1, 2])
    # Ignores last row which contains the coding for the breve, which is not in the ancient text
    df = df[:-1]
    df.columns = ['diacritic', 'betacode', 'name']
    diacritic_map =  dict(zip(df["betacode"], df['diacritic']))

    name_diacritic_map =  dict(zip(df["name"], df['diacritic']))

    for file_path in book_file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            contents = file.read()
            cleaned = clean_betacode(contents)
            punctuated_words = cleaned.split(" ")
            book = ""
            book = pericope_book_abbrevs[book_counter]
            chapter = 1
            verse = 1
            word_index = 1
            for punctuated_word in punctuated_words:
                # chapter and verse is now in form Chapter:Verse
                if len(punctuated_word) == 5 and (punctuated_word.replace(":", "")).isdigit() and punctuated_word[2] == ":":
                    last_chapter = chapter
                    last_verse = verse
                    chapter = int(punctuated_word[:2])
                    verse = int(punctuated_word[3:])
                    if chapter != last_chapter or verse != last_verse:
                        word_index = 1
                else:
                    mono_LC = simplify_betacode(punctuated_word, False, None, punctuation_map.keys())
                    word = mono_LC
                    unicode = betacode_to_unicode(mono_LC, alphabet_map, diacritic_map, None, True)
                    std_poly_LC = to_std_poly_form(unicode, False, name_diacritic_map)
                    cursor.execute('''
                            INSERT INTO pericope_words (word, unicode, std_poly_LC, book, chapter, verse, word_index)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''',
                            (word, unicode, std_poly_LC, book, chapter, verse, word_index)
                            )
                    word_index += 1
        book_counter += 1

def test_pericope_words(conn):
    df = pd.read_sql_query('SELECT * FROM pericope_words', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "pericope_words.csv").resolve(), index=False, encoding="utf-8-sig")

# In unicode so that both pericope_match_info and sbl_match_info can use it
def make_source_verses(cursor):
    cursor.execute('DROP TABLE IF EXISTS source_verses')

    cursor.execute('''CREATE TABLE IF NOT EXISTS source_verses (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse_num INTEGER,
                   verse_text TEXT
    )''')

    cursor.execute('''SELECT sinf.unicode, inst.book, inst.chapter, inst.verse FROM word_instances inst
                   LEFT JOIN source_word_info sinf ON inst.source_id = sinf.id
    ''')

    rows = cursor.fetchall()

    verse_text = ""
    last_verse_num = None
    for i in range(len(rows)):
        word = rows[i][0]
        book = rows[i][1]
        chapter = rows[i][2]
        verse_num = int(rows[i][3])
        verse_text += word + " "
        if i == len(rows) - 1 or int(rows[i+1][3]) != verse_num:
            verse_text = verse_text.strip()
            cursor.execute("INSERT INTO source_verses (book, chapter, verse_num, verse_text) VALUES (?, ?, ?, ?)", (book, chapter, verse_num, verse_text))
            verse_text = ""

def test_source_verses(conn):
    df = pd.read_sql_query('SELECT * FROM source_verses', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "source_verses.csv").resolve(), index=False, encoding="utf-8-sig")

def make_pericope_match_info(cursor):
    cursor.execute('DROP TABLE IF EXISTS pericope_match_info')

    cursor.execute('''CREATE TABLE IF NOT EXISTS pericope_match_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   pericope_id INTEGER,
                   word_order INTEGER,
                   secondary_word_order INTEGER,
                   matched_word_index INTEGER,
                   FOREIGN KEY (pericope_id) REFERENCES pericope_words(id)
                   )''')

    # cursor.execute("SELECT book, chapter, verse_num, verse_text FROM source_verses WHERE book = 'ACT' AND chapter = ? AND verse_num = ? LIMIT 1", (24, 6))
    cursor.execute("SELECT book, chapter, verse_num, verse_text FROM source_verses")
    verse_rows = cursor.fetchall()

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pericope_words_bcv ON pericope_words(book, chapter, verse)")

    # with open((Path(__file__).parent / ".." / "output" / "testing" / "pericope_match_info_log.txt").resolve(), 'w', encoding='utf-8') as out_file:
    #     out_file.write("HEY HEY\n")

    rp_book_index = 0
    rp_chapter_index = 1
    rp_verse_num_index = 2
    rp_verse_text_index = 3
    for verse_row in verse_rows:
        cursor.execute("SELECT id, unicode, book, chapter, verse, word_index FROM pericope_words WHERE book = ? AND chapter = ? AND verse = ?",
                       (verse_row[rp_book_index], verse_row[rp_chapter_index], verse_row[rp_verse_num_index]))
        per_rows = cursor.fetchall()

        verse_words = verse_row[rp_verse_text_index].lower().split(" ")
        per_id_by_match_index = [None] * len(verse_words)
        used_indexes = []
        highest_used_index = -1

        for per_row in per_rows:
            id = per_row[0]
            word = per_row[1].lower()
            curr_position = 0
            if used_indexes:
                curr_position = highest_used_index + 1
            if curr_position < len(verse_words):
                shifted_match_index = None
                if word in verse_words[curr_position:]:
                    # capitals in words are ignored for matching purposes
                    shifted_match_index = verse_words[curr_position:].index(word)
                if shifted_match_index is not None:
                    match_index = shifted_match_index + curr_position
                    per_id_by_match_index[match_index] = id
                    used_indexes.append(match_index)
                    if match_index > highest_used_index:
                        highest_used_index = match_index
            else:
                break
        
        # print(f"per_rows {per_rows}")
        # print(f"verse_row {verse_row}")
        # print(f"per_id_by_match_index {per_id_by_match_index}")
        to_insert = []
        # -1 means that no match has occured yet - necessary so that words that appear before a match will be ordered properly
        word_order = -1
        secondary_word_order = 1
        last_verse = None
        for per_row in per_rows:
            id = per_row[0]
            verse = per_row[4]
            # with open((Path(__file__).parent / ".." / "output" / "testing" / "pericope_match_info_log.txt").resolve(), 'a', encoding='utf-8') as out_file:
            #     out_file.write(f"disp_rows[i] {disp_rows[i]} \n")
            #     out_file.write(f"last_verse {last_verse} curr_verse {disp_rows[i][verse_index]} word_order {word_order} secondary_word_order {secondary_word_order} \n")
            if last_verse is not None:
                if last_verse != verse:
                    word_order = -1
                    secondary_word_order = 1

            if id in per_id_by_match_index:
                matched_word_index = per_id_by_match_index.index(id) + 1
                word_order = matched_word_index
                secondary_word_order = 1
            else:
                matched_word_index = None
                # use word_order and not word_order + 1 because sbl_id_by_match_index is 0-indexed
                if word_order != -1 and word_order < len(per_id_by_match_index):
                    next_match_id = per_id_by_match_index[word_order]
                    # with open((Path(__file__).parent / ".." / "output" / "testing" / "pericope_match_info_log.txt").resolve(), 'a', encoding='utf-8') as out_file:
                    #     out_file.write(f"next_match_id {next_match_id} word_order {word_order} \n disp_rows[i] {disp_rows[i]} \n")
                    if next_match_id is not None:
                        secondary_word_order += 1
                    else:
                        word_order += 1
                else:
                    if word_order != -1:
                        word_order += 1
                    else:
                        if last_verse is not None:
                            secondary_word_order += 1
            last_verse = verse

            to_insert.append([id, word_order, secondary_word_order, matched_word_index])

        cursor.executemany('''
            INSERT INTO pericope_match_info (pericope_id, word_order, secondary_word_order, matched_word_index)
            VALUES (?, ?, ?, ?)
            ''', to_insert
        )


def test_pericope_match_info(conn):
    df = pd.read_sql_query('SELECT * FROM pericope_match_info', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "pericope_match_info.csv").resolve(), index=False, encoding="utf-8-sig")

def test_full_pericope_info(conn):
    df = pd.read_sql_query('''SELECT dw.book, dw.chapter, dw.verse, dw.word_index, dw.word, dw.unicode, dm.matched_word_index, dm.word_order, dm.secondary_word_order
                           FROM pericope_match_info dm
                           LEFT JOIN pericope_words dw
                           ON dm.pericope_id = dw.id

                           UNION

                           SELECT dw.book, dw.chapter, dw.verse, dw.word_index, dw.word, dw.unicode, dm.matched_word_index,
                            COALESCE(dm.word_order, dw.word_index) AS word_order, COALESCE(dm.secondary_word_order, 1)
                           FROM pericope_words dw
                           LEFT JOIN pericope_match_info dm
                           ON dm.pericope_id = dw.id
                           ''', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "full_pericope_info.csv").resolve(), index=False, encoding="utf-8-sig")

def make_sbl_words(cursor):
    cursor.execute('DROP TABLE IF EXISTS sbl_words')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS sbl_words (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   source_id INTEGER,
                   parsed_id INTEGER,
                   word VARCHAR(45),
                   mono_LC VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER,
                   FOREIGN KEY (source_id) REFERENCES source_word_info(id)
                   )''')

    # base = (Path(__file__).parent / ".." / "external_sources" / "SBLGNT-master" / "data" / "sblgnt" / "text").resolve()
    # book_file_paths = [
    #     base / f for f in os.listdir(base)
    #     if (base / f).is_file()
    # ]
    
    base = (Path(__file__).parent / ".." / "external_sources" / "SBLGNT-master" / "data" / "sblgnt" / "text").resolve()
    book_file_paths = [
        base / "Matt.txt",
        base / "Mark.txt",
        base / "Luke.txt",
        base / "John.txt",
        base / "Acts.txt",
        base / "Rom.txt",
        base / "1Cor.txt",
        base / "2Cor.txt",
        base / "Gal.txt",
        base / "Eph.txt",
        base / "Phil.txt",
        base / "Col.txt",
        base / "1Thess.txt",
        base / "2Thess.txt",
        base / "1Tim.txt",
        base / "2Tim.txt",
        base / "Titus.txt",
        base / "Phlm.txt",
        base / "Heb.txt",
        base / "Jas.txt",
        base / "1Pet.txt",
        base / "2Pet.txt",
        base / "1John.txt",
        base / "2John.txt",
        base / "3John.txt",
        base / "Jude.txt",
        base / "Rev.txt"
    ]

    # For Testing
    # base = (Path(__file__).parent / "testing")
    # book_file_paths = [(base / "test sbl acts 5 2.txt").resolve()]

    char_df = pd.read_csv((Path(__file__).parent / "tools" / "SBLGNT" / "characters.csv").resolve(), usecols=[1, 2,3])
    char_df.columns = ['diacritics', 'punctuation', 'footnote']
    punc_chars = set(char_df['punctuation'])
    foot_chars = set(char_df['footnote'])
    diac_chars = set(char_df["diacritics"])

    book_counter = 0
    total_word_index = 1
    for file_path in book_file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            contents = file.read()
            # Split by any whitespace (spaces, tabs, newlines)
            words = re.split(r'\s+', contents)
            # Remove any empty strings
            words = [w for w in words if w]
            book = book_abbrevs[book_counter]
            chapter = None
            verse = None
            word_index = None
            for word in words:
                book_name = str(file_path.relative_to(base)).split('.')[0]
                if word == book_name:
                    continue
                if ':' in word and (word.replace(":", "")).isdigit():
                    chapter_verse = word.split(':')
                    chapter = int(chapter_verse[0])
                    verse = int(chapter_verse[1])
                    word_index = 1
                    continue
                if chapter is None or verse is None or word_index is None:
                    continue

                word = ''.join(c for c in word if c not in punc_chars and c not in foot_chars and not c.isdigit())
                lower_word = word.lower()
                lower_word = unicodedata.normalize('NFD', lower_word)
                mono_LC = ''.join(c for c in lower_word if c not in diac_chars)
                mono_LC = unicodedata.normalize('NFC', mono_LC)

                cursor.execute("SELECT id, parsed_id FROM source_word_info WHERE unicode = ?", (word,))

                source_row = cursor.fetchone()

                source_id = None

                parsed_id = None

                if source_row:
                    source_id = source_row[0]
                    parsed_id = source_row[1]
                else:
                    # TODO: WORK ON THIS and make sure no mono_lc has 2+ strong number
                    cursor.execute("SELECT id FROM parsed_word_info WHERE unicode = ?", (word,))
                    source_row = cursor.fetchone()
                
                cursor.execute("INSERT INTO sbl_words (source_id, word, mono_LC, book, chapter, verse, word_index, total_word_index) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (source_id, word, mono_LC, book, chapter, verse, word_index, total_word_index)
                )
                word_index += 1
                total_word_index += 1
        book_counter += 1

def test_sbl_words(conn):
    df = pd.read_sql_query('SELECT * FROM sbl_words', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "sbl_words.csv").resolve(), index=False, encoding="utf-8-sig")

def make_sbl_match_info(cursor):
    cursor.execute('DROP TABLE IF EXISTS sbl_match_info')

    cursor.execute('''CREATE TABLE IF NOT EXISTS sbl_match_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   sbl_id INTEGER,
                   word_order INTEGER,
                   secondary_word_order INTEGER,
                   matched_word_index INTEGER,
                   FOREIGN KEY (sbl_id) REFERENCES sbl_words(id)
                   )''')

    # cursor.execute("SELECT book, chapter, verse_num, verse_text FROM source_verses WHERE book = 'MAT' AND chapter = '1' AND verse_num = '1'")
    cursor.execute("SELECT book, chapter, verse_num, verse_text FROM source_verses")
    verse_rows = cursor.fetchall()

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sbl_words_bcv ON sbl_words(book, chapter, verse)")

    # with open((Path(__file__).parent / ".." / "output" / "testing" / "pericope_match_info_log.txt").resolve(), 'w', encoding='utf-8') as out_file:
    #     out_file.write("HEY HEY\n")

    rp_book_index = 0
    rp_chapter_index = 1
    rp_verse_num_index = 2
    rp_verse_text_index = 3
    for verse_row in verse_rows:
        cursor.execute("SELECT id, word, book, chapter, verse, word_index FROM sbl_words WHERE book = ? AND chapter = ? AND verse = ?",
                       (verse_row[rp_book_index], verse_row[rp_chapter_index], verse_row[rp_verse_num_index]))
        sbl_rows = cursor.fetchall()

        verse_words = verse_row[rp_verse_text_index].lower().split(" ")
        sbl_id_by_match_index = [None] * len(verse_words)
        used_indexes = []
        highest_used_index = -1

        for sbl_row in sbl_rows:
            id = sbl_row[0]
            word = sbl_row[1].lower()

            curr_position = 0
            if used_indexes:
                curr_position = highest_used_index + 1
            if curr_position < len(verse_words):
                shifted_match_index = None
                if word in verse_words[curr_position:]:
                    # capitals in words are ignored for matching purposes
                    shifted_match_index = verse_words[curr_position:].index(word)
                if shifted_match_index is not None:
                    match_index = shifted_match_index + curr_position
                    sbl_id_by_match_index[match_index] = id
                    used_indexes.append(match_index)
                    if match_index > highest_used_index:
                        highest_used_index = match_index
            else:
                break
        
        # print(f"sbl_id_by_match_index {sbl_id_by_match_index}")
        to_insert = []
        # -1 means that no match has occured yet - necessary so that words that appear before a match will be ordered properly
        word_order = -1
        secondary_word_order = 1
        last_verse = None
        for sbl_row in sbl_rows:
            id = sbl_row[0]
            verse = sbl_row[4]
            # with open((Path(__file__).parent / ".." / "output" / "testing" / "pericope_match_info_log.txt").resolve(), 'a', encoding='utf-8') as out_file:
            #     out_file.write(f"disp_rows[i] {disp_rows[i]} \n")
            #     out_file.write(f"last_verse {last_verse} curr_verse {disp_rows[i][verse_index]} word_order {word_order} secondary_word_order {secondary_word_order} \n")
            if last_verse is not None:
                if last_verse != verse:
                    word_order = -1
                    secondary_word_order = 1

            if id in sbl_id_by_match_index:
                matched_word_index = sbl_id_by_match_index.index(id) + 1
                word_order = matched_word_index
                secondary_word_order = 1
            else:
                matched_word_index = None
                # use word_order and not word_order + 1 because sbl_id_by_match_index is 0-indexed
                if word_order != -1 and word_order < len(sbl_id_by_match_index):
                    next_match_id = sbl_id_by_match_index[word_order]
                    # with open((Path(__file__).parent / ".." / "output" / "testing" / "pericope_match_info_log.txt").resolve(), 'a', encoding='utf-8') as out_file:
                    #     out_file.write(f"next_match_id {next_match_id} word_order {word_order} \n disp_rows[i] {disp_rows[i]} \n")
                    if next_match_id is not None:
                        secondary_word_order += 1
                    else:
                        word_order += 1
                else:
                    if word_order != -1:
                        word_order += 1
                    else:
                        if last_verse is not None:
                            secondary_word_order += 1
            last_verse = verse

            to_insert.append([id, word_order, secondary_word_order, matched_word_index])

        cursor.executemany('''
            INSERT INTO sbl_match_info (sbl_id, word_order, secondary_word_order, matched_word_index)
            VALUES (?, ?, ?, ?)
            ''', to_insert
        )

def test_sbl_match_info(conn):
    df = pd.read_sql_query('SELECT * FROM sbl_match_info', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "sbl_match_info.csv").resolve(), index=False, encoding="utf-8-sig")

def test_full_sbl_info(conn):
    df = pd.read_sql_query('''SELECT sw.book, sw.chapter, sw.verse, sw.word_index, sw.word, COALESCE(sm.word_order, sw.word_index) AS word_order,
                           COALESCE(sm.secondary_word_order, 1) AS secondary_word_order, sm.matched_word_index FROM sbl_words sw
                           LEFT JOIN sbl_match_info sm ON sw.id = sbl_id

                           UNION

                           SELECT sw.book, sw.chapter, sw.verse, sw.word_index, sw.word, sm.word_order,
                           sm.secondary_word_order, sm.matched_word_index FROM sbl_match_info sm
                           LEFT JOIN sbl_words sw ON sw.id = sbl_id

    ''', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "full_sbl_info.csv").resolve(), index=False, encoding="utf-8-sig")

def test_rp_sbl_merge(conn):
    df = pd.read_sql_query('''WITH rp AS (
                            SELECT inst.book, inst.chapter, inst.verse, inst.word_index, sinf.unicode AS word FROM word_instances inst
                            LEFT JOIN source_word_info sinf
                            ON inst.source_id = sinf.id
                           ),
                           sbl AS (
                                SELECT sw.word, sw.book, sw.chapter, sw.verse, sw.word_index, COALESCE(sm.word_order, sw.word_index) AS word_order, sm.secondary_word_order, sm.matched_word_index
                                FROM sbl_words sw
                                LEFT JOIN sbl_match_info sm
                                ON sw.id = sm.sbl_id
                            ),
                            final AS (
                                SELECT rp.book AS book, rp.chapter AS chapter, rp.verse AS verse, rp.word_index, rp.word AS rp_word, sbl.word AS sbl_word,
                                    COALESCE(sbl.word_order, rp.word_index) AS index_order, sbl.secondary_word_order FROM rp
                                LEFT JOIN sbl ON rp.book = sbl.book AND rp.chapter = sbl.chapter AND rp.verse = sbl.verse AND rp.word_index = sbl.matched_word_index
                           
                                UNION
                           
                                SELECT COALESCE(rp.book, sbl.book) AS book, COALESCE(rp.chapter, sbl.chapter) AS chapter, COALESCE(rp.verse, sbl.verse) AS verse,
                                    rp.word_index, rp.word AS rp_word, sbl.word AS sbl_word, COALESCE(sbl.word_order, rp.word_index) AS index_order, sbl.secondary_word_order FROM sbl
                                LEFT JOIN rp ON rp.book = sbl.book AND rp.chapter = sbl.chapter AND rp.verse = sbl.verse AND rp.word_index = sbl.matched_word_index
                            )
                           
                           SELECT f.book, f.chapter, f.verse, f.word_index, f.index_order, f.rp_word, f.sbl_word FROM final f
                           LEFT JOIN books bo ON bo.book = f.book
                           ORDER BY bo.id, f.chapter, f.verse, f.index_order, f.secondary_word_order
                           
                           ''', conn)
    df.to_csv((Path(__file__).parent / ".." / "output" / "test_rp_sbl_merge.csv").resolve(), index=False, encoding="utf-8-sig")

def verify_sbl_words(cursor, conn):
    letter_df = pd.read_csv((Path(__file__).parent / "tools" / "SBLGNT" / "characters.csv").resolve(), usecols=[0])
    letter_df.columns = ['letters']
    letter_set = set(letter_df['letters']).union(letter_df['letters'])

    cursor.execute("SELECT mono_LC, book, chapter, verse, word_index FROM sbl_words")
    rows = cursor.fetchall()

    errors = {}

    for row in rows:
        word = row[0]
        word = unicodedata.normalize('NFD', word)
        for c in word:
            if c not in letter_set:
                word = unicodedata.normalize('NFC', word)
                errors[c] = [word, row[1], row[2], row[3], row[4]]
    
    df = pd.DataFrame.from_dict(errors, orient='index', columns=['mono_LC', 'book', 'chapter', 'verse', 'word_index'])
    # Reset index to get the names into a column
    df = df.reset_index().rename(columns={'index': 'error'})
    df.to_csv((Path(__file__).parent / ".." / "output" / "sbl_words_verification.csv").resolve(), index=False, encoding="utf-8-sig")
    

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
    df.to_csv((Path(__file__).parent / ".." / "output" / "books.csv").resolve(), index=False, encoding="utf-8-sig")

def test_join(conn):
    df = pd.read_sql_query('''
        SELECT inst.book, inst.chapter, inst.verse, inst.word_index, sinf.unicode AS rp_word, sbl.word AS sbl_word
                           FROM word_instances inst
                           LEFT JOIN source_word_info sinf ON inst.source_id = sinf.id
                           LEFT JOIN sbl_words sbl
                           ON inst.book = sbl.book AND inst.chapter = sbl.chapter
                           AND inst.verse = sbl.verse AND inst.word_index = sbl.word_index
    ''', conn)
    df.to_csv(Path(__file__).parent / ".." / "output" / "test_join.csv", index=False, encoding="utf-8-sig")

def make_rp_words_file(conn):
    df = pd.read_sql_query('''SELECT inst.book, inst.chapter, inst.verse, inst.word_index, sinf.unicode, sinf.word FROM word_instances inst
                   LEFT JOIN source_word_info sinf ON inst.source_id = sinf.id
    ''', conn)
    df.to_csv(Path(__file__).parent / ".." / "output" / "rp_words.csv", index=False, encoding="utf-8-sig")

# WITH full_peric AS (             
#             SELECT pw.book, pw.chapter, pw.verse, pw.word_index, pw.source_id, pw.word AS peric_word, pw.unicode AS peric_unicode, pm.matched_word_index,
#                            pm.word_order, pm.secondary_word_order
#             FROM pericope_match_info pm
#             LEFT JOIN pericope_words pw
#             ON pm.pericope_id = pw.id

#             UNION

#             SELECT pw.book, pw.chapter, pw.verse, pw.word_index, pw.source_id, pw.word AS peric_word, pw.unicode AS peric_unicode, pm.matched_word_index,
#                     COALESCE(pm.word_order, pw.word_index) AS word_order, COALESCE(pm.secondary_word_order, 1)
#             FROM pericope_words pw
#             LEFT JOIN pericope_match_info pm
#             ON pm.pericope_id = pw.id
#         ),
#         rp_inst AS (
#             SELECT winst.source_id, winst.book, winst.chapter, winst.verse, winst.word_index, winst.total_word_index,
#                     full_peric.source_id AS peric_source_id, full_peric.peric_unicode, full_peric.peric_word, full_peric.matched_word_index,
#                            COALESCE(full_peric.word_order, winst.word_index) AS peric_index_order, COALESCE(full_peric.secondary_word_order, 1) AS peric_secondary_index_order
#             FROM word_instances winst
#             LEFT JOIN
#             full_peric ON
#             winst.book = full_peric.book AND winst.chapter = full_peric.chapter AND winst.verse = full_peric.verse AND winst.word_index = full_peric.matched_word_index
                           
#             UNION
                           
#             SELECT winst.source_id, COALESCE(winst.book, full_peric.book) AS book, COALESCE(winst.chapter, full_peric.chapter) AS chapter,
#                            COALESCE(winst.verse, full_peric.verse) AS verse, winst.word_index, winst.total_word_index,
#                     full_peric.source_id AS peric_source_id, full_peric.peric_unicode, full_peric.peric_word, full_peric.matched_word_index,
#                            COALESCE(full_peric.word_order, winst.word_index) AS peric_index_order, COALESCE(full_peric.secondary_word_order, 1) AS peric_secondary_index_order
#             FROM full_peric
#             LEFT JOIN
#             word_instances winst ON
#             winst.book = full_peric.book AND winst.chapter = full_peric.chapter AND winst.verse = full_peric.verse AND winst.word_index = full_peric.matched_word_index
#         ),
#         sbl AS (
#             SELECT sw.word, sw.book, sw.chapter, sw.verse, sw.word_index, COALESCE(sm.word_order, sw.word_index) AS word_order,
#                            COALESCE(sm.secondary_word_order, 1) AS secondary_word_order, sm.matched_word_index
#             FROM sbl_words sw
#             LEFT JOIN sbl_match_info sm
#             ON sw.id = sm.sbl_id

#             UNION

#             SELECT sw.word, sw.book, sw.chapter, sw.verse, sw.word_index, sm.word_order, sm.secondary_word_order, sm.matched_word_index
#             FROM sbl_match_info sm
#             LEFT JOIN sbl_words sw
#             ON sw.id = sm.sbl_id
#         ),
#         full_inst AS (
#             SELECT rp_inst.source_id, rp_inst.book AS book, rp_inst.chapter AS chapter, rp_inst.verse AS verse, rp_inst.word_index, rp_inst.total_word_index,
#                            rp_inst.peric_source_id, rp_inst.peric_unicode, rp_inst.peric_word, rp_inst.peric_index_order,
#                            rp_inst.peric_secondary_index_order, sbl.word AS sbl_word, COALESCE(sbl.word_order, rp_inst.word_index, rp_inst.peric_index_order) AS sbl_index_order,
#                            COALESCE(sbl.secondary_word_order, 1) AS sbl_secondary_index_order FROM rp_inst
#             LEFT JOIN sbl ON rp_inst.book = sbl.book AND rp_inst.chapter = sbl.chapter AND rp_inst.verse = sbl.verse AND rp_inst.word_index = sbl.matched_word_index
        
#             UNION
        
#             SELECT rp_inst.source_id, COALESCE(rp_inst.book, sbl.book) AS book, COALESCE(rp_inst.chapter, sbl.chapter) AS chapter, COALESCE(rp_inst.verse, sbl.verse) AS verse,
#                 rp_inst.word_index, rp_inst.total_word_index, rp_inst.peric_source_id, rp_inst.peric_unicode, rp_inst.peric_word,
#                            COALESCE(rp_inst.peric_index_order, rp_inst.word_index) AS peric_index_order,
#                            rp_inst.peric_secondary_index_order, sbl.word AS sbl_word,
#                 COALESCE(sbl.word_order, rp_inst.word_index, rp_inst.peric_index_order) AS sbl_index_order, COALESCE(sbl.secondary_word_order, 1) AS sbl_secondary_index_order FROM sbl
#             LEFT JOIN rp_inst ON rp_inst.book = sbl.book AND rp_inst.chapter = sbl.chapter AND rp_inst.verse = sbl.verse AND rp_inst.word_index = sbl.matched_word_index
#         ),
#         final_result AS (
#             SELECT full_inst.book, full_inst.chapter, full_inst.verse, full_inst.word_index, full_inst.total_word_index,
                           
#             sinf.unicode AS source_form, sinf.count AS source_form_count,
                           
#             full_inst.sbl_word AS sbl_source_form,

#             pinf.unicode AS mono_LC_form, pinf.count AS mono_LC_count,
                                
#             sinf.word AS betacode,
                                
#             COALESCE(pericinf.unicode, full_inst.peric_unicode) AS pericope_word,
                           
#             COALESCE(pericinf.word, full_inst.peric_word) AS pericope_betacode,
            
#             strinf.word AS lemma,
                           
#             COALESCE(pinf.str_num, peripinf.str_num) AS str_num,
            
#             strinf.def AS str_def,
#             strinf.root_1,
#             strinf.root_2,
#             strinf.root_3,

#             COALESCE(pinf.rp_code, peripinf.rp_code) AS rp_code,
#             COALESCE(pinf.rp_alt_code, peripinf.rp_alt_code) AS rp_alt_code,
#             COALESCE(pinf.rp_pos, peripinf.rp_pos) AS rp_pos,
#             COALESCE(pinf.rp_gender, peripinf.rp_gender) AS rp_gender,
#             COALESCE(pinf.rp_alt_gender, peripinf.rp_alt_gender) AS rp_alt_gender,
#             COALESCE(pinf.rp_number, peripinf.rp_number) AS rp_number,
#             COALESCE(pinf.rp_word_case, peripinf.rp_word_case) AS rp_word_case,
#             COALESCE(pinf.rp_alt_word_case, peripinf.rp_alt_word_case) AS rp_alt_word_case,
#             COALESCE(pinf.rp_tense, peripinf.rp_tense) AS rp_tense,
#             COALESCE(pinf.rp_type, peripinf.rp_type) AS rp_type,
#             COALESCE(pinf.rp_voice, peripinf.rp_voice) AS rp_voice,
#             COALESCE(pinf.rp_mood, peripinf.rp_mood) AS rp_mood,
#             COALESCE(pinf.rp_alt_mood, peripinf.rp_alt_mood) AS rp_alt_mood,
#             COALESCE(pinf.rp_person, peripinf.rp_person) AS rp_person,
#             COALESCE(pinf.rp_indeclinable, peripinf.rp_indeclinable) AS rp_indeclinable,
#             COALESCE(pinf.rp_why_indeclinable, peripinf.rp_why_indeclinable) AS rp_why_indeclinable,
#             COALESCE(pinf.rp_kai_crasis, peripinf.rp_kai_crasis) AS rp_kai_crasis,
#             COALESCE(pinf.rp_attic_greek_form, peripinf.rp_attic_greek_form) AS rp_attic_greek_form,
            
#             bo.id AS book_id,
            
#             full_inst.sbl_index_order, full_inst.sbl_secondary_index_order,
#             full_inst.peric_index_order, full_inst.peric_secondary_index_order
                           
#             FROM full_inst
#             INNER JOIN books bo ON full_inst.book = bo.book
#             LEFT JOIN source_word_info sinf ON full_inst.source_id = sinf.id
#             LEFT JOIN parsed_word_info pinf ON sinf.parsed_id = pinf.id
#             LEFT JOIN source_word_info pericinf ON full_inst.peric_source_id = pericinf.id
#             LEFT JOIN parsed_word_info peripinf ON pericinf.parsed_id = peripinf.id
#             LEFT JOIN strongs_info strinf ON pinf.str_num = strinf.str_num
#         )
#         SELECT book, chapter, verse, word_index, total_word_index,
                           
#             source_form, source_form_count,
                           
#             sbl_source_form,

#             mono_LC_form, mono_LC_count,
                                
#             betacode,
                                
#             pericope_word,
                           
#             pericope_betacode,
            
#             lemma,

#             str_num,

#             str_def,
#             root_1,
#             root_2,
#             root_3,
                           
#             rp_code,
#             rp_alt_code,
#             rp_pos,  
#             rp_gender,
#             rp_alt_gender,
#             rp_number,
#             rp_word_case,
#             rp_alt_word_case,
#             rp_tense,  
#             rp_type,  
#             rp_voice,  
#             rp_mood,  
#             rp_alt_mood,  
#             rp_person,  
#             rp_indeclinable,  
#             rp_why_indeclinable,  
#             rp_kai_crasis,  
#             rp_attic_greek_form
                           
#             FROM final_result
            
#             ORDER BY book_id, chapter, verse, sbl_index_order, sbl_secondary_index_order, peric_index_order, peric_secondary_index_order

def make_word_classification(conn):
    df = pd.read_sql_query('''
        WITH full_peric AS (             
            SELECT pw.book, pw.chapter, pw.verse, pw.word_index, pw.source_id, pw.word AS peric_word, pw.unicode AS peric_unicode, pm.matched_word_index,
                           pm.word_order, pm.secondary_word_order
            FROM pericope_match_info pm
            LEFT JOIN pericope_words pw
            ON pm.pericope_id = pw.id

            UNION

            SELECT pw.book, pw.chapter, pw.verse, pw.word_index, pw.source_id, pw.word AS peric_word, pw.unicode AS peric_unicode, pm.matched_word_index,
                    COALESCE(pm.word_order, pw.word_index) AS word_order, COALESCE(pm.secondary_word_order, 1)
            FROM pericope_words pw
            LEFT JOIN pericope_match_info pm
            ON pm.pericope_id = pw.id
        ),
        rp_inst AS (
            SELECT winst.source_id, winst.book, winst.chapter, winst.verse, winst.word_index, winst.total_word_index,
                    full_peric.source_id AS peric_source_id, full_peric.peric_unicode, full_peric.peric_word, full_peric.matched_word_index,
                           COALESCE(full_peric.word_order, winst.word_index) AS peric_index_order, COALESCE(full_peric.secondary_word_order, 1) AS peric_secondary_index_order
            FROM word_instances winst
            LEFT JOIN
            full_peric ON
            winst.book = full_peric.book AND winst.chapter = full_peric.chapter AND winst.verse = full_peric.verse AND winst.word_index = full_peric.matched_word_index
                           
            UNION
                           
            SELECT winst.source_id, COALESCE(winst.book, full_peric.book) AS book, COALESCE(winst.chapter, full_peric.chapter) AS chapter,
                           COALESCE(winst.verse, full_peric.verse) AS verse, winst.word_index, winst.total_word_index,
                    full_peric.source_id AS peric_source_id, full_peric.peric_unicode, full_peric.peric_word, full_peric.matched_word_index,
                           COALESCE(full_peric.word_order, winst.word_index) AS peric_index_order, COALESCE(full_peric.secondary_word_order, 1) AS peric_secondary_index_order
            FROM full_peric
            LEFT JOIN
            word_instances winst ON
            winst.book = full_peric.book AND winst.chapter = full_peric.chapter AND winst.verse = full_peric.verse AND winst.word_index = full_peric.matched_word_index
        ),
        sbl AS (
            SELECT sw.source_id AS sbl_source_id, sw.word, sw.book, sw.chapter, sw.verse, sw.word_index, COALESCE(sm.word_order, sw.word_index) AS word_order,
                           COALESCE(sm.secondary_word_order, 1) AS secondary_word_order, sm.matched_word_index
            FROM sbl_words sw
            LEFT JOIN sbl_match_info sm
            ON sw.id = sm.sbl_id

            UNION

            SELECT sw.source_id AS sbl_source_id, sw.word, sw.book, sw.chapter, sw.verse, sw.word_index, sm.word_order, sm.secondary_word_order, sm.matched_word_index
            FROM sbl_match_info sm
            LEFT JOIN sbl_words sw
            ON sw.id = sm.sbl_id
        ),
        full_inst AS (
            SELECT rp_inst.source_id AS rp_source_id, rp_inst.book AS book, rp_inst.chapter AS chapter, rp_inst.verse AS verse, rp_inst.word_index, rp_inst.total_word_index,
                           rp_inst.peric_source_id, rp_inst.peric_unicode, rp_inst.peric_word, rp_inst.peric_index_order,
                           rp_inst.peric_secondary_index_order, sbl.sbl_source_id, sbl.word AS sbl_word,
                           COALESCE(sbl.word_order, rp_inst.word_index, rp_inst.peric_index_order) AS sbl_index_order, 
                           COALESCE(sbl.secondary_word_order, 1) AS sbl_secondary_index_order FROM rp_inst
            LEFT JOIN sbl ON rp_inst.book = sbl.book AND rp_inst.chapter = sbl.chapter AND rp_inst.verse = sbl.verse AND rp_inst.word_index = sbl.matched_word_index
        
            UNION
        
            SELECT rp_inst.source_id AS rp_source_id, COALESCE(rp_inst.book, sbl.book) AS book, COALESCE(rp_inst.chapter, sbl.chapter) AS chapter, COALESCE(rp_inst.verse, sbl.verse) AS verse,
                rp_inst.word_index, rp_inst.total_word_index, rp_inst.peric_source_id, rp_inst.peric_unicode, rp_inst.peric_word,
                           COALESCE(rp_inst.peric_index_order, rp_inst.word_index) AS peric_index_order,
                           rp_inst.peric_secondary_index_order, sbl.sbl_source_id, sbl.word AS sbl_word,
                COALESCE(sbl.word_order, rp_inst.word_index, rp_inst.peric_index_order) AS sbl_index_order, COALESCE(sbl.secondary_word_order, 1) AS sbl_secondary_index_order FROM sbl
            LEFT JOIN rp_inst ON rp_inst.book = sbl.book AND rp_inst.chapter = sbl.chapter AND rp_inst.verse = sbl.verse AND rp_inst.word_index = sbl.matched_word_index
        ),
        to_join AS (
            SELECT *, COALESCE(rp_source_id, sbl_source_id, peric_source_id) AS source_join_id
            FROM full_inst
        ),
        final_result AS (
            SELECT to_join.book, to_join.chapter, to_join.verse, to_join.word_index, to_join.total_word_index,
                           
            rp_sinf.unicode AS source_form, rp_sinf.count AS source_form_count,
                           
            to_join.sbl_word AS sbl_source_form,

            pinf.unicode AS mono_LC_form, pinf.count AS mono_LC_count,
                                
            rp_sinf.word AS betacode,
                                
            to_join.peric_unicode AS pericope_word,
                           
            to_join.peric_word AS pericope_betacode,
            
            strinf.word AS lemma,
                           
            pinf.str_num AS str_num,
            
            strinf.def AS str_def,
            strinf.root_1,
            strinf.root_2,
            strinf.root_3,
                           
            pinf.rp_code AS rp_code,
            pinf.rp_alt_code AS rp_alt_code,
            pinf.rp_pos AS rp_pos,
            pinf.rp_gender AS rp_gender,
            pinf.rp_alt_gender AS rp_alt_gender,
            pinf.rp_number AS rp_number,
            pinf.rp_word_case AS rp_word_case,
            pinf.rp_alt_word_case AS rp_alt_word_case,
            pinf.rp_tense AS rp_tense,
            pinf.rp_type AS rp_type,
            pinf.rp_voice AS rp_voice,
            pinf.rp_mood AS rp_mood,
            pinf.rp_alt_mood AS rp_alt_mood,
            pinf.rp_person AS rp_person,
            pinf.rp_indeclinable AS rp_indeclinable,
            pinf.rp_why_indeclinable AS rp_why_indeclinable,
            pinf.rp_kai_crasis AS rp_kai_crasis,
            pinf.rp_attic_greek_form AS rp_attic_greek_form,
            
            bo.id AS book_id,
            
            to_join.sbl_index_order, to_join.sbl_secondary_index_order,
            to_join.peric_index_order, to_join.peric_secondary_index_order
                           
            FROM to_join
            INNER JOIN books bo ON to_join.book = bo.book
            LEFT JOIN source_word_info rp_sinf ON to_join.rp_source_id = rp_sinf.id
            LEFT JOIN source_word_info sinf ON to_join.source_join_id = sinf.id
            LEFT JOIN parsed_word_info pinf ON sinf.parsed_id = pinf.id
            LEFT JOIN strongs_info strinf ON pinf.str_num = strinf.str_num
        )
        SELECT book, chapter, verse, word_index, total_word_index,
                           
            source_form, source_form_count,
                           
            sbl_source_form,

            mono_LC_form, mono_LC_count,
                                
            betacode,
                                
            pericope_word,
                           
            pericope_betacode,
            
            lemma,

            str_num,

            str_def,
            root_1,
            root_2,
            root_3,
                           
            rp_code,
            rp_alt_code,
            rp_pos,  
            rp_gender,
            rp_alt_gender,
            rp_number,
            rp_word_case,
            rp_alt_word_case,
            rp_tense,  
            rp_type,  
            rp_voice,  
            rp_mood,  
            rp_alt_mood,  
            rp_person,  
            rp_indeclinable,  
            rp_why_indeclinable,  
            rp_kai_crasis,  
            rp_attic_greek_form
                           
            FROM final_result
            
            ORDER BY book_id, chapter, verse, sbl_index_order, sbl_secondary_index_order, peric_index_order, peric_secondary_index_order
    ''', conn)

    df.to_csv(Path(__file__).parent / ".." / "output" / "word_classification.csv", index=False, encoding="utf-8-sig")

def make_test_word_classification(conn):
    df = pd.read_sql_query('''
        WITH full_peric AS (             
            SELECT pw.book, pw.chapter, pw.verse, pw.word_index, pw.source_id, pw.word AS peric_word, pw.unicode AS peric_unicode, pm.matched_word_index,
                           pm.word_order, pm.secondary_word_order
            FROM pericope_match_info pm
            LEFT JOIN pericope_words pw
            ON pm.pericope_id = pw.id

            UNION

            SELECT pw.book, pw.chapter, pw.verse, pw.word_index, pw.source_id, pw.word AS peric_word, pw.unicode AS peric_unicode, pm.matched_word_index,
                    COALESCE(pm.word_order, pw.word_index) AS word_order, COALESCE(pm.secondary_word_order, 1)
            FROM pericope_words pw
            LEFT JOIN pericope_match_info pm
            ON pm.pericope_id = pw.id
        ),
        rp_inst AS (
            SELECT winst.source_id, winst.book, winst.chapter, winst.verse, winst.word_index, winst.total_word_index,
                    full_peric.source_id AS peric_source_id, full_peric.peric_unicode, full_peric.peric_word, full_peric.matched_word_index,
                           COALESCE(full_peric.word_order, winst.word_index) AS peric_index_order, COALESCE(full_peric.secondary_word_order, 1) AS peric_secondary_index_order
            FROM word_instances winst
            LEFT JOIN
            full_peric ON
            winst.book = full_peric.book AND winst.chapter = full_peric.chapter AND winst.verse = full_peric.verse AND winst.word_index = full_peric.matched_word_index
                           
            UNION
                           
            SELECT winst.source_id, COALESCE(winst.book, full_peric.book) AS book, COALESCE(winst.chapter, full_peric.chapter) AS chapter,
                           COALESCE(winst.verse, full_peric.verse) AS verse, winst.word_index, winst.total_word_index,
                    full_peric.source_id AS peric_source_id, full_peric.peric_unicode, full_peric.peric_word, full_peric.matched_word_index,
                           COALESCE(full_peric.word_order, winst.word_index) AS peric_index_order, COALESCE(full_peric.secondary_word_order, 1) AS peric_secondary_index_order
            FROM full_peric
            LEFT JOIN
            word_instances winst ON
            winst.book = full_peric.book AND winst.chapter = full_peric.chapter AND winst.verse = full_peric.verse AND winst.word_index = full_peric.matched_word_index
        ),
        sbl AS (
            SELECT sw.source_id AS sbl_source_id, sw.word, sw.book, sw.chapter, sw.verse, sw.word_index, COALESCE(sm.word_order, sw.word_index) AS word_order,
                           COALESCE(sm.secondary_word_order, 1) AS secondary_word_order, sm.matched_word_index
            FROM sbl_words sw
            LEFT JOIN sbl_match_info sm
            ON sw.id = sm.sbl_id

            UNION

            SELECT sw.source_id AS sbl_source_id, sw.word, sw.book, sw.chapter, sw.verse, sw.word_index, sm.word_order, sm.secondary_word_order, sm.matched_word_index
            FROM sbl_match_info sm
            LEFT JOIN sbl_words sw
            ON sw.id = sm.sbl_id
        ),
        full_inst AS (
            SELECT rp_inst.source_id AS rp_source_id, rp_inst.book AS book, rp_inst.chapter AS chapter, rp_inst.verse AS verse, rp_inst.word_index, rp_inst.total_word_index,
                           rp_inst.peric_source_id, rp_inst.peric_unicode, rp_inst.peric_word, rp_inst.peric_index_order,
                           rp_inst.peric_secondary_index_order, sbl.sbl_source_id, sbl.word AS sbl_word,
                           COALESCE(sbl.word_order, rp_inst.word_index, rp_inst.peric_index_order) AS sbl_index_order, 
                           COALESCE(sbl.secondary_word_order, 1) AS sbl_secondary_index_order FROM rp_inst
            LEFT JOIN sbl ON rp_inst.book = sbl.book AND rp_inst.chapter = sbl.chapter AND rp_inst.verse = sbl.verse AND rp_inst.word_index = sbl.matched_word_index
        
            UNION
        
            SELECT rp_inst.source_id AS rp_source_id, COALESCE(rp_inst.book, sbl.book) AS book, COALESCE(rp_inst.chapter, sbl.chapter) AS chapter, COALESCE(rp_inst.verse, sbl.verse) AS verse,
                rp_inst.word_index, rp_inst.total_word_index, rp_inst.peric_source_id, rp_inst.peric_unicode, rp_inst.peric_word,
                           COALESCE(rp_inst.peric_index_order, rp_inst.word_index) AS peric_index_order,
                           rp_inst.peric_secondary_index_order, sbl.sbl_source_id, sbl.word AS sbl_word,
                COALESCE(sbl.word_order, rp_inst.word_index, rp_inst.peric_index_order) AS sbl_index_order, COALESCE(sbl.secondary_word_order, 1) AS sbl_secondary_index_order FROM sbl
            LEFT JOIN rp_inst ON rp_inst.book = sbl.book AND rp_inst.chapter = sbl.chapter AND rp_inst.verse = sbl.verse AND rp_inst.word_index = sbl.matched_word_index
        ),
        to_join AS (
            SELECT *, COALESCE(rp_source_id, sbl_source_id, peric_source_id) AS source_join_id
            FROM full_inst
        ),
        final_result AS (
            SELECT to_join.book, to_join.chapter, to_join.verse, to_join.word_index, to_join.total_word_index,
                           
            rp_sinf.unicode AS source_form, rp_sinf.count AS source_form_count,
                           
            to_join.sbl_word AS sbl_source_form,

            pinf.unicode AS mono_LC_form, pinf.count AS mono_LC_count,
                                
            rp_sinf.word AS betacode,
                                
            to_join.peric_unicode AS pericope_word,
                           
            to_join.peric_word AS pericope_betacode,
            
            strinf.word AS lemma,
                           
            pinf.str_num AS str_num,
            
            strinf.def AS str_def,
            strinf.root_1,
            strinf.root_2,
            strinf.root_3,
                           
            pinf.rp_code AS rp_code,
            pinf.rp_alt_code AS rp_alt_code,
            pinf.rp_pos AS rp_pos,
            pinf.rp_gender AS rp_gender,
            pinf.rp_alt_gender AS rp_alt_gender,
            pinf.rp_number AS rp_number,
            pinf.rp_word_case AS rp_word_case,
            pinf.rp_alt_word_case AS rp_alt_word_case,
            pinf.rp_tense AS rp_tense,
            pinf.rp_type AS rp_type,
            pinf.rp_voice AS rp_voice,
            pinf.rp_mood AS rp_mood,
            pinf.rp_alt_mood AS rp_alt_mood,
            pinf.rp_person AS rp_person,
            pinf.rp_indeclinable AS rp_indeclinable,
            pinf.rp_why_indeclinable AS rp_why_indeclinable,
            pinf.rp_kai_crasis AS rp_kai_crasis,
            pinf.rp_attic_greek_form AS rp_attic_greek_form,
            
            bo.id AS book_id,
            
            to_join.sbl_index_order, to_join.sbl_secondary_index_order,
            to_join.peric_index_order, to_join.peric_secondary_index_order
                           
            FROM to_join
            INNER JOIN books bo ON to_join.book = bo.book
            LEFT JOIN source_word_info rp_sinf ON to_join.rp_source_id = rp_sinf.id
            LEFT JOIN source_word_info sinf ON to_join.source_join_id = sinf.id
            LEFT JOIN parsed_word_info pinf ON sinf.parsed_id = pinf.id
            LEFT JOIN strongs_info strinf ON pinf.str_num = strinf.str_num
        )
        SELECT book, chapter, verse, word_index, total_word_index,
                           
            source_form, source_form_count,
                           
            sbl_source_form,

            mono_LC_form, mono_LC_count,
                                
            betacode,
                                
            pericope_word,
                           
            pericope_betacode,
            
            lemma,

            str_num,

            str_def,
            root_1,
            root_2,
            root_3,
                           
            rp_code,
            rp_alt_code,
            rp_pos,  
            rp_gender,
            rp_alt_gender,
            rp_number,
            rp_word_case,
            rp_alt_word_case,
            rp_tense,  
            rp_type,  
            rp_voice,  
            rp_mood,  
            rp_alt_mood,  
            rp_person,  
            rp_indeclinable,  
            rp_why_indeclinable,  
            rp_kai_crasis,  
            rp_attic_greek_form
                           
            FROM final_result
            
            ORDER BY book_id, chapter, verse, sbl_index_order, sbl_secondary_index_order, peric_index_order, peric_secondary_index_order
    ''', conn)
    df.to_csv(Path(__file__).parent / ".." / "output" / "test_word_classification.csv", index=False, encoding="utf-8-sig")

def main():
    # Connect to a database (or create it)
    conn = sqlite3.connect(Path(__file__).parent / ".." / "WordGuide.db")
    cursor = conn.cursor()

    # make_betacode_bible(cursor)
    # test_betacode_bible(conn)

    # make_unicode_bible(cursor)
    # test_unicode_bible(conn)

    # make_external_unicode_bible(cursor)
    # test_external_unicode_bible(conn)

    # make_long_trait_codes()

    # make_old_source_word_info(cursor)
    # test_old_source_word_info(conn)

    # make_word_instances(cursor)
    # test_word_instances(conn)

    # make_parsed_word_info(cursor)
    # test_parsed_word_info(conn)

    # test_make_parsed_word_info(cursor)

    # make_parsed_word_info_verification(cursor)
    # test_parsed_word_info_verification(conn)

    # make_strongs_info(cursor)
    # test_strongs_info(conn)

    # make_pericope_words(cursor)
    # test_pericope_words(conn)

    # make_source_verses(cursor)
    # test_source_verses(conn)

    # make_pericope_match_info(cursor)
    # test_pericope_match_info(conn)

    # test_full_pericope_info(conn)
    
    # make_sbl_words(cursor)
    # test_sbl_words(conn)

    # make_sbl_match_info(cursor)
    # test_sbl_match_info(conn)

    # test_full_sbl_info(conn)
    # test_rp_sbl_merge(conn)

    # make_books(cursor)
    # test_books(conn)
    
    # make_test_word_classification(conn)
    # make_word_classification(conn)

    # test_join(conn)

    # make_rp_words_file(conn)

    # TODO: {} variants, change parsed_word_info to account for multiple str_num words, dictionary form to find which str_num for which mono_LC, ask Dad if keep punctuation of words for his reason, 
    #       add upper case and dictionary form to excel file, final output is 3 files, 1 with all info,
    #       one with data analytics for rp, and another with data analytics for sblgnt

    # Always close the connection
    conn.commit()
    conn.close()


main()