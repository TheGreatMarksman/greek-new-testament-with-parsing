

# Grammatically Parsed Greek New Testament

## Description

This repository compiles and analyzes data from external sources to compare and classify the Byzantine Majority Text and SBLGNT editions of the Greek New Testament. The culmination of the program's findings is available in `output/full_word_classification.xlsx`, which contains a side-by-side comparison of the words from the Byzantine Majority Text and SBLGNT, as well as the Strong's Number, Strong's definition, and parsing codes for the Byzantine Majority Text. The results have not been verified by a human - please submit any errors you find here: [Issues](https://github.com/TheGreatMarksman/new-testament-word-classification/issues).


## Data Sources

This repository uses data from:

- [byzantine-majority-text](https://github.com/byztxt/byzantine-majority-text)  
  Licensed under [The Unlicense](https://unlicense.org).  
  Full license text can be found in `licenses/UNLICENSE.txt`.

- [SBLGNT](https://github.com/LogosBible/SBLGNT)  
  Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).  
  Full license text can be found in `licenses/CC_BY_4.0.txt`.

- [Matthias Müller](https://www.christthetruth.net/2013/07/15/strongs-goes-excel/)  
  Freely available at the link provided.


## Getting Started
To see program results:  
  - Open `output/full_word_classification.xlsx`.


To reproduce program results:
  1. Clone this repository
  2. Clone the repositories and download the files in the Data Sources section above
  3. Place the folders and files in  `external_sources`.  
  4. Run `main/ParseNewTestament.py`
