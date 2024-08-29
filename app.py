import streamlit as st
import pandas as pd
import os
import sqlite3
from datetime import datetime
import time

# Load CSV and initialize state
def load_csv():
    st.subheader("Upload Your Keyword CSV")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        st.session_state['data'] = data
        st.success("CSV Uploaded Successfully!")
        return data
    return None

# Function to save computation with a custom file name and filters
def save_computation(data, kd_from, kd_to, gv_from, gv_to, tp_from, tp_to, volume_filter, first_seen_filter, sort_parent_keyword):
    user_directory = st.session_state.get('user_directory')
    if not user_directory:
        st.error("User directory not found.")
        return
    
    # Ensure the user directory exists
    os.makedirs(user_directory, exist_ok=True)
    
    # Automatically generate a filename if not provided
    file_name = st.text_input("Enter a name for your file", key="file_name_input")
    
    if file_name:
        file_name = f"{file_name}.csv"  # Append .csv extension to the file name
        file_path = os.path.join(user_directory, file_name)
        
        # Save the DataFrame to a CSV file
        data.to_csv(file_path, index=False)
        
        # Store the file information in the database along with the filters
        conn = sqlite3.connect('allusers.db')
        c = conn.cursor()
        user_id = st.session_state.get('user_id')
        if user_id:
            c.execute('''
                INSERT INTO files 
                (user_id, file_name, file_path, kd_from, kd_to, gv_from, gv_to, tp_from, tp_to, volume_filter, first_seen_filter, sort_parent_keyword) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', 
            (user_id, file_name, file_path, kd_from, kd_to, gv_from, gv_to, tp_from, tp_to, volume_filter, first_seen_filter, sort_parent_keyword))
            conn.commit()
            st.success(f"Computation saved as {file_name}")
        conn.close()
    else:
        st.warning("Please enter a file name.")

# Function to load saved computations
def load_saved_computations():
    conn = sqlite3.connect('allusers.db')
    c = conn.cursor()
    user_id = st.session_state.get('user_id')
    if user_id:
        c.execute('''
            SELECT id, file_name, file_path, timestamp, kd_from, kd_to, gv_from, gv_to, tp_from, tp_to, volume_filter, first_seen_filter, sort_parent_keyword 
            FROM files 
            WHERE user_id = ?
        ''', (user_id,))
        files = c.fetchall()
        conn.close()
        return files
    return []

# Function to delete a saved computation
def delete_saved_computation(file_id, file_path):
    conn = sqlite3.connect('allusers.db')
    c = conn.cursor()
    
    # Delete the file record from the database
    c.execute('DELETE FROM files WHERE id = ?', (file_id,))
    conn.commit()
    
    # Close the database connection
    conn.close()
    
    # Delete the file from the filesystem
    if os.path.exists(file_path):
        os.remove(file_path)
        st.success(f"File {os.path.basename(file_path)} deleted successfully.")
    else:
        st.warning("File not found or already deleted.")

# Display saved computations in the UI
def display_saved_computations():
    st.subheader("Saved Computations")
    files = load_saved_computations()
    if files:
        for file_id, file_name, file_path, timestamp, kd_from, kd_to, gv_from, gv_to, tp_from, tp_to, volume_filter, first_seen_filter, sort_parent_keyword in files:
            st.write(f"**{file_name}** - saved on {timestamp}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Load {file_name}", key=f"load_{file_id}"):
                    data = pd.read_csv(file_path)
                    st.session_state['data'] = data
                    st.session_state['kd_from'] = kd_from
                    st.session_state['kd_to'] = kd_to
                    st.session_state['gv_from'] = gv_from
                    st.session_state['gv_to'] = gv_to
                    st.session_state['tp_from'] = tp_from
                    st.session_state['tp_to'] = tp_to
                    st.session_state['volume_filter'] = volume_filter
                    st.session_state['first_seen_filter'] = first_seen_filter
                    st.session_state['sort_parent_keyword'] = sort_parent_keyword
                    st.success("Please check the Keyword Analysis menu")
                    time.sleep(3)  # Display notification for 3 seconds
                    st.experimental_rerun()  # Redirect to Keyword Analysis
            with col2:
                if st.button(f"Delete {file_name}", key=f"delete_{file_id}"):
                    delete_saved_computation(file_id, file_path)
                    st.experimental_rerun()  # Refresh the page after deletion
    else:
        st.write("No saved computations found.")

# Function to filter data with session state
def filter_data(data):
    st.subheader("Filter Keywords")

    # Layout the input fields in a grid with three columns
    col1, col2, col3 = st.columns(3)
    with col1:
        kd_from = st.number_input("KD From", min_value=0, max_value=100, value=st.session_state.get('kd_from', 0), step=1)
    with col2:
        kd_to = st.number_input("KD To", min_value=0, max_value=100, value=st.session_state.get('kd_to', 100), step=1)
    with col3:
        volume_filter = st.selectbox("Volume", ["All", "0-100", "100-1000", "1000+"], index=["All", "0-100", "100-1000", "1000+"].index(st.session_state.get('volume_filter', "All")))

    col4, col5, col6 = st.columns(3)
    with col4:
        gv_from = st.number_input("GV From", min_value=0, max_value=1000000, value=st.session_state.get('gv_from', 0), step=100)
    with col5:
        gv_to = st.number_input("GV To", min_value=0, max_value=1000000, value=st.session_state.get('gv_to', 1000000), step=100)
    with col6:
        first_seen_filter = st.selectbox("First Seen", ["All", "Last 30 Days", "Last 6 Months", "Last Year"], index=["All", "Last 30 Days", "Last 6 Months", "Last Year"].index(st.session_state.get('first_seen_filter', "All")))

    col7, col8, col9 = st.columns(3)
    with col7:
        tp_from = st.number_input("TP From", min_value=0, max_value=1000000, value=st.session_state.get('tp_from', 0), step=100)
    with col8:
        tp_to = st.number_input("TP To", min_value=0, max_value=1000000, value=st.session_state.get('tp_to', 1000000), step=100)
    with col9:
        sort_parent_keyword = st.selectbox("Sort Parent Keyword", ["None", "Ascending", "Descending"], index=["None", "Ascending", "Descending"].index(st.session_state.get('sort_parent_keyword', "None")))

    # Convert 'First seen' column to datetime
    if 'First seen' in data.columns:
        data['First seen'] = pd.to_datetime(data['First seen'], errors='coerce')

    # Single "Apply Filters" button at the end
    if st.button("Apply Filters"):
        # Apply KD range filter
        data = data[(data['Difficulty'] >= kd_from) & (data['Difficulty'] <= kd_to)]

        # Apply Global Volume range filter
        data = data[(data['Global volume'] >= gv_from) & (data['Global volume'] <= gv_to)]

        # Apply Traffic Potential range filter
        data = data[(data['Traffic potential'] >= tp_from) & (data['Traffic potential'] <= tp_to)]

        # Apply Volume filter
        if volume_filter != "All":
            if volume_filter == "0-100":
                data = data[(data['Volume'] > 0) & (data['Volume'] <= 100)]
            elif volume_filter == "100-1000":
                data = data[(data['Volume'] > 100) & (data['Volume'] <= 1000)]
            elif volume_filter == "1000+":
                data = data[data['Volume'] > 1000]

        # Apply First Seen filter
        if first_seen_filter != "All":
            if first_seen_filter == "Last 30 Days":
                data = data[data['First seen'] >= pd.Timestamp.now() - pd.DateOffset(days=30)]
            elif first_seen_filter == "Last 6 Months":
                data = data[data['First seen'] >= pd.Timestamp.now() - pd.DateOffset(months=6)]
            elif first_seen_filter == "Last Year":
                data = data[data['First seen'] >= pd.Timestamp.now() - pd.DateOffset(years=1)]

        # Sort by Parent Keyword if selected
        if sort_parent_keyword != "None":
            data = data.sort_values(by='Parent Keyword', ascending=(sort_parent_keyword == "Ascending"))

        # Update session state with the applied filters
        st.session_state['kd_from'] = kd_from
        st.session_state['kd_to'] = kd_to
        st.session_state['gv_from'] = gv_from
        st.session_state['gv_to'] = gv_to
        st.session_state['tp_from'] = tp_from
        st.session_state['tp_to'] = tp_to
        st.session_state['volume_filter'] = volume_filter
        st.session_state['first_seen_filter'] = first_seen_filter
        st.session_state['sort_parent_keyword'] = sort_parent_keyword

    return data

# Main app layout
def main():
    st.title("Keyword Grouper SEO App")
    
    # Sidebar Navigation
    with st.sidebar:
        # Display the first letter of the user's name in a circle
        if 'full_name' in st.session_state:
            first_letter = st.session_state.full_name[0].upper()
            st.markdown(
                f"<div style='font-size:48px;border-radius:50%;background-color:white;"
                f"width:80px;height:80px;line-height:80px;text-align:center;margin-bottom:20px;color:black'>{first_letter}</div>", 
                unsafe_allow_html=True
            )

        # Navigation text after icon
        st.header("Navigation")
        nav_option = st.radio("Go to", ["Upload CSV", "Keyword Analysis", "Saved Computations"])

    if nav_option == "Upload CSV":
        data = load_csv()
        if data is not None:
            st.session_state['data'] = data

    elif nav_option == "Keyword Analysis":
        if 'data' in st.session_state:
            data = st.session_state['data']
            filtered_data = filter_data(data)
            st.subheader("Filtered Keywords")
            st.write(filtered_data)
            # Add save computation functionality
            save_computation(
                filtered_data,
                st.session_state.get('kd_from', 0),
                st.session_state.get('kd_to', 100),
                st.session_state.get('gv_from', 0),
                st.session_state.get('gv_to', 1000000),
                st.session_state.get('tp_from', 0),
                st.session_state.get('tp_to', 1000000),
                st.session_state.get('volume_filter', "All"),
                st.session_state.get('first_seen_filter', "All"),
                st.session_state.get('sort_parent_keyword', "None")
            )
        else:
            st.warning("Please upload a CSV first.")
    
    elif nav_option == "Saved Computations":
        display_saved_computations()

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    main()
