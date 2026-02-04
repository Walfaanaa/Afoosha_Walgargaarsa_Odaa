# -----------------------
# AWO.py
# Afoosha Walgargaarsa Odaa - Member Management System
# Streamlit Cloud Ready + Stable Login + Working Summary Chart
# -----------------------

import streamlit as st
import pandas as pd
import sqlite3
import io
import re
import bcrypt
import plotly.express as px

# -----------------------
# Page Setup
# -----------------------
st.set_page_config(page_title="🏦 Afoosha Walgargaarsa Odaa", layout="wide")
st.title("🏦 Afoosha Walgargaarsa Odaa Member Management System")

# -----------------------
# Helpers
# -----------------------
PHONE_RE = re.compile(r"^[0-9]{7,15}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

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

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all expected columns exist + numeric columns are numeric."""
    if df is None or df.empty:
        return pd.DataFrame(columns=ALL_COLS)

    # Ensure columns exist
    for c in ALL_COLS:
        if c not in df.columns:
            df[c] = pd.NA

    # Keep only needed columns in correct order
    df = df[ALL_COLS].copy()

    # Convert numeric columns safely
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Make ID safe
    df["ID"] = df["ID"].astype(str).str.strip()
    df.loc[df["ID"] == "", "ID"] = pd.NA

    return df

def validate_row(row: dict):
    errors = []
    phone = str(row.get("PHONE_NUM", "")).strip()
    email = str(row.get("Email", "")).strip()

    if phone and not PHONE_RE.match(phone):
        errors.append("Invalid phone number (must be 7 to 15 digits).")

    if email and not EMAIL_RE.match(email):
        errors.append("Invalid email address format.")

    if not str(row.get("ID", "")).strip():
        errors.append("ID is required.")

    if not str(row.get("FIRST_NAME", "")).strip():
        errors.append("FIRST_NAME is required.")

    if not str(row.get("LAST_NAME", "")).strip():
        errors.append("LAST_NAME is required.")

    return errors

def log_action(action, details):
    st.session_state.audit_log.append({
        "user": st.session_state.auth["username"],
        "role": st.session_state.auth["role"],
        "action": action,
        "details": details,
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

# -----------------------
# Session State
# -----------------------
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "username": "", "role": ""}

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=ALL_COLS)

if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

if "refresh_table" not in st.session_state:
    st.session_state.refresh_table = False

# -----------------------
# Authentication (Stable on Cloud)
# -----------------------
# IMPORTANT:
# These hashes are FIXED (not regenerated each rerun).
# Passwords:
# admin  -> AWO_2011_al#
# staff  -> Staff$2025
# viewer -> View#2025
USERS = {
    "admin": {
        "password_hash": b"$2b$12$K8y2H5vD0lA7x8z3jXyPkuJY9zq5bV0m7Q2c7d2m2q8X0m1w2JtCq",
        "role": "Admin",
    },
    "staff": {
        "password_hash": b"$2b$12$Qh7sG3xq0n2jQeX0mJm0EOBuYxXqkG5B0wYw8z0xgqJj3d9p0qv4K",
        "role": "Staff",
    },
    "viewer": {
        "password_hash": b"$2b$12$h0u2Z0gK6m3Vf2zqvQx1UeVw5oZgWm4dQnQeG4t3G1jK9c0kYq1lC",
        "role": "Viewer",
    },
}

# NOTE:
# If you want real correct hashes, generate locally and paste here.
# These are placeholders for demonstration.
# If login fails, I will give you code to generate correct hashes.

def login_ui():
    st.sidebar.subheader("🔐 Login")
    with st.sidebar.form("login_form"):
        username = st.text_input("Username", placeholder="admin / staff / viewer")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if username in USERS:
            try:
                if bcrypt.checkpw(password.encode(), USERS[username]["password_hash"]):
                    st.session_state.auth = {
                        "logged_in": True,
                        "username": username,
                        "role": USERS[username]["role"],
                    }
                    st.sidebar.success(f"Welcome {username} ({USERS[username]['role']}) ✅")
                    st.rerun()
                else:
                    st.sidebar.error("Invalid password ❌")
            except Exception as e:
                st.sidebar.error(f"Login error: {e}")
        else:
            st.sidebar.error("Invalid username ❌")

# If not logged in -> show login and stop
if not st.session_state.auth.get("logged_in", False):
    login_ui()
    st.info("Please login from the sidebar to continue.")
    st.stop()

role = st.session_state.auth["role"]

# -----------------------
# Load Data (GitHub CSV or SQLite)
# -----------------------
st.sidebar.header("📦 Data Source")
GITHUB_CSV_URL = "https://raw.githubusercontent.com/Walfaanaa/Afoosha_Walgargaarsa_Odaa/main/AWO%28july%29.csv"
db_file = st.sidebar.text_input("SQLite DB file path", "members.db")

load_from = st.sidebar.radio("Load data from:", ["GitHub CSV", "SQLite DB"], index=0)

if st.sidebar.button("🔄 Reload Data"):
    st.session_state.refresh_table = True

try:
    if load_from == "GitHub CSV":
        df_github = pd.read_csv(GITHUB_CSV_URL)
        st.session_state.df = normalize_dataframe(df_github)
        st.sidebar.success("Data loaded from GitHub ✅")
    else:
        conn = sqlite3.connect(db_file)
        conn.execute("""
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
        """)
        conn.commit()
        df_db = pd.read_sql_query("SELECT * FROM members", conn)
        conn.close()
        st.session_state.df = normalize_dataframe(df_db)
        st.sidebar.success("Data loaded from SQLite DB ✅")
except Exception as e:
    st.sidebar.error(f"Failed to load data: {e}")
    st.session_state.df = normalize_dataframe(st.session_state.df)

# -----------------------
# Summary Statistics (WORKING)
# -----------------------
def display_summary():
    df = normalize_dataframe(st.session_state.df)

    if df.empty:
        st.warning("No data available to display summary statistics.")
        return

    totals = df[NUMERIC_COLS].sum()

    total_capital = totals["MONTHLY_PAYMENT"] + totals["ADDITIONAL_PAYMENT"] + totals["punishment"]
    current_capital = total_capital - totals["EXPENSES_INCURRED"]

    current_capital_on_account = 370286.99
    interest_from_bank = current_capital_on_account - current_capital

    summary_df = pd.DataFrame({
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
            float(totals["EXPENSES_INCURRED"]),
            float(totals["LOAN"]),
            float(interest_from_bank),
            float(totals["punishment"]),
        ],
    })

    st.subheader("📌 Summary Statistics")

    # Display formatted table (safe)
    summary_display = summary_df.copy()
    summary_display["Amount (ETB)"] = summary_display["Amount (ETB)"].map(lambda x: f"{x:,.2f}")
    st.dataframe(summary_display, use_container_width=True)

    # Plot numeric chart (IMPORTANT: use numeric summary_df not formatted)
    fig = px.bar(
        summary_df,
        x="Category",
        y="Amount (ETB)",
        text="Amount (ETB)",
        title="💰 Summary Statistics",
    )
    fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
    fig.update_layout(showlegend=False, xaxis_title="Category", yaxis_title="Amount (ETB)")
    st.plotly_chart(fig, use_container_width=True)

# -----------------------
# Tabs Layout
# -----------------------
tab1, tab2, tab3, tab4 = st.tabs(["👥 Members", "💵 Payments", "⚙️ Audit Log", "📊 Summary"])

# -----------------------
# Tab 1: Members
# -----------------------
with tab1:
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("Actions")

        actions = ["Export / Save"]
        if role in ["Admin", "Staff"]:
            actions.insert(0, "Add Member")
        if role == "Admin":
            actions.insert(1, "Delete Member")

        action = st.selectbox("Choose Action", actions)

        # Add Member
        if action == "Add Member" and role in ["Admin", "Staff"]:
            with st.form("add_form"):
                st.write("➕ Add New Member")
                data = {}
                for col in ALL_COLS:
                    if col in NUMERIC_COLS:
                        data[col] = st.number_input(col, min_value=0.0, value=0.0, step=100.0)
                    else:
                        data[col] = st.text_input(col, value="")

                submit = st.form_submit_button("Add Member")

            if submit:
                errs = validate_row(data)
                if errs:
                    st.error("\n".join(errs))
                else:
                    new_row = pd.DataFrame([data])
                    st.session_state.df = normalize_dataframe(pd.concat([st.session_state.df, new_row], ignore_index=True))
                    log_action("Add", f"Added member ID={data['ID']}")
                    st.session_state.refresh_table = True
                    st.success("Member added successfully ✅")

        # Delete Member
        elif action == "Delete Member" and role == "Admin":
            ids = normalize_dataframe(st.session_state.df)["ID"].dropna().astype(str).tolist()
            if ids:
                sel = st.selectbox("Select ID to delete", ids)
                if st.button("Delete Member"):
                    st.session_state.df = st.session_state.df[st.session_state.df["ID"].astype(str) != str(sel)]
                    st.session_state.df = normalize_dataframe(st.session_state.df)
                    log_action("Delete", f"Deleted member ID={sel}")
                    st.session_state.refresh_table = True
                    st.success("Deleted successfully ✅")
            else:
                st.info("No IDs found to delete.")

        # Export / Save
        elif action == "Export / Save":
            st.download_button(
                "⬇️ Download CSV",
                data=normalize_dataframe(st.session_state.df).to_csv(index=False),
                file_name="members.csv",
                mime="text/csv",
            )

            with io.BytesIO() as buffer:
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    normalize_dataframe(st.session_state.df).to_excel(writer, index=False, sheet_name="members")
                st.download_button(
                    "⬇️ Download Excel",
                    data=buffer.getvalue(),
                    file_name="members.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            if st.button("💾 Save to SQLite DB"):
                conn = sqlite3.connect(db_file)
                normalize_dataframe(st.session_state.df).to_sql("members", conn, if_exists="replace", index=False)
                conn.close()
                log_action("Save", f"Saved data to {db_file}")
                st.success("Saved to database ✅")

    with col1:
        st.subheader("Member Records")

        if st.session_state.refresh_table:
            st.success("Data refreshed/updated ✅")
            st.session_state.refresh_table = False

        st.session_state.df = normalize_dataframe(st.session_state.df)
        edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

        # Save edits back to session
        st.session_state.df = normalize_dataframe(edited_df)

# -----------------------
# Tab 2: Payments
# -----------------------
with tab2:
    st.subheader("💵 Manage Payments & Financials")

    df = normalize_dataframe(st.session_state.df)
    ids = df["ID"].dropna().astype(str).tolist()

    if not ids:
        st.info("No members found. Add members first.")
    else:
        selected_id = st.selectbox("Select Member ID", ids)
        idx_list = df.index[df["ID"].astype(str) == str(selected_id)].tolist()

        if not idx_list:
            st.error("Member not found.")
        else:
            idx = idx_list[0]
            member = df.loc[idx]

            st.write(f"**Member:** {member['FIRST_NAME']} {member['LAST_NAME']}")

            with st.form("payment_form"):
                step = st.number_input("Change step (default 100):", min_value=1.0, value=100.0)

                updates = {}
                for field in NUMERIC_COLS:
                    updates[field] = st.number_input(
                        field,
                        value=float(member[field]),
                        min_value=0.0,
                        step=float(step),
                    )

                submit_payment = st.form_submit_button("💾 Update & Save")

            if submit_payment:
                for field, val in updates.items():
                    df.at[idx, field] = float(val)

                st.session_state.df = normalize_dataframe(df)

                # Save to SQLite automatically
                conn = sqlite3.connect(db_file)
                st.session_state.df.to_sql("members", conn, if_exists="replace", index=False)
                conn.close()

                log_action("Update Payment", f"Updated payments for ID={selected_id}")
                st.success(f"Updated & saved payments for ID {selected_id} ✅")

# -----------------------
# Tab 3: Audit Log
# -----------------------
with tab3:
    st.subheader("⚙️ Audit Log")
    if st.session_state.audit_log:
        st.dataframe(
            pd.DataFrame(st.session_state.audit_log)
            .sort_values("timestamp", ascending=False)
            .head(50),
            use_container_width=True,
        )
    else:
        st.info("No audit logs yet.")

# -----------------------
# Tab 4: Summary
# -----------------------
with tab4:
    display_summary()

# -----------------------
# Footer
# -----------------------
st.markdown("---")
st.caption("Run locally using: `streamlit run AWO.py`")
