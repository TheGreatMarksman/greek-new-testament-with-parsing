import sqlite3


def main():
    conn = sqlite3.connect('WordGuide.db')
    cursor = conn.cursor()

    # Drop old table (important if changing schema)
    cursor.execute('DROP TABLE IF EXISTS breakdowns')
    
    # Create a table
    cursor.execute('''CREATE TABLE IF NOT EXISTS breakdowns (word TEXT UNIQUE PRIMARY KEY, count INTEGER)''')


        

    # Query data
    cursor.execute('SELECT * FROM words ORDER BY word ASC')
    word_rows = cursor.fetchall()

    cursor.execute('SELECT word, root FROM derivations ORDER BY word ASC')
    deriv_rows = cursor.fetchall()

    # Write the results to a text file
    with open('WordCounts.txt', 'w', encoding='utf-8') as out_file:
        for row in word_rows:
            out_file.write(f"{row}\n")  # word: count

    with open('DerivationCounts.txt', 'w', encoding='utf-8') as out_file:
        for row in deriv_rows:
            out_file.write(f"{row}\n") 


    # Always close the connection
    conn.commit()
    conn.close()

main()