import sqlite3
import unicodedata
import re
from collections import defaultdict
import pandas as pd
from pathlib import Path
import os


# GLOBALS

book_abbrevs = ["MAT", "MAR", "LUK", "JOH", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", 
         "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAM", 
         "1PE", "2PE", "1JO", "2JO", "3JO", "JUD", "REV"]


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
            
        if valid:
            for k, v in rp_dict.items():
                if str(v).lower() == "unknown":
                    rp_dict[k] = ""
            break

    return { "pos": rp_pos, "dict": rp_dict }
                            

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


def make_parsed_word_info(cursor):
    cursor.execute('DROP TABLE IF EXISTS parsed_word_info')
    
    # pos means part of speech, number means singular, plural etc.
    cursor.execute('''CREATE TABLE IF NOT EXISTS parsed_word_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   instance_id INTEGER,
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
                   rp_attic_greek_form VARCHAR(45),
                   FOREIGN KEY (instance_id) REFERENCES word_instances (id)
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
                    instance_id = None
                    std_poly_form = None
                    std_poly_LC = None

                    cursor.execute("SELECT id, unicode FROM word_instances WHERE book = ? AND chapter = ? AND verse = ? AND word_index = ?", (book, chapter, verse, word_index))
                    instance_row = cursor.fetchone()
                    if instance_row:
                        instance_id = instance_row[0]
                        std_poly_form = to_std_poly_form(instance_row[1], is_proper_noun, diacritic_map)
                        std_poly_LC = std_poly_form.lower()
                        test_poly = simplify_unicode(std_poly_LC, diacritic_list)
                        if unicode != test_poly:
                            std_poly_LC = "!!!"

                    cursor.execute('''
                                    INSERT INTO parsed_word_info (instance_id, word, unicode, std_poly_form, std_poly_LC, str_num, rp_code, rp_alt_code, rp_pos, rp_gender, rp_alt_gender, rp_number,
                                   rp_word_case, rp_alt_word_case, rp_tense, rp_type, rp_voice, rp_mood, rp_alt_mood, rp_person, rp_indeclinable, rp_why_indeclinable, rp_kai_crasis,
                                   rp_attic_greek_form) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
                                    ''',
                                    (instance_id, word, unicode, std_poly_form, std_poly_LC, str_num, code, alt_code, rp_pos, rp_dict["gender"], rp_dict["alt_gender"], rp_dict["number"], rp_dict["word_case"],
                                     rp_dict["alt_word_case"], rp_dict["tense"], rp_dict["type"], rp_dict["voice"], rp_dict["mood"], rp_dict["alt_mood"], rp_dict["person"],
                                     rp_dict["indeclinable"], rp_dict["why_indeclinable"], rp_dict["kai_crasis"], rp_dict["attic_greek_form"])
                                )
                    
                    word_index += 1

                    if two_codes:
                        i += 2

                    i += 3
        book_counter += 1


def make_std_poly_info(cursor):
    cursor.execute('DROP TABLE IF EXISTS std_poly_info')

    cursor.execute('''CREATE TABLE IF NOT EXISTS std_poly_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   std_poly_form VARCHAR(45) UNIQUE,
                   std_poly_LC VARCHAR(45),
                   str_num_1 INTEGER,
                   str_num_2 INTEGER,
                   str_num_3 INTEGER
                   )''')

    cursor.execute("SELECT DISTINCT std_poly_form, str_num FROM parsed_word_info")

    rows = cursor.fetchall()

    used_indexes = []
    for i in range(len(rows)):
        if i in used_indexes:
            continue
        std_poly_form = rows[i][0]
        std_poly_LC = rows[i][0].lower()
        str_nums = []
        str_nums.append(rows[i][1])
        
        for j in range(i, len(rows)):
            if len(str_nums) > 3:
                raise ValueError(f"ERROR IN make_std_poly_info: 3 str_nums for one std_poly_form - {std_poly_form}: {str_nums}")
            if len(str_nums) == 3:
                break
            if j in used_indexes:
                continue
            if rows[j][0] == std_poly_form and rows[j][1] not in str_nums:
                str_nums.append(rows[j][1])
                used_indexes.append(j)
        
        while len(str_nums) < 3:
            str_nums.append(None)
        cursor.execute('''INSERT INTO std_poly_info (std_poly_form, std_poly_LC, str_num_1, str_num_2, str_num_3) VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT (std_poly_form) DO UPDATE SET str_num_3 = "!!!"''',
                       (std_poly_form, std_poly_LC, str_nums[0], str_nums[1], str_nums[2])
        )


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


def make_source_verses(cursor):
    cursor.execute('DROP TABLE IF EXISTS source_verses')

    cursor.execute('''CREATE TABLE IF NOT EXISTS source_verses (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse_num INTEGER,
                   verse_text TEXT
    )''')

    cursor.execute('''SELECT unicode, book, chapter, verse FROM word_instances inst''')

    rows = cursor.fetchall()

    verse_text = ""
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

# To match by strong's number
def make_str_num_verses(cursor):
    cursor.execute('DROP TABLE IF EXISTS str_num_verses')

    cursor.execute('''CREATE TABLE IF NOT EXISTS str_num_verses (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse_num INTEGER,
                   verse_text TEXT
    )''')

    cursor.execute('''SELECT pinf.str_num, inst.unicode, inst.book, inst.chapter, inst.verse FROM word_instances inst LEFT JOIN parsed_word_info pinf ON inst.id = pinf.instance_id''')
    # cursor.execute('''SELECT pinf.str_num, inst.unicode, inst.book, inst.chapter, inst.verse FROM word_instances inst
    #                LEFT JOIN parsed_word_info pinf ON inst.id = pinf.instance_id
    #                LIMIT 15''')
    rows = cursor.fetchall()

    verse_text = ""
    for i in range(len(rows)):
        str_num = str(rows[i][0])
        book = rows[i][2]
        chapter = rows[i][3]
        verse_num = int(rows[i][4])
        verse_text += str_num + " "
        if i == len(rows) - 1 or int(rows[i+1][4]) != verse_num:
            verse_text = verse_text.strip()
            cursor.execute("INSERT INTO str_num_verses (book, chapter, verse_num, verse_text) VALUES (?, ?, ?, ?)", (book, chapter, verse_num, verse_text))
            verse_text = ""


def make_sbl_words(cursor):
    cursor.execute('DROP TABLE IF EXISTS sbl_words')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS sbl_words (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   word VARCHAR(45),
                   mono_LC VARCHAR(45),
                   std_poly_LC VARCHAR(45),
                   book VARCHAR(45),
                   chapter INTEGER,
                   verse INTEGER,
                   word_index INTEGER,
                   total_word_index INTEGER
                   )''')
    
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

    char_df = pd.read_csv((Path(__file__).parent / "tools" / "SBLGNT" / "characters.csv").resolve(), usecols=[1, 2, 3, 4])
    char_df.columns = ['diacritics', 'diacritic_names', 'punctuation', 'footnote']
    punc_chars = set(char_df['punctuation'])
    foot_chars = set(char_df['footnote'])
    diac_chars = set(char_df["diacritics"])
    name_diacritic_map =  dict(zip(char_df["diacritic_names"], char_df['diacritics']))

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
                std_poly_LC = to_std_poly_form(word, False, name_diacritic_map)
                
                cursor.execute("INSERT INTO sbl_words (word, mono_LC, std_poly_LC, book, chapter, verse, word_index, total_word_index) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (word, mono_LC, std_poly_LC, book, chapter, verse, word_index, total_word_index)
                )
                word_index += 1
                total_word_index += 1
        book_counter += 1


def make_word_orders(cursor):
    cursor.execute('DROP TABLE IF EXISTS instance_word_order')

    cursor.execute('''CREATE TABLE IF NOT EXISTS instance_word_order (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   instance_id INTEGER,
                   word_order INTEGER,
                   FOREIGN KEY (instance_id) REFERENCES word_instances(id)
                   )''')
    
    cursor.execute('DROP TABLE IF EXISTS sbl_word_order')

    cursor.execute('''CREATE TABLE IF NOT EXISTS sbl_word_order (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   sbl_id INTEGER,
                   word_order INTEGER,
                   FOREIGN KEY (sbl_id) REFERENCES sbl_words(id)
                   )''')

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sbl_words_bcv ON sbl_words(book, chapter, verse)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_word_instances_id ON word_instances(id)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parsed_word_info_instance_id ON parsed_word_info(instance_id)")


    cursor.execute("SELECT DISTINCT book, chapter, verse FROM word_instances ORDER BY book, chapter, verse")
    rp_bcv_rows = cursor.fetchall()

    cursor.execute("SELECT DISTINCT book, chapter, verse FROM sbl_words ORDER BY book, chapter, verse")
    sbl_bcv_rows = cursor.fetchall()


    book_index = 0
    chapter_index = 1
    verse_index = 2
    rp_bcv_counter = 0
    sbl_bcv_counter = 0
    rp_turn = True
    rp_bcv_done = False
    sbl_bcv_done = False
    if not rp_bcv_rows or not sbl_bcv_rows:
        rp_bcv_done = True
        sbl_bcv_done = True
    while not rp_bcv_done or not sbl_bcv_done:
        rp_bcv_row = rp_bcv_rows[rp_bcv_counter]
        sbl_bcv_row = sbl_bcv_rows[sbl_bcv_counter]
        
        id_index = 0
        str_num_index = 5
        word_index_index = 4
        if rp_bcv_row != sbl_bcv_row:
            if rp_bcv_row[book_index] == sbl_bcv_row[book_index]:
                if rp_bcv_row[chapter_index] == sbl_bcv_row[chapter_index]:
                    if rp_bcv_row[verse_index] > sbl_bcv_row[verse_index]:
                        rp_turn = False
                    elif rp_bcv_row[verse_index] < sbl_bcv_row[verse_index]:
                        rp_turn = True
                elif rp_bcv_row[chapter_index] > sbl_bcv_row[chapter_index]:
                    rp_turn = False
                else:
                    rp_turn = True
            elif rp_bcv_row[book_index] > sbl_bcv_row[book_index]:
                rp_turn = False
            else:
                rp_turn = True

            if rp_turn:

                cursor.execute('''WITH winst AS (
                            SELECT id, book, chapter, verse, word_index FROM word_instances WHERE book = ? AND chapter = ? AND verse = ?
                           )
                           SELECT winst.id, winst.book, winst.chapter, winst.verse, winst.word_index, pinf.str_num FROM winst
                           LEFT JOIN parsed_word_info pinf ON winst.id = pinf.instance_id
                           ''',
                        (rp_bcv_row[book_index], rp_bcv_row[chapter_index], rp_bcv_row[verse_index]))
                rp_rows = cursor.fetchall()
                for rp_row in rp_rows:
                    cursor.execute("INSERT INTO instance_word_order (instance_id, word_order) VALUES (?, ?)", (rp_row[id_index], rp_row[word_index_index]))
                rp_bcv_counter += 1
                rp_turn = False
            else:

                cursor.execute('''WITH sbl AS (
                                SELECT id, std_poly_LC, book, chapter, verse, word_index FROM sbl_words WHERE book = ? AND chapter = ? AND verse = ?
                            )
                            SELECT sbl.id, sbl.book, sbl.chapter, sbl.verse, sbl.word_index, spinf.str_num_1, spinf.str_num_2, spinf.str_num_3
                           FROM sbl
                           LEFT JOIN std_poly_info spinf
                           ON sbl.std_poly_LC = spinf.std_poly_LC''',
                        (sbl_bcv_row[book_index], sbl_bcv_row[chapter_index], sbl_bcv_row[verse_index]))
                sbl_rows = cursor.fetchall()
                for sbl_row in sbl_rows:
                    cursor.execute("INSERT INTO sbl_word_order (sbl_id, word_order) VALUES (?, ?)", (sbl_row[id_index], sbl_row[word_index_index]))
                sbl_bcv_counter += 1
                rp_turn = True
        else:
            cursor.execute('''WITH winst AS (
                            SELECT id, book, chapter, verse, word_index FROM word_instances WHERE book = ? AND chapter = ? AND verse = ?
                           )
                           SELECT winst.id, winst.book, winst.chapter, winst.verse, winst.word_index, pinf.str_num FROM winst
                           LEFT JOIN parsed_word_info pinf ON winst.id = pinf.instance_id
                           ''',
                        (rp_bcv_row[book_index], rp_bcv_row[chapter_index], rp_bcv_row[verse_index]))
            rp_rows = cursor.fetchall()

            cursor.execute('''WITH sbl AS (
                                SELECT id, std_poly_LC, book, chapter, verse, word_index FROM sbl_words WHERE book = ? AND chapter = ? AND verse = ?
                            )
                            SELECT sbl.id, sbl.book, sbl.chapter, sbl.verse, sbl.word_index, spinf.str_num_1, spinf.str_num_2, spinf.str_num_3
                           FROM sbl
                           LEFT JOIN std_poly_info spinf
                           ON sbl.std_poly_LC = spinf.std_poly_LC''',
                        (sbl_bcv_row[book_index], sbl_bcv_row[chapter_index], sbl_bcv_row[verse_index]))
            sbl_rows = cursor.fetchall()

            rp_counter = 0
            sbl_counter = 0

            rp_orders = {}
            sbl_orders = {}

            curr_order = 1

            rp_done = False
            sbl_done = False

            while not rp_done or not sbl_done:
                rp_num = rp_rows[rp_counter][str_num_index]
                sbl_nums =  sbl_rows[sbl_counter][str_num_index:]
                
                if rp_num in sbl_nums:                    
                    rp_orders[rp_rows[rp_counter][id_index]] = curr_order
                    sbl_orders[sbl_rows[sbl_counter][id_index]] = curr_order
                    rp_counter += 1
                    sbl_counter += 1
                    curr_order += 1
                else:
                    # checks if rp_num is any of the possible 3 sbl_nums in the following sbl_rows
                    matched_sbl_index = next((i for i, sbl_row in enumerate(sbl_rows[sbl_counter:]) if rp_num in sbl_row[str_num_index:]), None)

                    # checks if any of the sbl_nums is the rp_num of the following rp_rows
                    matched_rp_index = next((i for i, rp_row in enumerate(rp_rows[rp_counter:]) if rp_row[str_num_index] in sbl_nums), None)

                    rp_matched = matched_rp_index is not None
                    sbl_matched = matched_sbl_index is not None
                    sbl_match_first = False
                    if rp_matched and sbl_matched:
                        sbl_match_first = matched_sbl_index < matched_rp_index
                    if (rp_matched and sbl_matched and sbl_match_first) or (sbl_matched and not rp_matched):
                        for i in range(matched_sbl_index):
                            sbl_orders[sbl_rows[sbl_counter][id_index]] = curr_order
                            curr_order += 1
                            sbl_counter += 1
                    elif (rp_matched and sbl_matched and not sbl_match_first) or (rp_matched and not sbl_matched):
                        for i in range(matched_rp_index):
                            rp_orders[rp_rows[rp_counter][id_index]] = curr_order
                            curr_order += 1
                            rp_counter += 1
                    else:
                        rp_orders[rp_rows[rp_counter][id_index]] = curr_order
                        curr_order += 1
                        rp_counter += 1

                if rp_counter >= len(rp_rows):

                    rp_done = True
                    for i in range(sbl_counter, len(sbl_rows)):
                        sbl_orders[sbl_rows[sbl_counter][id_index]] = curr_order
                        curr_order += 1
                        sbl_counter += 1
                    sbl_done = True
                    
                if sbl_counter >= len(sbl_rows):

                    sbl_done = True
                    for i in range(rp_counter, len(rp_rows)):
                        rp_orders[rp_rows[rp_counter][id_index]] = curr_order
                        curr_order += 1
                        rp_counter += 1
                    rp_done = True        

            for rp_id, rp_order in rp_orders.items():
                cursor.execute("INSERT INTO instance_word_order (instance_id, word_order) VALUES (?, ?)", (rp_id, rp_order))
            
            for sbl_id, sbl_order in sbl_orders.items():
                cursor.execute("INSERT INTO sbl_word_order (sbl_id, word_order) VALUES (?, ?)", (sbl_id, sbl_order))

            rp_bcv_counter += 1
            sbl_bcv_counter += 1

        if rp_bcv_counter >= len(rp_bcv_rows):

            rp_bcv_done = True
            for i in range(sbl_bcv_counter, len(sbl_bcv_rows)):
                cursor.execute('''WITH sbl AS (
                            SELECT id, std_poly_LC, book, chapter, verse, word_index FROM sbl_words WHERE book = ? AND chapter = ? AND verse = ?
                        )
                        SELECT sbl.id, sbl.book, sbl.chapter, sbl.verse, sbl.word_index, spinf.str_num_1, spinf.str_num_2, spinf.str_num_3
                        FROM sbl
                        LEFT JOIN std_poly_info spinf
                        ON sbl.std_poly_LC = spinf.std_poly_LC''',
                    (sbl_bcv_row[book_index], sbl_bcv_row[chapter_index], sbl_bcv_row[verse_index]))
                sbl_rows = cursor.fetchall()
                for sbl_row in sbl_rows:
                    cursor.execute("INSERT INTO sbl_word_order (sbl_id, word_order) VALUES (?, ?)", (sbl_row[id_index], sbl_row[word_index_index]))
                sbl_bcv_counter += 1
            sbl_bcv_done = True

        if sbl_bcv_counter >= len(sbl_bcv_rows):

            sbl_bcv_done = True
            for i in range(rp_bcv_counter, len(rp_bcv_rows)):
                cursor.execute('''WITH winst AS (
                        SELECT id, book, chapter, verse, word_index FROM word_instances WHERE book = ? AND chapter = ? AND verse = ?
                        )
                        SELECT winst.id, winst.book, winst.chapter, winst.verse, winst.word_index, pinf.str_num FROM winst
                        LEFT JOIN parsed_word_info pinf ON winst.id = pinf.instance_id
                        ''',
                    (rp_bcv_row[book_index], rp_bcv_row[chapter_index], rp_bcv_row[verse_index]))
                rp_rows = cursor.fetchall()
                for rp_row in rp_rows:
                    cursor.execute("INSERT INTO instance_word_order (instance_id, word_order) VALUES (?, ?)", (rp_row[id_index], rp_row[word_index_index]))
                rp_bcv_counter += 1
            rp_bcv_done = True


def make_books(cursor):
    cursor.execute('DROP TABLE IF EXISTS books')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS books (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   book VARCHAR(45)
                   )''')
    
    for abbrev in book_abbrevs:
        cursor.execute("INSERT INTO books (book) VALUES (?)", (abbrev,))


def make_rp_words_file(conn):
    df = pd.read_sql_query('''SELECT inst.book, inst.chapter, inst.verse, inst.word_index, sinf.unicode, sinf.word FROM word_instances inst
                   LEFT JOIN source_word_info sinf ON inst.source_id = sinf.id
    ''', conn)
    df.to_csv(Path(__file__).parent / ".." / "output" / "rp_words.csv", index=False, encoding="utf-8-sig")


def make_word_classification(conn):
    df = pd.read_sql_query('''
        WITH rp AS (
            SELECT winst.id, winst.book, winst.chapter, winst.verse, winst.word_index, winst.total_word_index, iwo.word_order, winst.unicode AS word, winst.word AS betacode,
                    winst.std_poly_LC
            FROM word_instances winst
            LEFT JOIN
            instance_word_order iwo ON winst.id = iwo.instance_id
        ),
        sbl AS (
            SELECT sw.book, sw.chapter, sw.verse, sw.word_index, swo.word_order, sw.word, sw.std_poly_LC
            FROM sbl_words sw
            LEFT JOIN sbl_word_order swo
            ON sw.id = swo.sbl_id
        ),
        rp_sbl AS (
            SELECT rp.id AS inst_id, COALESCE(rp.book, sbl.book) AS book, COALESCE(rp.chapter, sbl.chapter) AS chapter, COALESCE(rp.verse, sbl.verse) AS verse, rp.word_index,
                 rp.total_word_index, COALESCE(rp.word_order, sbl.word_order) AS word_order, rp.word AS rp_word, sbl.word AS sbl_word, rp.betacode,
                           COALESCE(rp.std_poly_LC, sbl.std_poly_LC) AS std_poly_LC
            FROM rp
            LEFT JOIN sbl ON rp.book = sbl.book AND rp.chapter = sbl.chapter AND rp.verse = sbl.verse AND rp.word_order = sbl.word_order
                           
            UNION
                           
            SELECT rp.id AS inst_id, COALESCE(rp.book, sbl.book) AS book, COALESCE(rp.chapter, sbl.chapter) AS chapter, COALESCE(rp.verse, sbl.verse) AS verse, rp.word_index,
                 rp.total_word_index, COALESCE(rp.word_order, sbl.word_order) AS word_order, rp.word AS rp_word, sbl.word AS sbl_word, rp.betacode,
                           COALESCE(rp.std_poly_LC, sbl.std_poly_LC) AS std_poly_LC
            FROM sbl
            LEFT JOIN rp ON rp.book = sbl.book AND rp.chapter = sbl.chapter AND rp.verse = sbl.verse AND rp.word_order = sbl.word_order
        ),
        with_info AS (
            SELECT rp_sbl.inst_id, rp_sbl.book, rp_sbl.chapter, rp_sbl.verse, rp_sbl.word_index,
                 rp_sbl.total_word_index, rp_sbl.word_order, rp_sbl.rp_word, rp_sbl.sbl_word, rp_sbl.betacode,
                           rp_sbl.std_poly_LC,
                           pwi.unicode AS mono_LC,
                           COALESCE(pwi.str_num, spi.str_num_1) AS final_str_num,
                           
                            CASE
                                WHEN pwi.str_num IS NULL OR pwi.str_num = spi.str_num_1 THEN spi.str_num_2
                                WHEN pwi.str_num = spi.str_num_2 THEN spi.str_num_1
                                ELSE spi.str_num_1
                            END AS alt_1_str_num,

                            CASE
                                WHEN pwi.str_num = spi.str_num_2 THEN spi.str_num_3
                                WHEN pwi.str_num = spi.str_num_3 THEN spi.str_num_2
                                ELSE spi.str_num_3
                            END AS alt_2_str_num,
                           
                            pwi.rp_code,
                            pwi.rp_alt_code,
                            pwi.rp_pos,
                            pwi.rp_gender,
                            pwi.rp_alt_gender,
                            pwi.rp_number,
                            pwi.rp_word_case,
                            pwi.rp_alt_word_case,
                            pwi.rp_tense,
                            pwi.rp_type,
                            pwi.rp_voice,
                            pwi.rp_mood,
                            pwi.rp_alt_mood,
                            pwi.rp_person,
                            pwi.rp_indeclinable,
                            pwi.rp_why_indeclinable,
                            pwi.rp_kai_crasis,
                            pwi.rp_attic_greek_form

            FROM rp_sbl
            LEFT JOIN parsed_word_info pwI ON rp_sbl.inst_id = pwI.instance_id
            LEFT JOIN std_poly_info spi ON rp_sbl.std_poly_LC = spi.std_poly_LC
        ),
        final AS (
            SELECT with_info.book, with_info.chapter, with_info.verse, with_info.word_index,
                 with_info.total_word_index, with_info.word_order, with_info.rp_word AS source_form, with_info.sbl_word AS sbl_source_form, with_info.mono_LC, with_info.betacode,
                           with_info.std_poly_LC, si.word AS lemma, with_info.final_str_num AS str_num, si.root_1, si.root_2, si.root_3,
                           with_info.alt_1_str_num, with_info.alt_2_str_num, si.def AS str_def, with_info.rp_code, with_info.rp_alt_code,
                            with_info.rp_pos, with_info.rp_gender, with_info.rp_alt_gender, with_info.rp_number, with_info.rp_word_case, with_info.rp_alt_word_case,
                           with_info.rp_tense, with_info.rp_type, with_info.rp_voice, with_info.rp_mood, with_info.rp_alt_mood, with_info.rp_person, with_info.rp_indeclinable,
                           with_info.rp_why_indeclinable, with_info.rp_kai_crasis, with_info.rp_attic_greek_form, bo.id AS book_id
            FROM with_info
            LEFT JOIN strongs_info si ON with_info.final_str_num = si.str_num
            LEFT JOIN books bo ON with_info.book = bo.book
        )
        SELECT book, chapter, verse, word_index,
                 total_word_index, source_form, sbl_source_form, mono_LC, betacode,
                           std_poly_LC, lemma, str_num, root_1, root_2, root_3,
                           alt_1_str_num, alt_2_str_num, str_def, rp_code, rp_alt_code,
                            rp_pos, rp_gender, rp_alt_gender, rp_number, rp_word_case, rp_alt_word_case,
                           rp_tense, rp_type, rp_voice, rp_mood, rp_alt_mood, rp_person, rp_indeclinable,
                           rp_why_indeclinable, rp_kai_crasis, rp_attic_greek_form
        FROM final
        ORDER BY book_id, chapter, verse, word_order
    ''', conn)

    df.to_csv(Path(__file__).parent / ".." / "output" / "word_classification.csv", index=False, encoding="utf-8-sig")


def main():
    # Connect to a database (or create it)
    conn = sqlite3.connect(Path(__file__).parent / ".." / "WordGuide.db")
    cursor = conn.cursor()

    make_betacode_bible(cursor)

    make_unicode_bible(cursor)

    make_long_trait_codes()

    make_word_instances(cursor)

    make_parsed_word_info(cursor)

    make_std_poly_info(cursor)
    
    make_strongs_info(cursor)

    make_source_verses(cursor)

    make_str_num_verses(cursor)
    
    make_sbl_words(cursor)

    make_word_orders(cursor)

    make_books(cursor)

    make_word_classification(conn)

    # Always close the connection
    conn.commit()
    conn.close()


main()
