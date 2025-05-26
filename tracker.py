import pandas as pd
import matplotlib.pyplot as plt
import json

# Read the CSV file
data = pd.read_csv('expenses.csv')

# Convert date to datetime and extract month-year
data['date'] = pd.to_datetime(data['date'])
data['month_year'] = data['date'].dt.strftime('%Y-%m')

# Group by category and sum amounts
category_summary = data.groupby('category')['amount'].sum()

# Group by month-year and sum amounts
monthly_summary = data.groupby('month_year')['amount'].sum()

# Save summaries to JSON
summary_dict = {
    'category_summary': category_summary.to_dict(),
    'monthly_summary': monthly_summary.to_dict()
}
with open('expense_summary.json', 'w') as f:
    json.dump(summary_dict, f, indent=4)

# Create a pie chart for categories
plt.figure(figsize=(8, 6))
plt.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%', startangle=90)
plt.title('Expense Breakdown by Category')
plt.savefig('expense_chart.png')
plt.show()

# Create a bar chart for monthly totals
plt.figure(figsize=(8, 6))
monthly_summary.plot(kind='bar')
plt.title('Monthly Expense Totals')
plt.xlabel('Month-Year')
plt.ylabel('Total Amount')
plt.savefig('monthly_expense_chart.png')
plt.show()