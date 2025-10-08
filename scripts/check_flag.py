import sys
sys.path.insert(0, r'C:\Users\troy.noeldner\OneDrive - North Dakota University System\Documents\ProjectReporter\hrl-project-tracker')
import data_manager as dm
print('Loading bucket_icons...')
df = dm.load_table('bucket_icons')
print('Rows:', None if df is None else len(df))
print('Flag before pop:', dm.BUCKET_ICONS_AUTO_CREATED)
print('Pop returns:', dm.pop_bucket_icons_auto_created())
print('Flag after pop:', dm.BUCKET_ICONS_AUTO_CREATED)
