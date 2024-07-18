import csv
from datetime import datetime

EXP_FILE = 'expenses.csv'
INC_FILE = 'income.csv'

CATEGORIES = ['Food',  'Transport',  'Utilities',  'Fun',  'Health',  'Other']

def add_income(date,  source,  amount):
    with open(INC_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([date,  source,  amount])

def add_expense(date,  category,  description,  amount):
    with open(EXP_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([date,  category,  description,  amount])

def view_expenses():
    try:
        with open(EXP_FILE, mode='r') as file:
            reader = csv.reader(file)
            expenses = list(reader)
            for index, expense in enumerate(expenses):
                print(f"{index}: Date: {expense[0]}, Category: {expense[1]}, Description: {expense[2]}, Amount: {expense[3]}")
    except FileNotFoundError:
        print("No expenses recorded yet.")

def delete_expense(index):
    try:
        with open(EXP_FILE, mode='r') as file:
            reader = csv.reader(file)
            expenses = list(reader)

        if 0 <= index < len(expenses):
            expenses.pop(index)
            with open(EXP_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(expenses)
            print("Expense deleted successfully.")
        else:
            print("Invalid index.")
    except FileNotFoundError:
        print("No expenses recorded yet.")

def generate_report():
    try:
        with open(EXP_FILE, mode='r') as file:
            reader = csv.reader(file)
            expenses = list(reader)

            report = {}
            for expense in expenses:
                category = expense[1]
                amount = float(expense[3])
                if category in report:
                    report[category] += amount
                else:
                    report[category] = amount

            for category, total in report.items():
                print(f"Category: {category}, Total Spent: ${total:.2f}")
    except FileNotFoundError:
        print("No expenses recorded yet.")

def calculate_balance():
    total_income = 0.0
    total_expenses = 0.0

    try:
        with open(INC_FILE, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                total_income += float(row[2])
    except FileNotFoundError:
        pass

    try:
        with open(EXP_FILE, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                total_expenses += float(row[3])
    except FileNotFoundError:
        pass

    balance = total_income - total_expenses
    print(f"Total Income: ${total_income:.2f}")
    print(f"Total Expenses: ${total_expenses:.2f}")
    print(f"Remaining Balance: ${balance:.2f}")

def main():
    while True:
        print("\nExpense Tracker")
        print("1. Add Income")
        print("2. Add Expense")
        print("3. View Expenses")
        print("4. Delete Expense")
        print("5. Generate Report")
        print("6. Calculate Balance")
        print("7. Exit")

        choice = input("Select an option: ")

        if choice == '1':
            date = input("Set the date (DD-MM-YYYY): ")
            source = input("Set the income source: ")
            amount = input("Set the amount from income: ")
            add_income(date,  source,  amount)
        elif choice == '2':
            date = input("Set the date (DD-MM-YYYY): ")
            print("Select a category:")
            for i, category in enumerate(CATEGORIES, 1):
                print(f"{i}. {category}")
            category_choice = int(input("Set the the number corresponding to the category: "))
            if 1 <= category_choice <= len(CATEGORIES):
                category = CATEGORIES[category_choice - 1]
            else:
                category = 'Other'
            description = input("Set the description of the expense: ")
            amount = input("Set the amount in the expense: ")
            add_expense(date,  category,  description,  amount)
        elif choice == '3':
            view_expenses()
        elif choice == '4':
            index = int(input("Select the index of the expense to be deleted: "))
            delete_expense(index)
        elif choice == '5':
            generate_report()
        elif choice == '6':
            calculate_balance()
        elif choice == '7':
            break
        else:
            print("Invalid choice. Please select a valid choice.")

if __name__ == "__main__":
    main()
