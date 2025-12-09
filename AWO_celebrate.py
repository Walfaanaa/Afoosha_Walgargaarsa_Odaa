import streamlit as st
import pandas as pd
import requests
from io import StringIO, BytesIO
from datetime import datetime, timedelta

st.title("Afoosha Walgargaarsa Odaa – (GitHub data)")

# URL of the raw CSV file in GitHub
csv_url = "https://raw.githubusercontent.com/Walfaanaa/Afoosha_Walgargaarsa_Odaa/main/members.csv"

try:
    s = requests.get(csv_url).content
    members = pd.read_csv(StringIO(s.decode('utf-8')))
except Exception as e_csv:
    st.warning("Could not read CSV from GitHub; trying Excel.")
    # Try Excel file
    xlsx_url = "https://raw.githubusercontent.com/Walfaanaa/Afoosha_Walgargaarsa_Odaa/main/members.xlsx"
    try:
        b = requests.get(xlsx_url).content
        members = pd.read_excel(BytesIO(b))
    except Exception as e_xlsx:
        st.error(f"Cannot load data from GitHub. CSV error: {e_csv}\\nExcel error: {e_xlsx}")
        st.stop()

# --- rest of scheduling logic as before ---
start_date = datetime(2025, 1, 1)
members["celebration_date"] = [start_date + timedelta(days=90 * i) for i in range(len(members))]

today = datetime.today()
def status(date):
    if date < today:
        return "✔️ Completed"
    elif (date - today).days <= 90:
        return "⭐ Next in Line"
    else:
        return "⏳ Waiting"

members["status"] = members["celebration_date"].apply(status)

st.subheader("Celebration Schedule")
st.dataframe(members)

if all(members["celebration_date"] < today):
    st.warning("All members completed! Starting a new round...")
    new_start = today
    members["celebration_date"] = [new_start + timedelta(days=90 * i) for i in range(len(members))]
    st.dataframe(members)
