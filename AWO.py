import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import os
from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================
load_dotenv()

# Single login credential
AWO_USER = os.getenv("AWO_USER")
AWO_PASSWORD = os.getenv("AWO_PASSWORD")

# Fail fast if missing
if not all([AWO_USER, AWO_PASSWORD]):
    raise ValueError(
        "Missing credentials in .env. Please set AWO_USER and AWO_PASSWORD"
    )

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="AWO System", layout="wide", page_icon="📊")

# =========================================================
# CONSTANTS
# =========================================================
NUMERIC_COLS = [
    "MONTHLY_PAYMENT",
    "ADDITIONAL_PAYMENT",
    "EXPENSES_INCURRED",
    "LOAN",
    "punishment",
]

ALL_COLS = [
    "ID",
    "FIRST_NAME",
    "LAST_NAME",
    "MONTHLY_PAYMENT",
    "ADDITIONAL_PAYMENT",
    "EXPENSES_INCURRED",
    "LOAN",
    "OPENINNG_DATE",
    "PHONE_NUM",
    "Email",
    "punishment",
]

GITHUB_CSV_URL = "https://raw.githubusercontent.com/Walfaanaa/Afoosha_Walgargaarsa_Odaa/main/AWO%28july%29.csv"

# =========================================================
# SESSION STATE INIT
# =========================================================
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=ALL_COLS)

if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "username": ""}

# =========================================================
# HELPERS
# =========================================================
def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=ALL_COLS)
    df = df.copy()
    for c in ALL_COLS:
        if c not in df.columns:
            df[c] = ""
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    if "OPENINNG_DATE" in df.columns:
        df["OPENINNG_DATE"] = df["OPENINNG_DATE"].astype(str)
    return df[ALL_COLS]


def save_to_sqlite(df: pd.DataFrame, db_file: str):
    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            ID TEXT PRIMARY KEY,
            FIRST_NAME TEXT,
            LAST_NAME TEXT,
            MONTHLY_PAYMENT REAL,
            ADDITIONAL_PAYMENT REAL,
            EXPENSES_INCURRED REAL,
            LOAN REAL,
            OPENINNG_DATE TEXT,
            PHONE_NUM TEXT,
            Email TEXT,
            punishment REAL
        )
        """
    )
    conn.commit()
    df.to_sql("members", conn, if_exists="replace", index=False)
    conn.close()


def load_from_sqlite(db_file: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            ID TEXT PRIMARY KEY,
            FIRST_NAME TEXT,
            LAST_NAME TEXT,
            MONTHLY_PAYMENT REAL,
            ADDITIONAL_PAYMENT REAL,
            EXPENSES_INCURRED REAL,
            LOAN REAL,
            OPENINNG_DATE TEXT,
            PHONE_NUM TEXT,
            Email TEXT,
            punishment REAL
        )
        """
    )
    conn.commit()
    df = pd.read_sql_query("SELECT * FROM members", conn)
    conn.close()
    return normalize_dataframe(df)


# =========================================================
# LOGIN
# =========================================================
def login_ui():
    st.sidebar.subheader("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username == AWO_USER and password == AWO_PASSWORD:
            st.session_state.auth = {
                "logged_in": True,
                "username": username,
                "role": "Admin",  # single password, treat as Admin
            }
            st.sidebar.success(f"Welcome {username} ✅")
            st.rerun()
        else:
            st.sidebar.error("Invalid username or password ❌")


def logout_button():
    if st.sidebar.button("Logout"):
        st.session_state.auth = {"logged_in": False, "username": ""}
        st.rerun()


if not st.session_state.auth.get("logged_in", False):
    login_ui()
    st.info("Please login from the sidebar to continue.")
    st.stop()

st.sidebar.success(f"Logged in as: {st.session_state.auth['username']}")
logout_button()

# =========================================================
# DATA SETTINGS
# =========================================================
st.sidebar.header("📦 Data Source")
db_file = st.sidebar.text_input("SQLite DB file path", "members.db")
load_from = st.sidebar.radio("Load data from:", ["GitHub CSV", "SQLite DB"], index=0)

if st.sidebar.button("🔄 Reload Data"):
    try:
        if load_from == "GitHub CSV":
            df_github = pd.read_csv(GITHUB_CSV_URL)
            st.session_state.df = normalize_dataframe(df_github)
            st.sidebar.success("Data loaded from GitHub ✅")
        else:
            st.session_state.df = load_from_sqlite(db_file)
            st.sidebar.success("Data loaded from SQLite DB ✅")
    except Exception as e:
        st.sidebar.error(f"Failed to load data: {e}")

if st.session_state.df.empty:
    try:
        df_github = pd.read_csv(GITHUB_CSV_URL)
        st.session_state.df = normalize_dataframe(df_github)
    except Exception:
        st.session_state.df = normalize_dataframe(st.session_state.df)

# =========================================================
# SUMMARY FUNCTION
# =========================================================
def display_summary():
    df = normalize_dataframe(st.session_state.df)

    if df.empty:
        st.warning("No data available to display summary statistics.")
        return

    totals = df[NUMERIC_COLS].sum()

    total_capital = totals["MONTHLY_PAYMENT"] + totals["ADDITIONAL_PAYMENT"] + totals["punishment"]
    current_capital = total_capital - totals["EXPENSES_INCURRED"]

    current_capital_on_account = 370286.99
    total_incurred = totals["EXPENSES_INCURRED"]
    loan = totals["LOAN"]
    interest_from_bank = current_capital_on_account - current_capital
    punishment = totals["punishment"]

    summary_df = pd.DataFrame(
        {
            "Category": [
                "Total Capital",
                "Current Capital",
                "Current Capital on Account",
                "Total Incurred",
                "Loan",
                "Interest from Bank",
                "Punishment",
            ],
            "Amount (ETB)": [
                float(total_capital),
                float(current_capital),
                float(current_capital_on_account),
                float(total_incurred),
                float(loan),
                float(interest_from_bank),
                float(punishment),
            ],
        }
    )

    st.subheader("📌 Summary Statistics")
    summary_table = summary_df.copy()
    summary_table["Amount (ETB)"] = summary_table["Amount (ETB)"].map(lambda x: f"{x:,.2f}")
    st.dataframe(summary_table, use_container_width=True)

    color_map = {
        "Total Capital": "#0d6efd",
        "Current Capital": "#dc3545",
        "Current Capital on Account": "#198754",
        "Total Incurred": "#fd7e14",
        "Loan": "#6f42c1",
        "Interest from Bank": "#20c997",
        "Punishment": "#6c757d",
    }

    fig = px.bar(
        summary_df,
        x="Category",
        y="Amount (ETB)",
        text="Amount (ETB)",
        color="Category",
        color_discrete_map=color_map,
        title="💰 Summary Statistics",
    )

    fig.update_traces(
        texttemplate="%{text:,.2f}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Amount: %{y:,.2f} ETB<extra></extra>",
    )

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Amount (ETB)",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


# =========================================================
# MAIN UI
# =========================================================
st.title("📊 Afoosha Walgargaarsa Odaa (AWO) System")

tab1, tab2, tab3 = st.tabs(["📌 Summary", "👥 Members", "💾 Save/Export"])

# -------------------------
# TAB 1: SUMMARY
# -------------------------
with tab1:
    display_summary()

# -------------------------
# TAB 2: MEMBERS TABLE
# -------------------------
with tab2:
    st.subheader("👥 Members Data")

    df = normalize_dataframe(st.session_state.df)
    st.dataframe(df, use_container_width=True)

    # Admin-only: Add member
    st.markdown("### ➕ Add New Member")

    with st.form("add_member_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            new_id = st.text_input("ID")
            first_name = st.text_input("First Name")
            monthly = st.number_input("Monthly Payment", min_value=0.0, value=0.0)

        with col2:
            last_name = st.text_input("Last Name")
            additional = st.number_input("Additional Payment", min_value=0.0, value=0.0)
            expenses = st.number_input("Expenses Incurred", min_value=0.0, value=0.0)

        with col3:
            loan_amount = st.number_input("Loan", min_value=0.0, value=0.0)
            punishment_val = st.number_input("Punishment", min_value=0.0, value=0.0)
            opening_date = st.text_input("Opening Date", value=str(datetime.now().date()))

        phone = st.text_input("Phone Number")
        email = st.text_input("Email")

        submitted = st.form_submit_button("✅ Add Member")

        if submitted:
            if not new_id.strip():
                st.error("ID is required!")
            else:
                new_row = {
                    "ID": new_id.strip(),
                    "FIRST_NAME": first_name.strip(),
                    "LAST_NAME": last_name.strip(),
                    "MONTHLY_PAYMENT": monthly,
                    "ADDITIONAL_PAYMENT": additional,
                    "EXPENSES_INCURRED": expenses,
                    "LOAN": loan_amount,
                    "OPENINNG_DATE": opening_date.strip(),
                    "PHONE_NUM": phone.strip(),
                    "Email": email.strip(),
                    "punishment": punishment_val,
                }

                st.session_state.df = normalize_dataframe(
                    pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                )

                st.success("Member added successfully ✅")
                st.rerun()

# -------------------------
# TAB 3: SAVE / EXPORT
# -------------------------
with tab3:
    st.subheader("💾 Save & Export")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save to SQLite"):
            try:
                save_to_sqlite(st.session_state.df, db_file)
                st.success(f"Saved to SQLite DB: {db_file} ✅")
            except Exception as e:
                st.error(f"Failed to save: {e}")

    with col2:
        st.download_button(
            "⬇️ Download CSV",
            data=normalize_dataframe(st.session_state.df).to_csv(index=False).encode("utf-8"),
            file_name="AWO_export.csv",
            mime="text/csv",
        )
