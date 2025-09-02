# Output

This program contains several output files, most of which are the .csv files of the SQL tables used in the program. The files which require further explanation are described below:


## full_word_classification

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
  - mono_LC: monotonic (no accents/diacritics) lowercase Byzantine Majority Text word
  - uncial: monotonic (no accents/diacritics) uppercase Byzantine Majority Text word
  - betacode: beta code of Byzantine Majority Text word
  - std_poly_LC: standard polytonic (changes grave accents to acute) lowercase form of Byzantine Majority Text word
  - lemma: dictionary form of Byzantine Majority Text word
  - str_num: Strong's Number for the word; if rp_text is not blank, str_num is what Maurice A. Robinson specified for that word, as seen here: [https://github.com/byztxt/byzantine-majority-text/tree/master/source/Strongs]. Otherwise,     str_num is one of up to three possible Strong's Numbers for that word
  - rp_str_num_count: the number of times the Strong's number appears in the Byzantine Majority Text
  - root_1, root_2, root_3: up to three roots for Byzantine Majority Text word
  - alt_1_str_num, alt_2_str_num: up to 2 possible alternate Strong's Numbers
  - str_def: Strong's definition for the Byzantine Majority Text word
  - rp_code: Robinson-Pierpont parsing code for Byzantine Majority Text word
  - rp_alt_code: alternate Robinson-Pierpont parsing code for Byzantine Majority Text word, as specified by Maurice A. Robinson here: [https://github.com/byztxt/byzantine-majority-text/tree/master/source/Strongs]
  - Remaining Columns: Contains information from the parsing code. An "alt" in front of the name means that that information came from the alternate code mentioned above. Columns of note are elaborated on below
  - rp_pos: Part of Speech of Byzantine Majority Text word
  - rp_why_indeclinable: specifies why Byzantine Majority Text word is indeclinable
  - rp_kai_crasis: specifies if word is a kai crasis, which is when the word "καί" contracts with another word instead of being seperate
