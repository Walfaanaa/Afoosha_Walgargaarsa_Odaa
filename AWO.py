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
            st.session_state.auth = {"logged_in": True, "username": username}
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
# MAIN UI
# =========================================================
st.title("📊 Afoosha Walgargaarsa Odaa (AWO) System")
st.subheader("Welcome, you are logged in ✅")

# Here you can continue adding your Summary / Members / Save tabs
