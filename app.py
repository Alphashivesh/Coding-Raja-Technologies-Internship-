import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import json
import os

# ==========================
# ---- App Configuration ----
# ==========================
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💸",
    layout="wide",
)

# --------------------------
# ---- File Definitions ----
# --------------------------
EXP_FILE = 'expenses.csv'
INC_FILE = 'income.csv'
REC_FILE = 'recurring.csv'
CFG_FILE = 'settings.json'  # stores categories
BUDGET_FILE = 'budgets.json'  # stores monthly budgets per category

DEFAULT_CATEGORIES = ['Food', 'Transport', 'Utilities', 'Fun', 'Health', 'Other']

# ---------------------------
# ---- Utility Functions ----
# ---------------------------

def ensure_files_exist():
    if not os.path.exists(EXP_FILE):
        pd.DataFrame(columns=["date", "category", "description", "amount"]).to_csv(EXP_FILE, index=False)
    if not os.path.exists(INC_FILE):
        pd.DataFrame(columns=["date", "source", "amount"]).to_csv(INC_FILE, index=False)
    if not os.path.exists(REC_FILE):
        pd.DataFrame(columns=["type", "category_or_source", "description", "amount", "frequency", "next_date"]).to_csv(REC_FILE, index=False)
    if not os.path.exists(CFG_FILE):
        with open(CFG_FILE, 'w') as f:
            json.dump({"categories": DEFAULT_CATEGORIES}, f, indent=2)
    if not os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, 'w') as f:
            json.dump({}, f, indent=2)


def load_categories():
    try:
        with open(CFG_FILE, 'r') as f:
            cfg = json.load(f)
        cats = cfg.get("categories", DEFAULT_CATEGORIES)
        if not isinstance(cats, list) or len(cats) == 0:
            return DEFAULT_CATEGORIES
        return cats
    except Exception:
        return DEFAULT_CATEGORIES


def save_categories(categories):
    with open(CFG_FILE, 'w') as f:
        json.dump({"categories": categories}, f, indent=2)


def load_budgets():
    try:
        with open(BUDGET_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def save_budgets(budgets: dict):
    with open(BUDGET_FILE, 'w') as f:
        json.dump(budgets, f, indent=2)


def read_expenses():
    try:
        df = pd.read_csv(EXP_FILE)
        # Ensure headers exist
        expected_cols = ["date", "category", "description", "amount"]
        if df.empty or not all(col in df.columns for col in expected_cols):
            df = pd.DataFrame(columns=expected_cols)
        else:
            df['date'] = pd.to_datetime(df['date'], errors="coerce").dt.date
        return df
    except FileNotFoundError:
        # Create file with headers if not exists
        df = pd.DataFrame(columns=["date", "category", "description", "amount"])
        df.to_csv(EXP_FILE, index=False)
        return df



def read_income():
    df = pd.read_csv(INC_FILE)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
    return df


def read_recurring():
    df = pd.read_csv(REC_FILE)
    if not df.empty:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        df['next_date'] = pd.to_datetime(df['next_date']).dt.date
    return df


def write_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False)


# ---------------------------
# ---- Recurring Engine  ----
# ---------------------------

def add_period(d: date, freq: str) -> date:
    if freq == 'daily':
        return d + timedelta(days=1)
    if freq == 'weekly':
        return d + timedelta(weeks=1)
    if freq == 'monthly':
        # Add ~1 month by advancing to next month same day when possible
        month = d.month + 1
        year = d.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = min(d.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
        return date(year, month, day)
    if freq == 'yearly':
        try:
            return date(d.year + 1, d.month, d.day)
        except ValueError:
            # Feb 29 -> Feb 28 next year
            return date(d.year + 1, d.month, 28)
    return d


def process_recurring_transactions():
    """Apply due recurring transactions up to today, then bump next_date accordingly."""
    rec = read_recurring()
    if rec.empty:
        return

    expenses = read_expenses()
    income = read_income()

    today = date.today()
    changed = False

    for idx, row in rec.iterrows():
        r_type = str(row['type']).strip().lower()
        freq = str(row['frequency']).strip().lower()
        next_dt: date = row['next_date']
        while pd.notna(next_dt) and next_dt <= today:
            amt = float(row['amount'])
            name = str(row['category_or_source'])
            if r_type == 'expense':
                new_row = {
                    'date': next_dt,
                    'category': name,
                    'description': row.get('description', ''),
                    'amount': amt,
                }
                expenses = pd.concat([expenses, pd.DataFrame([new_row])], ignore_index=True)
                changed = True
            elif r_type == 'income':
                new_row = {
                    'date': next_dt,
                    'source': name,
                    'amount': amt,
                }
                income = pd.concat([income, pd.DataFrame([new_row])], ignore_index=True)
                changed = True
            next_dt = add_period(next_dt, freq)
        rec.at[idx, 'next_date'] = next_dt

    if changed:
        # Normalize date/amount types before saving
        if not expenses.empty:
            expenses['date'] = pd.to_datetime(expenses['date']).dt.date
            expenses['amount'] = pd.to_numeric(expenses['amount'], errors='coerce').fillna(0.0)
            write_csv(expenses, EXP_FILE)
        if not income.empty:
            income['date'] = pd.to_datetime(income['date']).dt.date
            income['amount'] = pd.to_numeric(income['amount'], errors='coerce').fillna(0.0)
            write_csv(income, INC_FILE)
        write_csv(rec, REC_FILE)


# ---------------------------
# ---- Sidebar Filters  ----
# ---------------------------

def sidebar_filters(expenses: pd.DataFrame, income: pd.DataFrame, categories: list):
    st.sidebar.header("Filters")
    # Date range defaults: this month
    today = date.today()
    first_of_month = today.replace(day=1)
    min_date = min([
        first_of_month,
        expenses['date'].min() if not expenses.empty else first_of_month,
        income['date'].min() if not income.empty else first_of_month,
    ])
    max_date = max([
        today,
        expenses['date'].max() if not expenses.empty else today,
        income['date'].max() if not income.empty else today,
    ])

    date_range = st.sidebar.date_input(
        "Date range",
        value=(first_of_month, today),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date, end_date = first_of_month, today

    cat_sel = st.sidebar.multiselect("Categories", options=categories, default=categories)

    min_amt = float(st.sidebar.number_input("Min amount", min_value=0.0, value=0.0, step=100.0))
    max_amt = float(st.sidebar.number_input("Max amount (0 = no cap)", min_value=0.0, value=0.0, step=100.0))

    return start_date, end_date, cat_sel, min_amt, max_amt


def apply_filters(df: pd.DataFrame, start_date: date, end_date: date, categories: list, min_amt: float, max_amt: float):
    if df.empty:
        return df
    mask = (
        (df['date'] >= start_date) & (df['date'] <= end_date)
    )
    if 'category' in df.columns and categories:
        mask &= df['category'].isin(categories)
    if 'amount' in df.columns:
        mask &= df['amount'] >= min_amt
        if max_amt > 0:
            mask &= df['amount'] <= max_amt
    return df.loc[mask].copy()


# ---------------------------
# ---- Dashboard Charts  ----
# ---------------------------

def kpi_card(label: str, value: float):
    st.metric(label, f"₹{value:,.2f}")


def dashboard(expenses_f: pd.DataFrame, income_f: pd.DataFrame):
    st.subheader("Overview")
    total_exp = float(expenses_f['amount'].sum()) if not expenses_f.empty else 0.0
    total_inc = float(income_f['amount'].sum()) if not income_f.empty else 0.0
    balance = total_inc - total_exp

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Income (filtered)", total_inc)
    with c2:
        kpi_card("Expenses (filtered)", total_exp)
    with c3:
        kpi_card("Balance (filtered)", balance)

    st.divider()

    # Expenses by Category
    if not expenses_f.empty:
        by_cat = expenses_f.groupby('category', as_index=False)['amount'].sum()
        by_cat = by_cat.sort_values('amount', ascending=False)
        st.write("### Expenses by Category")
        st.bar_chart(by_cat.set_index('category'))

    # Cashflow over time
    if not expenses_f.empty or not income_f.empty:
        st.write("### Cashflow Over Time")
        exp_daily = expenses_f.groupby('date', as_index=False)['amount'].sum() if not expenses_f.empty else pd.DataFrame(columns=['date', 'amount'])
        inc_daily = income_f.groupby('date', as_index=False)['amount'].sum() if not income_f.empty else pd.DataFrame(columns=['date', 'amount'])
        exp_daily['amount'] = -exp_daily['amount']  # negative for expenses
        inc_daily['amount'] = inc_daily['amount']
        cash = pd.concat([exp_daily, inc_daily], ignore_index=True).sort_values('date')
        cash['cumulative'] = cash['amount'].cumsum()
        st.line_chart(cash.set_index('date')[['amount', 'cumulative']])


# ---------------------------
# ---- Budgets  ----
# ---------------------------

def budgets_ui(categories: list, expenses: pd.DataFrame):
    st.subheader("Monthly Budgets by Category")
    budgets = load_budgets()

    # Editor for budgets
    data = []
    for cat in categories:
        data.append({"category": cat, "budget": float(budgets.get(cat, 0.0))})
    df_b = pd.DataFrame(data)

    edited = st.data_editor(df_b, num_rows="dynamic", use_container_width=True, key="budget_editor")
    if st.button("Save Budgets", type="primary"):
        new_budgets = {row['category']: float(row['budget']) for _, row in edited.iterrows() if str(row['category']).strip()}
        save_budgets(new_budgets)
        st.success("Budgets saved!")
        st.rerun()

    # Utilization for current month
    if not expenses.empty:
        now = date.today()
        start_m = now.replace(day=1)
        end_m = (start_m + timedelta(days=40)).replace(day=1) - timedelta(days=1)
        month_exp = expenses[(expenses['date'] >= start_m) & (expenses['date'] <= end_m)]
        spent_by_cat = month_exp.groupby('category', as_index=False)['amount'].sum() if not month_exp.empty else pd.DataFrame(columns=['category', 'amount'])
        st.write("### This Month: Budget Utilization")
        for cat in categories:
            budget = float(budgets.get(cat, 0.0))
            spent = float(spent_by_cat.loc[spent_by_cat['category'] == cat, 'amount'].sum()) if not spent_by_cat.empty else 0.0
            pct = 0 if budget <= 0 else min(100, (spent / budget) * 100)
            st.progress(int(pct), text=f"{cat}: Spent ₹{spent:,.2f} / Budget ₹{budget:,.2f} ({pct:.0f}%)")
            if budget > 0 and spent > budget:
                st.warning(f"Over budget in **{cat}** by ₹{spent - budget:,.2f}")


# ---------------------------
# ---- Manage Data UIs  ----
# ---------------------------

def add_transactions_ui(categories: list):
    st.subheader("Add Transactions")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Add Income")
        inc_date = st.date_input("Date", value=date.today(), key="inc_date")
        inc_source = st.text_input("Source", key="inc_source")
        inc_amount = st.number_input("Amount", min_value=0.0, step=100.0, key="inc_amount")
        if st.button("Add Income", use_container_width=True, type="primary"):
            if inc_source and inc_amount > 0:
                df = read_income()
                df = pd.concat([df, pd.DataFrame([{ 'date': inc_date, 'source': inc_source, 'amount': float(inc_amount)}])], ignore_index=True)
                write_csv(df, INC_FILE)
                st.success("Income added")
                st.rerun()
            else:
                st.error("Please provide a source and an amount > 0")

    with c2:
        st.markdown("#### Add Expense")
        exp_date = st.date_input("Date ", value=date.today(), key="exp_date")
        exp_category = st.selectbox("Category", options=categories, index=0, key="exp_cat")
        exp_desc = st.text_input("Description", key="exp_desc")
        exp_amount = st.number_input("Amount ", min_value=0.0, step=100.0, key="exp_amount")
        if st.button("Add Expense", use_container_width=True, type="primary"):
            if exp_category and exp_amount > 0:
                df = read_expenses()
                df = pd.concat([df, pd.DataFrame([{ 'date': exp_date, 'category': exp_category, 'description': exp_desc, 'amount': float(exp_amount)}])], ignore_index=True)
                write_csv(df, EXP_FILE)
                st.success("Expense added")
                st.rerun()
            else:
                st.error("Please provide a category and an amount > 0")


def manage_expenses_ui(expenses: pd.DataFrame, categories: list):
    st.subheader("Manage Expenses")
    if expenses.empty:
        st.info("No expenses yet.")
        return

    # Provide editing via data_editor
    editable = expenses.copy()
    editable = editable.sort_values('date', ascending=False).reset_index(drop=True)
    editable['date'] = pd.to_datetime(editable['date'])

    edited = st.data_editor(
        editable,
        column_config={
            'date': st.column_config.DateColumn("date", format="YYYY-MM-DD"),
            'category': st.column_config.SelectboxColumn("category", options=categories),
            'description': st.column_config.TextColumn("description"),
            'amount': st.column_config.NumberColumn("amount", step=100.0, min_value=0.0),
        },
        use_container_width=True,
        num_rows="fixed",
        key="expense_table",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Save Changes", type="primary"):
            # Normalize and save
            edited['date'] = pd.to_datetime(edited['date']).dt.date
            edited['amount'] = pd.to_numeric(edited['amount'], errors='coerce').fillna(0.0)
            write_csv(edited, EXP_FILE)
            st.success("Saved changes")
            st.rerun()
    with col2:
        del_idx = st.multiselect("Select rows to delete", options=edited.index.tolist(), help="Pick by row number from the table above")
        if st.button("Delete Selected", type="secondary"):
            remaining = edited.drop(index=del_idx)
            remaining['date'] = pd.to_datetime(remaining['date']).dt.date
            remaining['amount'] = pd.to_numeric(remaining['amount'], errors='coerce').fillna(0.0)
            write_csv(remaining, EXP_FILE)
            st.success(f"Deleted {len(del_idx)} rows")
            st.rerun()


def manage_income_ui(income: pd.DataFrame):
    st.subheader("Manage Income")
    if income.empty:
        st.info("No income yet.")
        return

    editable = income.copy().sort_values('date', ascending=False).reset_index(drop=True)
    editable['date'] = pd.to_datetime(editable['date'])

    edited = st.data_editor(
        editable,
        column_config={
            'date': st.column_config.DateColumn("date", format="YYYY-MM-DD"),
            'source': st.column_config.TextColumn("source"),
            'amount': st.column_config.NumberColumn("amount", step=100.0, min_value=0.0),
        },
        use_container_width=True,
        num_rows="fixed",
        key="income_table",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Save Income Changes", type="primary"):
            edited['date'] = pd.to_datetime(edited['date']).dt.date
            edited['amount'] = pd.to_numeric(edited['amount'], errors='coerce').fillna(0.0)
            write_csv(edited, INC_FILE)
            st.success("Saved changes")
            st.rerun()
    with col2:
        del_idx = st.multiselect("Select rows to delete", options=edited.index.tolist(), key="inc_del_idx")
        if st.button("Delete Selected Income"):
            remaining = edited.drop(index=del_idx)
            remaining['date'] = pd.to_datetime(remaining['date']).dt.date
            remaining['amount'] = pd.to_numeric(remaining['amount'], errors='coerce').fillna(0.0)
            write_csv(remaining, INC_FILE)
            st.success(f"Deleted {len(del_idx)} rows")
            st.rerun()


# ---------------------------
# ---- Recurring UI  ----
# ---------------------------

def recurring_ui(categories: list):
    st.subheader("Recurring Transactions")

    # Form to add recurring
    with st.expander("Add New Recurring"):
        r_type = st.radio("Type", ["expense", "income"], horizontal=True)
        name_label = "Category" if r_type == 'expense' else "Source"
        if r_type == 'expense':
            name = st.selectbox(name_label, options=categories)
            desc = st.text_input("Description")
        else:
            name = st.text_input(name_label)
            desc = ''
        amount = st.number_input("Amount", min_value=0.0, step=100.0)
        freq = st.selectbox("Frequency", options=["daily", "weekly", "monthly", "yearly"], index=2)
        next_dt = st.date_input("Next Date", value=date.today())
        if st.button("Add Recurring", type="primary"):
            df = read_recurring()
            new = {
                'type': r_type,
                'category_or_source': name,
                'description': desc,
                'amount': float(amount),
                'frequency': freq,
                'next_date': next_dt,
            }
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            write_csv(df, REC_FILE)
            st.success("Recurring transaction added")
            st.rerun()

    # Table
    rec = read_recurring()
    if rec.empty:
        st.info("No recurring transactions configured.")
        return

    rec_disp = rec.copy()
    rec_disp['next_date'] = pd.to_datetime(rec_disp['next_date'])
    edited = st.data_editor(
        rec_disp,
        column_config={
            'type': st.column_config.SelectboxColumn("type", options=['expense', 'income']),
            'category_or_source': st.column_config.TextColumn("category_or_source"),
            'description': st.column_config.TextColumn("description"),
            'amount': st.column_config.NumberColumn("amount", step=100.0, min_value=0.0),
            'frequency': st.column_config.SelectboxColumn("frequency", options=['daily', 'weekly', 'monthly', 'yearly']),
            'next_date': st.column_config.DateColumn("next_date", format="YYYY-MM-DD"),
        },
        use_container_width=True,
        num_rows="fixed",
        key="rec_table",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Save Recurring Changes", type="primary"):
            edited['next_date'] = pd.to_datetime(edited['next_date']).dt.date
            edited['amount'] = pd.to_numeric(edited['amount'], errors='coerce').fillna(0.0)
            write_csv(edited, REC_FILE)
            st.success("Saved changes")
            st.rerun()
    with col2:
        del_idx = st.multiselect("Select rows to delete", options=edited.index.tolist(), key="rec_del_idx")
        if st.button("Delete Selected Recurring"):
            remaining = edited.drop(index=del_idx)
            remaining['next_date'] = pd.to_datetime(remaining['next_date']).dt.date
            remaining['amount'] = pd.to_numeric(remaining['amount'], errors='coerce').fillna(0.0)
            write_csv(remaining, REC_FILE)
            st.success(f"Deleted {len(del_idx)} rows")
            st.rerun()


# ---------------------------
# ---- Import/Export  ----
# ---------------------------

def import_export_ui():
    st.subheader("Import / Export")

    st.markdown("#### Export Current Data")
    exp_bytes = open(EXP_FILE, 'rb').read() if os.path.exists(EXP_FILE) else b''
    inc_bytes = open(INC_FILE, 'rb').read() if os.path.exists(INC_FILE) else b''
    rec_bytes = open(REC_FILE, 'rb').read() if os.path.exists(REC_FILE) else b''

    st.download_button("Download expenses.csv", data=exp_bytes, file_name="expenses.csv")
    st.download_button("Download income.csv", data=inc_bytes, file_name="income.csv")
    st.download_button("Download recurring.csv", data=rec_bytes, file_name="recurring.csv")

    st.divider()

    st.markdown("#### Import / Merge CSVs")
    st.caption("Uploaded rows are appended. Column names must match the target file.")

    up_exp = st.file_uploader("Upload expenses.csv", type=['csv'], key="up_exp")
    if up_exp is not None:
        new = pd.read_csv(up_exp)
        cur = read_expenses()
        merged = pd.concat([cur, new], ignore_index=True)
        # Normalize types
        if not merged.empty:
            merged['date'] = pd.to_datetime(merged['date']).dt.date
            merged['amount'] = pd.to_numeric(merged['amount'], errors='coerce').fillna(0.0)
        write_csv(merged, EXP_FILE)
        st.success("Merged expenses.csv")
        st.rerun()

    up_inc = st.file_uploader("Upload income.csv", type=['csv'], key="up_inc")
    if up_inc is not None:
        new = pd.read_csv(up_inc)
        cur = read_income()
        merged = pd.concat([cur, new], ignore_index=True)
        if not merged.empty:
            merged['date'] = pd.to_datetime(merged['date']).dt.date
            merged['amount'] = pd.to_numeric(merged['amount'], errors='coerce').fillna(0.0)
        write_csv(merged, INC_FILE)
        st.success("Merged income.csv")
        st.rerun()

    up_rec = st.file_uploader("Upload recurring.csv", type=['csv'], key="up_rec")
    if up_rec is not None:
        new = pd.read_csv(up_rec)
        cur = read_recurring()
        merged = pd.concat([cur, new], ignore_index=True)
        if not merged.empty:
            merged['amount'] = pd.to_numeric(merged['amount'], errors='coerce').fillna(0.0)
            merged['next_date'] = pd.to_datetime(merged['next_date']).dt.date
        write_csv(merged, REC_FILE)
        st.success("Merged recurring.csv")
        st.rerun()


# ---------------------------
# ---- Settings  ----
# ---------------------------

def settings_ui():
    st.subheader("Settings & Categories")
    categories = load_categories()

    st.write("### Manage Categories")
    st.caption("Rename, add, or remove categories. These are used for expenses and budgets.")

    df = pd.DataFrame({"category": categories})
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button("Save Categories", type="primary"):
        new_cats = [str(c).strip() for c in edited['category'].tolist() if str(c).strip()]
        if len(new_cats) == 0:
            st.error("You must have at least one category.")
        else:
            save_categories(new_cats)
            st.success("Saved categories")
            st.rerun()


# ---------------------------
# ---- Main App  ----
# ---------------------------

def main():
    ensure_files_exist()

    # Apply recurring transactions that are due
    process_recurring_transactions()

    categories = load_categories()
    expenses = read_expenses()
    income = read_income()

    # Sidebar filters
    start_date, end_date, cat_sel, min_amt, max_amt = sidebar_filters(expenses, income, categories)

    # Filtered views
    expenses_f = apply_filters(expenses, start_date, end_date, cat_sel, min_amt, max_amt)
    # For income, only filter by date/amount (no category)
    income_f = income.copy()
    if not income_f.empty:
        income_f = income_f[(income_f['date'] >= start_date) & (income_f['date'] <= end_date)]

    # Header
    st.title("💸 Expense Tracker")
    st.caption("CSV-backed personal finance app with budgets, recurring transactions, filters, charts, and import/export.")

    tabs = st.tabs(["Dashboard", "Add", "Expenses", "Income", "Budgets", "Recurring", "Import/Export", "Settings"]) 

    with tabs[0]:
        dashboard(expenses_f, income_f)

    with tabs[1]:
        add_transactions_ui(categories)

    with tabs[2]:
        manage_expenses_ui(expenses, categories)

    with tabs[3]:
        manage_income_ui(income)

    with tabs[4]:
        budgets_ui(categories, expenses)

    with tabs[5]:
        recurring_ui(categories)

    with tabs[6]:
        import_export_ui()

    with tabs[7]:
        settings_ui()


if __name__ == "__main__":
    main()
