import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime, timedelta

st.title("Afoosha Walgargaarsa Odaa – Celebration Scheduling System")

# -----------------------------
# Load Excel file from GitHub
# -----------------------------
github_url = "https://raw.githubusercontent.com/Walfaanaa/Afoosha_Walgargaarsa_Odaa/main/AWO(celebrate_order).xlsx"

try:
    r = requests.get(github_url)
    r.raise_for_status()  # Raise error if not successful
    members = pd.read_excel(BytesIO(r.content))
except Exception as e:
    st.error(f"Cannot load Excel file from GitHub.\n{e}")
    st.stop()

# -----------------------------
# Assign celebration dates 3 months apart
# -----------------------------
start_date = datetime(2025, 1, 1)  # First celebration date

members["celebration_date"] = [
    start_date + timedelta(days=90 * i)
    for i in range(len(members))
]

today = datetime.today()

# -----------------------------
# Set status symbols
# -----------------------------
def status(date):
    if date < today:
        return "✔️ Completed"
    elif (date - today).days <= 90:
        return "⭐ Next in Line"
    else:
        return "⏳ Waiting"

members["status"] = members["celebration_date"].apply(status)

# -----------------------------
# Display celebration schedule
# -----------------------------
st.subheader("Celebration Schedule")
st.dataframe(members)

# -----------------------------
# Auto-refresh / New round
# -----------------------------
if all(members["celebration_date"] < today):
    st.warning("All members completed! Starting a new round...")

    new_start = today
    members["celebration_date"] = [
        new_start + timedelta(days=90 * i)
        for i in range(len(members))
    ]
    members["status"] = members["celebration_date"].apply(status)
    st.dataframe(members)
