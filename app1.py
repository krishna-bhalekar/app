import streamlit as st
import pandas as pd
import os
import login  # Import the login module
import data_processing as dp  # Import data processing functions
import pickle  # For saving and loading computation state

# Check login state
def check_login_state():
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("Please login first.")
        st.experimental_set_query_params(page="login")
        st.stop()

# Save computation state to a file in the user's directory
def save_computation_state(data_frames, base_file_name="computation_state"):
    user_email = st.session_state.email
    user_directory = f"./user_data/{user_email}"
    
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    
    full_path = os.path.join(user_directory, f"{base_file_name}.pkl")
    
    with open(full_path, 'wb') as file:
        pickle.dump(data_frames, file)
    
    st.success("Computation state saved successfully.")

# Load computation state from a file
def load_computation_state(file_name):
    user_email = st.session_state.email
    user_directory = f"./user_data/{user_email}"
    full_path = os.path.join(user_directory, file_name)
    
    with open(full_path, 'rb') as file:
        return pickle.load(file)

# List saved files for the user
def list_saved_files(extension=".pkl"):
    user_email = st.session_state.email
    user_directory = f"./user_data/{user_email}"
    
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    
    files = [f for f in os.listdir(user_directory) if f.endswith(extension)]
    if files:
        return files
    else:
        return []

# Streamlit user interface
def main():
    check_login_state()  # Ensure the user is logged in

    # Display the first letter of the user's name in a circle (similar to a profile picture)
    first_letter = st.session_state.full_name[0].upper()
    st.sidebar.markdown(f"<div style='font-size:48px;border-radius:50%;background-color:rgb(255, 253, 128);width:80px;height:80px;line-height:80px;text-align:center;'>{first_letter}</div>", unsafe_allow_html=True)

    # Add the full name text below the avatar icon
    full_name_text = f"Hi {st.session_state.full_name}, your saved files"
    st.sidebar.markdown(f"<div style='text-align:center;margin-top:10px;'>{full_name_text}</div>", unsafe_allow_html=True)
    

    # List saved files in the sidebar
    saved_files = list_saved_files()
    st.sidebar.subheader("Your Saved Files")
    if saved_files:
        for file in saved_files:
            if st.sidebar.button(file):
                st.session_state.selected_file = file
                st.experimental_rerun()
    else:
        st.sidebar.write("No saved files found.")

    st.title("Keyword Grouper SEO App")
    st.markdown("by [Growth Src](https://growthsrc.com/)")

    # If a file is selected, load and display the saved computation state
    if 'selected_file' in st.session_state:
        st.subheader(f"Resuming from {st.session_state.selected_file}")
        computations = load_computation_state(st.session_state.selected_file)
        for sheet_name, sheet_df in computations.items():
            st.write(f"### {sheet_name}")
            st.dataframe(sheet_df)

    # Default stop words in English
    default_stop_words = set([
        'and', 'but', 'is', 'the', 'to', 'in', 'for', 'on', 'with', 'as', 'by', 'at', 'from',
        'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
        'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
        'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
    ])

    # Upload CSV file for keyword with clicks
    st.subheader("⬆️ Upload Keyword CSV with Clicks")
    uploaded_file = st.file_uploader("CSV with Keyword and Clicks", type=["csv"])

    if uploaded_file is not None:
        data = dp.read_csv_file(uploaded_file)
        if data is not None:
            # Automatically map columns
            keyword_column = 'Parent Keyword'
            clicks_column = 'Volume'
            difficulty_column = 'Difficulty'
            traffic_potential_column = 'Traffic potential'
            cpc_column = 'CPC'

            # Calculate Opportunity Score
            data = dp.calculate_opportunity_score(data, volume_column=clicks_column, difficulty_column=difficulty_column, cpc_column=cpc_column)

            # Store computations
            computations = {}

            # Process the data directly
            with st.spinner("Grouping..."):
                grouped_keyword_df = dp.group_keyword(data, default_stop_words)
                computations['Grouped Keywords'] = grouped_keyword_df

                metrics = dp.calculate_group_metrics(data, grouped_keyword_df)
                computations['Group Metrics'] = pd.DataFrame.from_dict(metrics, orient='index')

                # Display top 20 groups by Total Volume, Avg KD, and Traffic Potential
                def display_top_groups(metric_key, title):
                    sorted_groups = sorted(metrics.items(), key=lambda x: x[1][metric_key], reverse=(metric_key != 'Avg. KD'))
                    top_groups = sorted_groups[:20]
                    top_groups_df = pd.DataFrame(top_groups, columns=['Cluster', 'Metrics'])
                    top_groups_df[metric_key] = top_groups_df['Metrics'].map(lambda x: x[metric_key])
                    top_groups_df['Total Volume'] = top_groups_df['Metrics'].map(lambda x: x['Total Volume'])
                    top_groups_df['Avg. KD'] = top_groups_df['Metrics'].map(lambda x: x['Avg. KD'])
                    top_groups_df['Traffic Potential'] = top_groups_df['Metrics'].map(lambda x: x['Traffic Potential'])
                    st.subheader(title)
                    st.dataframe(top_groups_df.drop(columns=['Metrics']).style.format({
                        'Total Volume': '{:,.0f}', 'Avg. KD': '{:.2f}', 'Traffic Potential': '{:,.0f}',
                    }).background_gradient(cmap='viridis'))
                    computations[title] = top_groups_df.drop(columns=['Metrics'])

                col1, col2, col3 = st.columns(3)
                with col1:
                    display_top_groups('Total Volume', "🔑 Top 20 Clusters by Volume")
                with col2:
                    display_top_groups('Avg. KD', "🔑 Top 20 Clusters by Avg KD")
                with col3:
                    display_top_groups('Traffic Potential', "🔑 Top 20 Clusters by Potential")

                # Display full data with sorting options
                st.subheader("Filter Full Sheet")
                col_sort, col_order = st.columns(2)
                with col_sort:
                    sort_column = st.selectbox("Select the column to sort by:", data.columns)
                with col_order:
                    sort_order = st.radio("Select the order:", ["Ascending", "Descending"], index=1)
                ascending = True if sort_order == "Ascending" else False
                filtered_data = data.sort_values(by=sort_column, ascending=ascending)

                st.subheader(f"📄 Filtered Full Sheet by {sort_column}")
                filtered_data = filtered_data.drop(columns=['Last Update', 'First seen', '#'], errors='ignore')
                st.dataframe(filtered_data.style.format({
                    'Volume': '{:,.0f}', 'Difficulty': '{:.2f}', 'Traffic potential': '{:,.0f}', 'Global volume': '{:,.0f}', 'CPC': '{:.2f}', 'CPS': '{:.2f}', 'Opportunity Score': '{:.2f}'
                }).background_gradient(cmap='viridis').applymap(lambda x: 'background-color: white; color: black;' if pd.isna(x) or x == '' else ''))

                computations['Filtered Data'] = filtered_data

                # Filter by keyword
                keyword = st.text_input("📄 Sorted Full Sheet by cluster containing", help="Enter the keyword to filter cluster.", key="keyword_input")
                if keyword:
                    keyword_sorted_data = filtered_data[filtered_data[keyword_column].str.contains(keyword, case=False, na=False)]
                    if not keyword_sorted_data.empty:
                        st.subheader(f"📄 Sorted Full Sheet by cluster containing '{keyword}'")
                        st.dataframe(keyword_sorted_data.style.format({
                            'Volume': '{:,.0f}', 'Difficulty': '{:.2f}', 'Traffic potential': '{:,.0f}', 'Global volume': '{:,.0f}', 'CPC': '{:.2f}', 'CPS': '{:.2f}', 'Opportunity Score': '{:.2f}'
                        }).background_gradient(cmap='viridis').applymap(lambda x: 'background-color: white; color: black;' if pd.isna(x) or x == '' else ''))

                        # Store keyword filtered data
                        computations[f"Filtered Data for '{keyword}'"] = keyword_sorted_data

                        # Calculate unique counts and sum values for the filtered data
                        def count_unique_and_sum(df):
                            columns_for_unique_count = ['Parent Keyword', 'Keyword', 'SERP Features', 'Country']
                            unique_counts = df[columns_for_unique_count].nunique()
                            sum_counts = df.select_dtypes(include=[int, float]).sum()
                            avg_difficulty = df[difficulty_column].mean()
                            avg_cpc = df[cpc_column].mean()
                            avg_opportunity_score = df['Opportunity Score'].mean()
                            unique_parent_keyword = df['Parent Keyword'].unique()
                            return unique_counts, sum_counts, unique_parent_keyword, avg_difficulty, avg_cpc, avg_opportunity_score

                        unique_counts_filtered, sum_counts_filtered, unique_parent_keyword_filtered, avg_difficulty_filtered, avg_cpc_filtered, avg_opportunity_score_filtered = count_unique_and_sum(keyword_sorted_data)
                        unique_counts_filtered_df = pd.DataFrame(unique_counts_filtered, columns=['Unique Counts']).transpose()
                        sum_counts_filtered_df = pd.DataFrame(sum_counts_filtered, columns=['Sum Counts']).transpose()

                        # Create DataFrame for average values
                        avg_values_filtered_df = pd.DataFrame({
                            'Avg. Difficulty': [avg_difficulty_filtered],
                            'Avg. CPC': [avg_cpc_filtered],
                            'Avg. Opportunity Score': [avg_opportunity_score_filtered]
                        })

                        # Convert unique parent keyword to DataFrame and transpose it for horizontal display
                        unique_parent_keyword_filtered_df = pd.DataFrame(unique_parent_keyword_filtered, columns=['Unique Cluster'])

                        # Place the tables side by side
                        col_left, col_center, col_right = st.columns([2, 1, 2])
                        with col_left:
                            st.subheader("Unique Counts and Sum Counts")
                            combined_counts_filtered_df = pd.concat([unique_counts_filtered_df, sum_counts_filtered_df])
                            st.dataframe(combined_counts_filtered_df.style.format({
                                'Parent Keyword': '{:,.0f}', 'Keyword': '{:,.0f}', 'SERP Features': '{:,.0f}', 'Country': '{:,.0f}',
                                'Volume': '{:,.0f}', 'Traffic potential': '{:,.0f}', 'Global volume': '{:,.0f}', 'CPS': '{:.2f}', 'CPC': '{:.2f}', 'Difficulty': '{:.2f}', 'Opportunity Score': '{:.2f}'
                            }).background_gradient(cmap='viridis'))

                            computations['Unique Counts and Sum Counts'] = combined_counts_filtered_df

                        with col_center:
                            st.subheader("Average Values")
                            st.dataframe(avg_values_filtered_df.style.format({
                                'Avg. Difficulty': '{:.2f}', 'Avg. CPC': '{:.2f}', 'Avg. Opportunity Score': '{:.2f}'
                            }).background_gradient(cmap='viridis'))
                            computations['Average Values'] = avg_values_filtered_df

                        with col_right:
                            st.subheader("Unique Clusters")
                            st.dataframe(unique_parent_keyword_filtered_df)
                            computations['Unique Clusters'] = unique_parent_keyword_filtered_df
                    else:
                        st.write("No matches found.")

                # Calculate Traffic for filtered data
                traffic_monthly_filtered = filtered_data['Volume'].sum()
                traffic_potential_desktop_filtered = int(traffic_monthly_filtered * 0.15)
                traffic_potential_mobile_filtered = int(traffic_monthly_filtered * 0.10)

                # Calculate Conversions for filtered data
                conversion_rates = [1.00, 0.50, 0.25]
                conversion_data = {
                    "CTR": [f"{rate:.2f}%" for rate in conversion_rates],
                    "Potential Desktop": [int(traffic_potential_desktop_filtered * (rate / 100)) for rate in conversion_rates],
                    "Potential Mobile": [int(traffic_potential_mobile_filtered * (rate / 100)) for rate in conversion_rates]
                }
                conversion_df_filtered = pd.DataFrame(conversion_data)

                computations['Conversions'] = conversion_df_filtered

                # Section for selecting Average Order Value (AOV)
                col_centered = st.columns([1, 1, 1])
                with col_centered[1]:
                    st.subheader("Select Average Order Value (AOV):")
                    selected_aov = st.number_input(" ", min_value=0, value=100, step=1, format="%d")
                    st.write(f"You entered AOV value: ${selected_aov}")

                # Calculate Revenue for filtered data
                high_conversion_rate = 0.10
                medium_conversion_rate = 0.05
                low_conversion_rate = 0.025

                revenue_data = {
                    "Ranges": ["High", "Medium", "Low"],
                    "Potential Desktop": [
                        f"${traffic_potential_desktop_filtered * high_conversion_rate * selected_aov:,.2f}",
                        f"${traffic_potential_desktop_filtered * medium_conversion_rate * selected_aov:,.2f}",
                        f"${traffic_potential_desktop_filtered * low_conversion_rate * selected_aov:,.2f}"
                    ],
                    "Potential Mobile": [
                        f"${traffic_potential_mobile_filtered * high_conversion_rate * selected_aov:,.2f}",
                        f"${traffic_potential_mobile_filtered * medium_conversion_rate * selected_aov:,.2f}",
                        f"${traffic_potential_mobile_filtered * low_conversion_rate * selected_aov:,.2f}"
                    ]
                }

                revenue_df = pd.DataFrame(revenue_data)

                computations['Revenue'] = revenue_df

                # Display Traffic, Conversions, and Revenue side by side
                col_traffic, col_conversions, col_revenue = st.columns(3)
                with col_traffic:
                    st.subheader("TRAFFIC")
                    traffic_data_filtered = {
                        "": ["Traffic Monthly"],
                        "Potential Desktop": [traffic_potential_desktop_filtered],
                        "Potential Mobile": [traffic_potential_mobile_filtered]
                    }
                    traffic_df_filtered = pd.DataFrame(traffic_data_filtered)
                    st.table(traffic_df_filtered.style.set_table_styles([
                        {
                            'selector': 'th',
                            'props': [
                                ('background-color', '#ffffff'),
                                ('color', 'black'),
                                ('text-align', 'center'),
                                ('box-shadow', '2px 2px 5px rgba(0, 0, 0, 0.3)')  # Add shadow to table headers
                            ]
                        },
                        {
                            'selector': 'td',
                            'props': [
                                ('text-align', 'center'),
                                ('box-shadow', '2px 2px 5px rgba(0, 0, 0, 0.3)')  # Add shadow to table cells
                            ]
                        }
                    ]))

                with col_conversions:
                    st.subheader("CONVERSIONS")
                    st.table(conversion_df_filtered.style.set_table_styles([
                        {
                            'selector': 'th',
                            'props': [
                                ('background-color', '#ffffff'),
                                ('color', 'black'),
                                ('text-align', 'center'),
                                ('box-shadow', '2px 2px 5px rgba(0, 0, 0, 0.3)')  # Add shadow to table headers
                            ]
                        },
                        {
                            'selector': 'td',
                            'props': [
                                ('text-align', 'center'),
                                ('box-shadow', '2px 2px 5px rgba(0, 0, 0, 0.3)')  # Add shadow to table cells
                            ]
                        }
                    ]))

                with col_revenue:
                    st.subheader("REVENUE")
                    st.table(revenue_df.style.set_table_styles([
                        {
                            'selector': 'th',
                            'props': [
                                ('background-color', '#ffffff'),
                                ('color', 'black'),
                                ('text-align', 'center'),
                                ('box-shadow', '2px 2px 5px rgba(0, 0, 0, 0.3)')  # Add shadow to table headers
                            ]
                        },
                        {
                            'selector': 'td',
                            'props': [
                                ('text-align', 'center'),
                                ('box-shadow', '2px 2px 5px rgba(0, 0, 0, 0.3)')  # Add shadow to table cells
                            ]
                        }
                    ]))

                # Sticky save button at the bottom right
                st.markdown("""
                    <style>
                    .sticky {
                        position: fixed;
                        bottom: 10px;
                        right: 10px;
                        z-index: 9999;
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        text-align: center;
                        cursor: pointer;
                        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
                    }
                    .sticky:hover {
                        background-color: #45a049;
                    }
                    </style>
                    <button class="sticky" onclick="document.getElementById('save-button').click()">Save Computations</button>
                """, unsafe_allow_html=True)

                if st.button("Save Computations", key='save-button'):
                    save_computation_state(computations)

    else:
        st.write("Please upload a CSV file.")

if __name__ == "__main__":
    login.main()  # Check login status
    if st.session_state.logged_in:
        main()  # Run the main application
