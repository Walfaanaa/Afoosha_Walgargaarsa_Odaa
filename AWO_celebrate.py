import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.title("Afoosha Walgargaarsa Odaa – Celebration Scheduling System")

# --------------------------------------------
# Load Excel file directly from your folder
# --------------------------------------------
file_path = r"C:\Users\walfaanaam\Documents\AWO(celebrate_order).xlsx"

try:
    members = pd.read_excel(file_path)
except Exception as e:
    st.error(f"Cannot load Excel file. Check file path.\n{e}")
    st.stop()

# --------------------------------------------
# Create celebration order (3 months apart)
# --------------------------------------------
start_date = datetime(2025, 1, 1)

members["celebration_date"] = [
    start_date + timedelta(days=90 * i)
    for i in range(len(members))
]

today = datetime.today()

# --------------------------------------------
# Status symbols
# --------------------------------------------
def status(date):
    if date < today:
        return "✔️ Completed"
    elif (date - today).days <= 90:
        return "⭐ Next in Line"
    else:
        return "⏳ Waiting"

members["status"] = members["celebration_date"].apply(status)

# --------------------------------------------
# Display schedule
# --------------------------------------------
st.subheader("Celebration Schedule")
st.dataframe(members)

# --------------------------------------------
# Auto-start new round when all completed
# --------------------------------------------
if all(members["celebration_date"] < today):
    st.warning("All members completed! Starting a new round...")

    new_start = today
    members["celebration_date"] = [
        new_start + timedelta(days=90 * i)
        for i in range(len(members))
    ]

    st.dataframe(members)
