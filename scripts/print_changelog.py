import sys
sys.path.insert(0, r'C:\Users\troy.noeldner\OneDrive - North Dakota University System\Documents\ProjectReporter\hrl-project-tracker')
import data_manager as dm
ch = dm.load_table('changelog')
print('changelog rows:', None if ch is None else len(ch))
if ch is not None:
    print(ch.tail().to_dict(orient='records'))
