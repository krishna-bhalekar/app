import sqlite3
import os
import hashlib

def create_db():
    conn = sqlite3.connect('allusers.db')
    c = conn.cursor()

    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone_no TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            directory TEXT NOT NULL
        )
    ''')

    # Create files table with additional columns for filters
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            kd_from INTEGER,
            kd_to INTEGER,
            gv_from INTEGER,
            gv_to INTEGER,
            tp_from INTEGER,
            tp_to INTEGER,
            volume_filter TEXT,
            first_seen_filter TEXT,
            sort_parent_keyword TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_directory(email):
    # Create a directory for the user to store files
    user_directory = f"./user_data/{email}"
    os.makedirs(user_directory, exist_ok=True)
    return user_directory

def create_user(first_name, last_name, phone_no, email, password):
    directory = create_user_directory(email)  # Create and get the user directory
    conn = sqlite3.connect('allusers.db')
    c = conn.cursor()

    # Check if the email already exists
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    if c.fetchone():
        print("Email already exists. Please use a different one.")
    else:
        hashed_password = hash_password(password)  # Hash the password before storing
        try:
            c.execute('INSERT INTO users (first_name, last_name, phone_no, email, password, directory) VALUES (?, ?, ?, ?, ?, ?)', 
                      (first_name, last_name, phone_no, email, hashed_password, directory))
            conn.commit()
            print("User registered successfully!")
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
    conn.close()

if __name__ == "__main__":
    create_db()
