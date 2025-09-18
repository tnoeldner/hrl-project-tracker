# file: check_columns.py
import pandas as pd

try:
    # Make sure the Excel file name and sheet name are correct here.
    df = pd.read_excel('Project Tracker.xlsx', sheet_name='DATA')
    
    # This will print the list of column names exactly as Python sees them.
    print("Your column names are:")
    print(df.columns.tolist())
    
except Exception as e:
    print(f"An error occurred: {e}")