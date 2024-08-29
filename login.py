import streamlit as st
import sqlite3
import hashlib
import os
import app  # Import the app module

# Hash the password for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Create a directory for the user to store files
def create_user_directory(email):
    user_directory = f"./user_data/{email}"
    os.makedirs(user_directory, exist_ok=True)
    return user_directory

# Create a new user in the database
def create_user(first_name, last_name, phone_no, email, password):
    conn = sqlite3.connect('allusers.db')
    c = conn.cursor()
    # Check if the email already exists
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    if c.fetchone():
        st.error("Email already exists. Please use a different one.")
    else:
        directory = create_user_directory(email)  # Create and get the user directory
        c.execute('INSERT INTO users (first_name, last_name, phone_no, email, password, directory) VALUES (?, ?, ?, ?, ?, ?)', 
                  (first_name, last_name, phone_no, email, hash_password(password), directory))
        conn.commit()
        st.success("User registered successfully!")
    conn.close()

# Check if the login credentials are correct
def check_login(email, password):
    conn = sqlite3.connect('allusers.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    stored_password = c.fetchone()
    conn.close()
    if stored_password and stored_password[0] == hash_password(password):
        return True
    return False

# Get user information after login
def get_user_info(email):
    conn = sqlite3.connect('allusers.db')
    c = conn.cursor()
    c.execute('SELECT id, first_name, last_name, directory FROM users WHERE email = ?', (email,))
    user_info = c.fetchone()
    conn.close()
    return user_info

# Login function
def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(email, password):
            user_info = get_user_info(email)
            if user_info:
                # Store login details in session state
                st.session_state.logged_in = True
                st.session_state.user_id = user_info[0]
                st.session_state.full_name = f"{user_info[1]} {user_info[2]}"
                st.session_state.user_directory = user_info[3]
                st.write("Login successful! Redirecting...")
                st.stop()  # Stop further execution to avoid rerun errors
        else:
            st.error("Invalid email or password")

# Registration function
def register():
    st.title("Register")
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name")
    with col2:
        last_name = st.text_input("Last Name")
    phone_no = st.text_input("Phone Number")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    password_confirm = st.text_input("Confirm Password", type="password")
    if st.button("Register"):
        if password == password_confirm:
            if first_name and last_name and phone_no and email and password:
                create_user(first_name, last_name, phone_no, email, password)
            else:
                st.error("Please fill out all fields")
        else:
            st.error("Passwords do not match")

# Main function
def main():
    # Initialize session state variables if not already done
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Check if user is logged in
    if st.session_state.logged_in:
        app.main()  # Call the main function from app.py
    else:
        # Show login or registration form
        menu = ["Login", "Register"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Login":
            login()
        elif choice == "Register":
            register()

if __name__ == "__main__":
    main()
