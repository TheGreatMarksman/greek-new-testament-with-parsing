import pdfplumber

with pdfplumber.open("Robinson_Pierpont_GNT.pdf") as pdf:
    with open("Robinson_Pierpont_GNT_Attempt.txt", "w", encoding="utf-8") as out_file:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                out_file.write(text + "\n")
