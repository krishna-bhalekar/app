import streamlit as st

# Access query parameters directly without calling it as a function
query_params = st.query_params

if "page" in query_params:
    page = query_params["page"][0]
else:
    page = "login"

if page == "login":
    import login
    login.main()
elif page == "app":
    import app
    app.main()
