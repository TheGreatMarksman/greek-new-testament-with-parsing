

# Greek New Testament With Parsing

## Description

This repository compiles and analyzes data from external sources to list the words and parsing information of the Greek New Testament and compares the words of the Byzantine Majority Text and SBLGNT editions. The culmination of the program's findings is available in `greek-new-testament-with-parsing/greek_new_testament_with_parsing.xlsx`, which contains the Strong's Numbers, Strong's definitions, and parsing codes for the Byzantine Majority Text, as well as a side-by-side comparison of the words from the SBLGNT. The results have not been verified by a human - please submit any errors you find [here](https://github.com/TheGreatMarksman/greek-new-testament-with-parsing/issues).


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
  - Open `greek-new-testament-with-parsing/greek_new_testament_with_parsing.xlsx`.


To reproduce program results:
  1. Clone this repository
  2. Clone the repositories and download the files in the Data Sources section above
  3. Place the folders and files in  `external_sources`.  
  4. Run `main/ParseNewTestament.py`
