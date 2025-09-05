# 💰 Streamlit Expense Tracker

## 🚀 Live Demo

Try the app here:  
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-username-your-repo-name.streamlit.app)

---

A simple yet powerful **expense and income tracking app** built with [Streamlit](https://streamlit.io/).  
Track your spending, manage budgets, set recurring transactions, and visualize your finances with charts and KPIs.

---

## 🚀 Features
- Add **Income** and **Expense** with category, description, and date.
- Manage records with **inline editing** and **multi-delete**.
- Set **Monthly Budgets** per category with utilization tracking.
- Define **Recurring Transactions** (daily/weekly/monthly/yearly).
- Visual **Dashboard** with KPIs, category bar chart, and cashflow line chart.
- Sidebar **filters** (date range, categories, min/max amount).
- Import/Export **CSV files** for expenses, income, and recurring.
- Manage categories dynamically.
- Files auto-create on first run (no manual setup needed).

---

## 🛠️ Installation
Clone the repo:
```bash
git clone https://github.com/your-username/streamlit-expense-tracker.git
cd streamlit-expense-tracker
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Run the app:
```bash
streamlit run app.py
```

---

## 🌐 Deployment

You can deploy this project for free on:

- **[Streamlit Cloud](https://share.streamlit.io)** (recommended)

### Steps:
1. Push this repo to GitHub.
2. Log in to **Streamlit Cloud**.
3. Select your repo → set `app.py` as the entry point.
4. Add `requirements.txt` in your repo (already provided here).
5. Deploy! 🎉

---

## 📂 File Storage

The app automatically creates and updates:

- `expenses.csv` → All expenses  
- `income.csv` → All incomes  
- `recurring.csv` → Recurring transactions  
- `settings.json` → Category settings  
- `budgets.json` → Budget settings  

No need to add these manually.  

---

## 📊 Demo Data (Optional)

If you’d like your app to show **sample data** on first run, include pre-filled CSVs in the repo.  
Otherwise, the app will generate empty files the first time you add data.  

---

## 📜 License

MIT License © 2025 Shivesh Kumar

