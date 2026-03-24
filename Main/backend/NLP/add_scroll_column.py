import sqlite3

conn = sqlite3.connect('tos_research.db')
cursor = conn.cursor()

# Add scroll_position column
cursor.execute('''
    ALTER TABLE gaze_samples 
    ADD COLUMN scroll_position REAL DEFAULT 0
''')

conn.commit()
conn.close()
print("✅ Added scroll_position column")