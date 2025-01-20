import json
import os
import sqlite3
from typing import List
from pydantic import BaseModel

class ErrorItem(BaseModel):
    code: str
    category: str
    subcategory: str
    description: str
    details: str
    diagnostic_questions: List[str]
    resolution: str
    search_keys: List[str]

# Ensure the JSON file path is correct
error_db_file_path = '//data/parsed/error_db.json'

# Load data from the JSON file
with open(error_db_file_path, 'r', encoding='utf-8') as file:
    error_db = json.load(file)

error_items = [ErrorItem(**item) for item in error_db["errors"]]

# Directory path
directory = 'data/parsed'

# Check if directory exists, if not, create it
if not os.path.exists(directory):
    os.makedirs(directory)

# Connect to SQLite database
conn = sqlite3.connect('data/parsed/error_db.sqlite')
c = conn.cursor()

# Create table
c.execute('''
CREATE TABLE IF NOT EXISTS errors (
    code TEXT PRIMARY KEY,
    category TEXT,
    subcategory TEXT,
    description TEXT,
    details TEXT,
    diagnostic_questions TEXT,
    resolution TEXT,
    search_keys TEXT
)
''')

# Clear the table if it's not empty
c.execute('DELETE FROM errors')

# Insert data into the table
for error_item in error_items:
    c.execute('''
    INSERT INTO errors (code, category, subcategory, description, details, diagnostic_questions, resolution, search_keys)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (error_item.code, error_item.category, error_item.subcategory, error_item.description, error_item.details,
          ', '.join(error_item.diagnostic_questions), error_item.resolution, ', '.join(error_item.search_keys)))

# Commit the changes and close the connection
conn.commit()
conn.close()
