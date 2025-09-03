# Greek New Testament With Parsing

This folder contains `greek_new_testament_with_parsing.xlsx`, the main findings of the program.

## Description

### Sheet 1 - full_word_classification

Columns:
  - book: abbreviated book name
  - chapter: chapter
  - verse: verse
  - word_in_verse: the position of the word in the verse
  - word_in_NT: the position of the word in the New Testament
  - rp_text: the word as it appears in the Robinson-Pierpont edition of the Greek New Testament in the Original Greek, Byzantine Majority Text
  - sbl_text: the word as it appears in the SBLGNT
  - match?: TRUE if both the Byzantine Majority Text and SBLGNT use the exact same word; FALSE otherwise
  - unaccented_LC: monotonic no accents/diacritics lowercase Byzantine Majority Text word
  - uncial: no accents/diacritics uppercase Byzantine Majority Text word
  - betacode: beta code of Byzantine Majority Text word
  - std_poly_LC: standard polytonic (changes grave accents to acute) lowercase form of Byzantine Majority Text word
  - lemma: dictionary form of Byzantine Majority Text word
  - str_num: Strong's Number (numbers assigned by James Strong to every root word in the Bible) for the word; if rp_text is not blank, str_num is what Maurice A. Robinson specified for that word, as seen [here](https://github.com/byztxt/byzantine-majority-text/tree/master/source). Otherwise, str_num is one of up to three possible Strong's Numbers for that word
  - rp_str_num_count: the number of times the Strong's number appears in the Byzantine Majority Text
  - root_1, root_2, root_3: up to three roots for Byzantine Majority Text word
  - alt_1_str_num, alt_2_str_num: up to 2 possible alternate Strong's Numbers
  - str_def: Strong's definition for the Byzantine Majority Text word
  - rp_code: Robinson-Pierpont parsing code for Byzantine Majority Text word
  - rp_alt_code: alternate Robinson-Pierpont parsing code for Byzantine Majority Text word, as specified by Maurice A. Robinson [here](https://github.com/byztxt/byzantine-majority-text/tree/master/source)
  - Remaining Columns: Contains information from the parsing code. An "alt" in front of the name means that that information came from the alternate code mentioned above. Columns of note are elaborated on below
  - rp_pos: Part of Speech of Byzantine Majority Text word
  - rp_why_indeclinable: specifies why Byzantine Majority Text word is indeclinable
  - rp_kai_crasis: specifies if word is a kai crasis, which is when the word "καί" contracts with another word instead of being seperate


### Sheet 2 - analytics

- Contains data used to create graphs in the "graphs" sheet
- First section contains all distinct Strong's Numbers in each book of the Byzantine Majority Text
- Second section contains all exclusive Strong's Numbers in each book of the Byzantine Majority Text, meaning a Strong's Number that appears in one book, but no others
- Third section contains the nouns of the Byzantine Majority Text ranked by how frequently they appear
- Fourth section contains the number of times the Byzantine Majority Text and SBLGNT used the same exact word in each book of the Byzantine Majority Text, as well as that number divided by the number of words in the Byzantine Majority Text to get a percentage of the Byzantine Majority Text words that match to the SBLGNT

### Sheet 3 - graphs

- Contains graphs of the data in the "analytics" sheet


## betacode_to_unicode_verification.xlsx

- Verifies that the program's betacode-to-unicode converter returns an equivalent output to another converter (whose output files are found [here](https://github.com/byztxt/byzantine-majority-text/tree/master/csv-unicode))


## rp_sbl_word_order_merge_verification.xlsx

- Verifies that the scheme used to put matching words on the same row correctly matches the words by their Strong's Number and preserves the word order of both the Byzantine Majority Text and the SBLGNT
