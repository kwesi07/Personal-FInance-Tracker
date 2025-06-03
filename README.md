Expense Tracker

Description

A Python-based command-line application for personal finance management, featuring user authentication, AI-driven expense categorization, budget tracking, and spending visualizations. Uses SQLite for persistent storage, Pandas for analytics, scikit-learn for machine learning, and Matplotlib for charts. Designed to showcase Python, database, and AI skills for tech/finance roles.

Features





User Authentication: Register and login with secure password hashing.



Expense Tracking: Add expenses with automatic or manual categorization.



AI Categorization: Uses scikit-learn to categorize expenses based on descriptions.



Budget Management: Set monthly budgets per category with spending alerts.



Analytics: View expense summaries, budgets, and bar charts (JSON and PNG output).

Prerequisites





Python 3.8+



pip



Git

Setup Instructions





Clone repository:

git clone https://github.com/kwesi-owusuofori/Expense-Tracker.git
cd Expense-Tracker



Install dependencies:

pip install -r requirements.txt



Prepare training_data.csv:





Ensure csv exists with columns description,category.



Example provided in repository.



Run application:

python expense_tracker.py --help

Usage

# Register user
python expense_tracker.py register --username alice --password pass123

# Login
python expense_tracker.py login --username alice --password pass123

# Add expense (AI or manual category)
python expense_tracker.py add --user_id 1 --description "Starbucks coffee" --amount 5.50
python expense_tracker.py add --user_id 1 --description "Uber ride" --amount 15.00 --category Transport

# Set budget
python expense_tracker.py set-budget --user_id 1 --category Food --amount 200 --month 2025-06

# View budgets
python expense_tracker.py view-budget --user_id 1

# View expenses
python expense_tracker.py view-expenses --user_id 1

# View summary with JSON and chart
python expense_tracker.py view-summary --user_id 1

Sample Output

Summary saved to summary.json:
{'Food': 5.5, 'Transport': 15.0}
Chart saved to summary.png
[Image opens in default viewer]

Troubleshooting





Database Errors: Ensure expenses.db has write permissions (chmod +w expenses.db).



AI Model: Verify training_data.csv exists. Retrain by deleting model.pkl.



Chart Issues: Ensure Matplotlib is installed (pip show matplotlib). Check summary.png.



Dependencies: Run pip install -r requirements.txt if errors occur.

Notes





Portfolio: Demonstrates Python, SQLite, Pandas, scikit-learn, and Matplotlib.



Future Enhancements: GUI, web deployment, OCR for receipts.