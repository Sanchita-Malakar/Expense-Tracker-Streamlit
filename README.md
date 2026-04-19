# ₹ Expense Tracker Pro – Advanced Personal Finance Analytics

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://expense-tracker-app-sanchita4yjcxgzrvtf75zuggzmtcp.streamlit.app/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Live interactive dashboard** for tracking expenses, income, budgets, and savings – built for Data Analyst / Business Analyst / Financial Analyst roles.

👉 **Live Demo**: [https://expense-tracker-app-sanchita4yjcxgzrvtf75zuggzmtcp.streamlit.app/]  
📂 **GitHub Repo**: [github.com/yourusername/Expense-Tracker-Streamlit](https://github.com/Sanchita-Malakar/Expense-Tracker-Streamlit)

---

## 📌 Overview

This project is a **complete personal finance management system** that allows users to:
- Track expenses and income with an intuitive UI
- Visualise spending trends with interactive Plotly charts
- Set monthly budgets and monitor overspending
- Import CSV files with flexible column mapping
- Generate actionable financial insights automatically

All data is stored in **SQLite** (local database) and the app runs entirely in the browser using **Streamlit**. Synthetic data is seeded on first run – no real financial data required.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **💰 Dual Tracking** | Expenses + Income – separate tables, combined analytics |
| **📊 Interactive Charts** | Monthly trends, category breakdowns, payment method pies, heatmaps |
| **🎯 Budget vs Actual** | Set monthly budgets per category, see progress bars and alerts |
| **📝 CRUD Operations** | Add, edit, delete expenses/income with inline data editor |
| **📤 CSV Import** | Upload any CSV – map columns, remap categories, skip duplicates |
| **🧠 Smart Insights** | Savings rate, overspending alerts, personalised recommendations |
| **📅 Synthetic Data** | Realistic synthetic generator (seasonal patterns, weekend spikes) |
| **💾 Persistent Storage** | SQLite database – all changes saved locally |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend / UI | [Streamlit](https://streamlit.io/) |
| Database | [SQLite3](https://www.sqlite.org/) |
| Data Processing | Pandas, NumPy |
| Visualisation | Plotly Express + Graph Objects |
| Data Generation | Python (random, datetime) |
| Deployment | Streamlit Community Cloud / Render |

---

## 📸 Screenshots

### Dashboard Overview
![Dashboard Overview](images/dashboard_overview.png)

### Income Tracker
![Income Tracker](images/income_tracker.png)

### Budget vs Actual
![Budget vs Actual](images/budget_vs_actual.png)

### Smart Insights
![Insights](images/insights_recommendations.png)

### CSV Import Interface
![CSV Import](images/csv_import.png)

---

## 🚀 Getting Started (Local Setup)

### Prerequisites
- Python 3.9 or higher
- Git (optional)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/Expense-Tracker-Streamlit.git
cd Expense-Tracker-Streamlit

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
streamlit run app.py
