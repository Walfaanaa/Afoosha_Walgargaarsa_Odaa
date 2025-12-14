# -----------------------
# Streamlit_Afoosha_walgargaarsa_Odaa.py
# Fully Updated Version with Fixed Current_capital_on_account
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
# Initialize Session State
# -----------------------
if 'auth' not in st.session_state:
    st.session_state.auth = {'logged_in': False, 'username': '', 'role': ''}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=[
        'ID','FIRST_NAME','LAST_NAME','MONTHLY_PAYMENT','ADDITIONAL_PAYMENT',
        'EXPENSES_INCURRED','LOAN','OPENINNG_DATE','PHONE_NUM','Email','punishment'
    ])

if 'audit_log' not in st.session_state:
    st.session_state.audit_log = []

if 'refresh_table' not in st.session_state:
    st.session_state.refresh_table = False

# -----------------------
# Authentication
# -----------------------
USERS = {
    'admin': {'password_hash': bcrypt.hashpw(b"AWO_2011_al#", bcrypt.gensalt()), 'role': 'Admin'},
    'staff': {'password_hash': bcrypt.hashpw(b"Staff$2025", bcrypt.gensalt()), 'role': 'Staff'},
    'viewer': {'password_hash': bcrypt.hashpw(b"View#2025", bcrypt.gensalt()), 'role': 'Viewer'}
}

def login():
    with st.form('login_form'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submit = st.form_submit_button('Login')
        if submit:
            if username in USERS and bcrypt.checkpw(password.encode(), USERS[username]['password_hash']):
                st.session_state.auth = {'logged_in': True, 'username': username, 'role': USERS[username]['role']}
                st.success(f"Welcome {username} ({USERS[username]['role']})")
            else:
                st.error('Invalid credentials')

if not st.session_state.auth.get('logged_in', False):
    st.sidebar.warning('Please log in to continue')
    login()
    st.stop()

role = st.session_state.auth['role']

# -----------------------
# Data Loading
# -----------------------
PHONE_RE = re.compile(r"^[0-9]{7,15}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

st.sidebar.header('Data Source')
GITHUB_CSV_URL = "https://raw.githubusercontent.com/Walfaanaa/Afoosha_Walgargaarsa_Odaa/main/AWO%28july%29.csv"

try:
    df_github = pd.read_csv(GITHUB_CSV_URL)
    st.session_state.df = df_github
    st.sidebar.success("Data loaded from GitHub ✅")
except Exception as e:
    st.sidebar.warning(f"Failed to load from GitHub: {e}")
    db_file = st.sidebar.text_input('SQLite DB file path', 'members.db')
    conn = sqlite3.connect(db_file)
    conn.execute('''CREATE TABLE IF NOT EXISTS members (
        ID INTEGER PRIMARY KEY,
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
    )''')
    conn.commit()
    st.session_state.df = pd.read_sql_query('SELECT * FROM members', conn)
    conn.close()

# -----------------------
# Audit Log Function
# -----------------------
def log_action(action, details):
    st.session_state.audit_log.append({
        'user': st.session_state.auth['username'],
        'role': role,
        'action': action,
        'details': details,
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# -----------------------
# Row Validation
# -----------------------
def validate_row(row):
    errors = []
    if not re.match(PHONE_RE, str(row['PHONE_NUM'])):
        errors.append('Invalid phone number')
    if not re.match(EMAIL_RE, str(row['Email'])):
        errors.append('Invalid email')
    return errors

# -----------------------
# Tabs Layout
# -----------------------
tab1, tab2, tab3, tab4 = st.tabs(["👥 Members", "💵 Payments", "⚙️ Audit Log", "🔒 Profile"])

# -----------------------
# Tab 1: Members Management
# -----------------------
with tab1:
    col1, col2 = st.columns([2,1])
    with col2:
        st.subheader('Actions')
        actions = ['Export / Save']
        if role in ['Admin','Staff']:
            actions.insert(0, 'Add Member')
        if role == 'Admin':
            actions.insert(1, 'Delete Member')
        action = st.selectbox('Choose Action', actions)

        # Add Member
        if action == 'Add Member' and role in ['Admin','Staff']:
            with st.form('add_form'):
                data = {col: st.text_input(col, value="") for col in st.session_state.df.columns}
                submit = st.form_submit_button('Add')
                if submit:
                    errs = validate_row(data)
                    if errs:
                        st.error("\n".join(errs))
                    else:
                        numeric_cols = ['MONTHLY_PAYMENT','ADDITIONAL_PAYMENT','EXPENSES_INCURRED','LOAN','punishment']
                        for col in numeric_cols:
                            try:
                                data[col] = float(data[col])
                            except (ValueError, TypeError):
                                data[col] = 0.0
                        new_row = pd.DataFrame([data])
                        for col in st.session_state.df.columns:
                            if col not in new_row.columns:
                                new_row[col] = pd.NA
                        new_row = new_row[st.session_state.df.columns]
                        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                        log_action('Add', f"Added ID {data['ID']}")
                        st.session_state.refresh_table = True

        # Delete Member
        elif action == 'Delete Member' and role == 'Admin':
            ids = st.session_state.df['ID'].astype(str).tolist()
            sel = st.selectbox('Select ID to delete', ids)
            if st.button('Delete'):
                st.session_state.df = st.session_state.df[st.session_state.df['ID'].astype(str)!=sel]
                log_action('Delete', f"Deleted ID {sel}")
                st.session_state.refresh_table = True

        # Export / Save
        elif action == 'Export / Save':
            st.download_button('Download CSV', st.session_state.df.to_csv(index=False), 'members.csv')
            with io.BytesIO() as buffer:
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    st.session_state.df.to_excel(writer, index=False)
                st.download_button('Download Excel', buffer.getvalue(), 'members.xlsx')
            if st.button('Save to DB'):
                db_file = st.sidebar.text_input('SQLite DB file path', 'members.db')
                conn = sqlite3.connect(db_file)
                st.session_state.df.to_sql('members', conn, if_exists='replace', index=False)
                conn.close()
                log_action('Save', f"Saved to {db_file}")
                st.success('Data saved to database')

    with col1:
        st.subheader('Member Records')
        if st.session_state.refresh_table:
            st.success("Member data updated successfully!")
            st.session_state.refresh_table = False
        st.data_editor(st.session_state.df, num_rows="dynamic")

# -----------------------
# Tab 2: Payments Management
# -----------------------
with tab2:
    st.subheader("💵 Manage Payments & Financials")
    editable_fields = ['MONTHLY_PAYMENT','ADDITIONAL_PAYMENT','EXPENSES_INCURRED','LOAN','punishment']
    member_ids = st.session_state.df['ID'].astype(str).tolist()
    if member_ids:
        selected_id = st.selectbox("Select Member ID", member_ids)
        idx = st.session_state.df['ID'].astype(str).eq(selected_id).idxmax()
        member = st.session_state.df.loc[idx]
        st.write(f"**{member['FIRST_NAME']} {member['LAST_NAME']}**")

        with st.form("payment_form"):
            increment_value = float(st.number_input("Change step (default 100):", min_value=1.0, value=100.0))
            updates = {}
            for field in editable_fields:
                current_val = 0.0 if pd.isna(member[field]) else float(member[field])
                updates[field] = st.number_input(
                    field,
                    value=current_val,
                    min_value=0.0,
                    step=increment_value
                )
            submit_payment = st.form_submit_button("💾 Update & Save")
            if submit_payment:
                for field, val in updates.items():
                    st.session_state.df.at[idx, field] = val
                    log_action('Update Payment', f"{field} of ID {selected_id} set to {val}")
                db_file = st.sidebar.text_input('SQLite DB file path', 'members.db')
                conn = sqlite3.connect(db_file)
                st.session_state.df.to_sql('members', conn, if_exists='replace', index=False)
                conn.close()
                st.success(f"All payment fields updated and saved for ID {selected_id}")

# -----------------------
# Tab 3: Audit Log
# -----------------------
with tab3:
    st.subheader("⚙️ Audit Log")
    st.dataframe(pd.DataFrame(st.session_state.audit_log).tail(50))

# -----------------------
# Tab 4: Profile / Change Username & Password
# -----------------------
with tab4:
    st.subheader("🔒 Change Username / Password")
    current_username = st.session_state.auth['username']
    new_username = st.text_input("New Username", value=current_username)
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    if st.button("Update Credentials"):
        if new_password != confirm_password:
            st.error("Passwords do not match!")
        elif len(new_password) < 8:
            st.error("Password too short! Must be at least 8 characters.")
        else:
            USERS[new_username] = USERS.pop(current_username)
            USERS[new_username]['password_hash'] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
            st.session_state.auth['username'] = new_username
            st.success("Username and/or password updated successfully!")
            log_action("Update Credentials", f"{current_username} changed username/password to {new_username}")

# -----------------------
# Footer
# -----------------------
st.markdown('---')
st.caption('Run using: `streamlit run Streamlit_Afoosha_walgargaarsa_Odaa.py`')

# -----------------------
# 📊 Summary Statistics Section
# -----------------------
st.markdown("## 📊 Summary Statistics")

if not st.session_state.df.empty:
    totals = st.session_state.df[['MONTHLY_PAYMENT', 'ADDITIONAL_PAYMENT', 'EXPENSES_INCURRED', 'LOAN', 'punishment']].sum()
    
    Total_capital = totals['MONTHLY_PAYMENT'] + totals['ADDITIONAL_PAYMENT'] + totals['punishment']
    Current_capital = Total_capital - totals['EXPENSES_INCURRED']

    # Fixed current capital on account
    Current_capital_on_account = 368_682.90
    Interest_from_bank = Current_capital - Current_capital_on_account

    summary_df = pd.DataFrame({
        'Category': [
            'Total Capital',
            'Current Capital',
            'Current Capital on Account',
            'Interest from Bank'
        ],
        'Amount (ETB)': [
            Total_capital,
            Current_capital,
            Current_capital_on_account,
            Interest_from_bank
        ]
    })

    st.dataframe(summary_df, use_container_width=True)

    # Color-coded Plotly chart
    colors = ['blue', 'red', 'green', 'orange']
    fig = px.bar(
        summary_df,
        x='Category',
        y='Amount (ETB)',
        text='Amount (ETB)',
        title='💰 Summary Statistics',
        color='Category',
        color_discrete_sequence=colors
    )
    fig.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Amount (ETB)",
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No data available to display summary statistics.")
