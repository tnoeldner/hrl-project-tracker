import os,shutil,sys,runpy
proj_root = r'C:\Users\troy.noeldner\OneDrive - North Dakota University System\Documents\ProjectReporter\hrl-project-tracker'
db_path = os.path.join(proj_root, 'project_tracker.db')
backup_path = db_path + '.bak'

# Backup existing DB if present
if os.path.exists(db_path):
    print('Backing up existing DB...')
    shutil.copy2(db_path, backup_path)
    os.remove(db_path)
    print('Existing DB removed to simulate first-run.')

# Run the check scripts which will invoke auto-creation
sys.path.insert(0, proj_root)
print('Running bucket_icons check...')
runpy.run_path(os.path.join('scripts','check_bucket_icons.py'), run_name='__main__')
print('Running notifications check...')
runpy.run_path(os.path.join('scripts','check_notifications.py'), run_name='__main__')

# Now print the changelog
import data_manager as dm
changelog = dm.load_table('changelog')
print('Changelog rows:', None if changelog is None else len(changelog))
if changelog is not None:
    print(changelog.tail().to_dict(orient='records'))

# Restore DB if we backed it up
if os.path.exists(backup_path):
    shutil.copy2(backup_path, db_path)
    os.remove(backup_path)
    print('Original DB restored from backup.')
