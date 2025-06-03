import sqlite3
import argparse
import pandas as pd
from datetime import datetime
import bcrypt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import joblib
import os
import json
import matplotlib.pyplot as plt

# Initialize database
def init_db():
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date TEXT,
            category TEXT,
            amount REAL,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            category TEXT,
            month TEXT,
            amount REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

# Train or load AI model
def get_ai_model():
    model_file = "model.pkl"
    training_file = "training_data.csv"
    categories = ["Food", "Transport", "Music", "Social", "Tech", "Other"]
    
    if os.path.exists(model_file):
        return joblib.load(model_file), categories
    
    if not os.path.exists(training_file):
        raise FileNotFoundError("training_data.csv not found. Please provide training data.")
    
    df = pd.read_csv(training_file)
    model = make_pipeline(TfidfVectorizer(), LogisticRegression())
    model.fit(df["description"], df["category"])
    joblib.dump(model, model_file)
    return model, categories

# Register user
def register_user(username, password):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        print("User registered successfully!")
    except sqlite3.IntegrityError:
        print("Username already exists.")
    conn.close()

# Login user
def login_user(username, password):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode(), user[1]):
        return user[0]
    else:
        raise ValueError("Invalid username or password.")

# Add expense with AI categorization
def add_expense(user_id, description, amount, category=None):
    model, categories = get_ai_model()
    date = datetime.now().strftime("%Y-%m-%d")
    
    if not category:
        probas = model.predict_proba([description])[0]
        max_proba = max(probas)
        predicted = model.predict([description])[0]
        if max_proba >= 0.7:
            category = predicted
            print(f"AI categorized as: {category} (confidence: {max_proba:.2f})")
        else:
            print(f"AI unsure (confidence: {max_proba:.2f}). Please select category:")
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat}")
            choice = int(input("Enter choice: ")) - 1
            category = categories[choice]
    
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("INSERT INTO expenses (user_id, date, category, amount, description) VALUES (?, ?, ?, ?, ?)",
              (user_id, date, category, amount, description))
    conn.commit()
    
    # Check budget
    month = date[:7]  # YYYY-MM
    c.execute("SELECT amount FROM budgets WHERE user_id = ? AND category = ? AND month = ?",
              (user_id, category, month))
    budget = c.fetchone()
    if budget:
        budget_amount = budget[0]
        c.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND category = ? AND date LIKE ?",
                  (user_id, category, f"{month}%"))
        total_spent = c.fetchone()[0] or 0
        if total_spent > budget_amount:
            print(f"Warning: Exceeded {category} budget of ${budget_amount:.2f} (spent ${total_spent:.2f})!")
        elif total_spent > 0.9 * budget_amount:
            print(f"Alert: Approaching {category} budget of ${budget_amount:.2f} (spent ${total_spent:.2f})")
    
    conn.close()
    print("Expense added successfully!")

# Set budget
def set_budget(user_id, category, amount, month=None):
    if not month:
        month = datetime.now().strftime("%Y-%m")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO budgets (user_id, category, month, amount) VALUES (?, ?, ?, ?)",
              (user_id, category, month, amount))
    conn.commit()
    conn.close()
    print(f"Budget set: ${amount:.2f} for {category} in {month}")

# View budgets
def view_budgets(user_id):
    conn = sqlite3.connect("expenses.db")
    df = pd.read_sql_query("""
        SELECT b.category, b.month, b.amount AS budget, SUM(e.amount) AS spent
        FROM budgets b
        LEFT JOIN expenses e ON b.user_id = e.user_id AND b.category = e.category AND e.date LIKE b.month || '%'
        WHERE b.user_id = ?
        GROUP BY b.category, b.month
    """, conn, params=(user_id,))
    conn.close()
    if df.empty:
        print("No budgets set.")
    else:
        df["spent"] = df["spent"].fillna(0)
        df["remaining"] = df["budget"] - df["spent"]
        print("\nBudget Summary:")
        print(df[["category", "month", "budget", "spent", "remaining"]])

# View expenses
def view_expenses(user_id):
    conn = sqlite3.connect("expenses.db")
    df = pd.read_sql_query("SELECT date, category, amount, description FROM expenses WHERE user_id = ?",
                           conn, params=(user_id,))
    conn.close()
    if df.empty:
        print("No expenses found.")
    else:
        print("\nExpense Summary:")
        print(df.groupby("category")["amount"].sum())
        print("\nDetailed Expenses:")
        print(df)

# View summary with JSON output and Matplotlib chart
def view_summary(user_id):
    conn = sqlite3.connect("expenses.db")
    df = pd.read_sql_query("SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ? GROUP BY category",
                           conn, params=(user_id,))
    conn.close()
    
    if df.empty:
        print("No expenses to summarize.")
        return
    
    # JSON output
    summary = dict(zip(df["category"], df["total"]))
    with open("summary.json", "w") as f:
        json.dump(summary, f, indent=4)
    print("\nSummary saved to summary.json:")
    print(summary)
    
    # Matplotlib chart
    plt.figure(figsize=(10, 6))
    plt.bar(df["category"], df["total"], color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
    plt.xlabel("Category")
    plt.ylabel("Total Spent ($)")
    plt.title("Spending by Category")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("summary.png")
    plt.close()
    print("Chart saved to summary.png")
    # Open image (platform-specific)
    if os.name == "posix":  # macOS/Linux
        os.system("open summary.png")
    elif os.name == "nt":  # Windows
        os.system("start summary.png")

if __name__ == "__main__":
    init_db()
    parser = argparse.ArgumentParser(description="Expense Tracker CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Register
    reg_parser = subparsers.add_parser("register", help="Register new user")
    reg_parser.add_argument("--username", required=True)
    reg_parser.add_argument("--password", required=True)

    # Login
    login_parser = subparsers.add_parser("login", help="Login user")
    login_parser.add_argument("--username", required=True)
    login_parser.add_argument("--password", required=True)

    # Add expense
    add_parser = subparsers.add_parser("add", help="Add expense")
    add_parser.add_argument("--description", required=True)
    add_parser.add_argument("--amount", type=float, required=True)
    add_parser.add_argument("--category", choices=["Food", "Transport", "Music", "Social", "Tech", "Other"])
    add_parser.add_argument("--user_id", type=int, required=True)

    # Set budget
    budget_parser = subparsers.add_parser("set-budget", help="Set monthly budget")
    budget_parser.add_argument("--category", required=True)
    budget_parser.add_argument("--amount", type=float, required=True)
    budget_parser.add_argument("--month", help="YYYY-MM")
    budget_parser.add_argument("--user_id", type=int, required=True)

    # View budgets
    view_budget_parser = subparsers.add_parser("view-budget", help="View budgets")
    view_budget_parser.add_argument("--user_id", type=int, required=True)

    # View expenses
    view_exp_parser = subparsers.add_parser("view-expenses", help="View expenses")
    view_exp_parser.add_argument("--user_id", type=int, required=True)

    # View summary
    summary_parser = subparsers.add_parser("view-summary", help="View expense summary with JSON and chart")
    summary_parser.add_argument("--user_id", type=int, required=True)

    args = parser.parse_args()

    if args.command == "register":
        register_user(args.username, args.password)
    elif args.command == "login":
        user_id = login_user(args.username, args.password)
        print(f"Logged in as user ID: {user_id}")
    elif args.command == "add":
        add_expense(args.user_id, args.description, args.amount, args.category)
    elif args.command == "set-budget":
        set_budget(args.user_id, args.category, args.amount, args.month)
    elif args.command == "view-budget":
        view_budgets(args.user_id)
    elif args.command == "view-expenses":
        view_expenses(args.user_id)
    elif args.command == "view-summary":
        view_summary(args.user_id)