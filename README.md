

# Byzantine Majority Text - SBLGNT Comparison and Classification

## Description

This repository compiles and analyzes data from external sources to compare and classify the Byzantine Majority Text and SBLGNT editions of the Greek New Testament. The culmination of the program's findings is available in `output/full_word_classification.xlsx`, which contains a side-by-side comparison of the words from the Byzantine Majority Text and SBLGNT, as well as the Strong's Number, Strong's definition, and parsing codes for the Byzantine Majority Text.


## Data Sources

This repository uses data from:

- [byzantine-majority-text](https://github.com/byztxt/byzantine-majority-text)  
  Licensed under [The Unlicense](https://unlicense.org).  
  Full license text can be found in `licenses/UNLICENSE.txt`.

- [SBLGNT](https://github.com/LogosBible/SBLGNT)  
  Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).  
  Full license text can be found in `licenses/CC_BY_4.0.txt`.

- [Matthias Müller](https://www.christthetruth.net/2013/07/15/strongs-goes-excel/)  
  Not licensed - **We do not redistribute the Excel file directly.** 


## Getting Started

1. Clone the repositories and download the files in Data Sources
2. Place the folders and files in  `external_sources`.  
3. Run `main/ParseNewTestament.py`
