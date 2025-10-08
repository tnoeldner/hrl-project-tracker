import sys
sys.path.insert(0, r'C:\Users\troy.noeldner\OneDrive - North Dakota University System\Documents\ProjectReporter\hrl-project-tracker')
import data_manager as dm
print('Attempting to load notifications...')
df = dm.load_table('notifications')
print('Result type:', type(df))
if df is not None:
    print('Rows:', len(df))
    print(df.head().to_dict(orient='records'))
else:
    print('No df returned')
