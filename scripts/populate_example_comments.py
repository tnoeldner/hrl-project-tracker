import sys
from datetime import datetime
sys.path.insert(0, r'C:\Users\troy.noeldner\OneDrive - North Dakota University System\Documents\ProjectReporter\hrl-project-tracker')
import data_manager as dm
import pandas as pd

print('Loading tasks and comments...')
tasks = dm.load_table('tasks')
comments = dm.load_table('comments')
users = dm.load_table('users')

if tasks is None:
    print('No tasks table found, aborting.')
    sys.exit(1)

if comments is None or comments.empty:
    print('Populating example comments...')
    example_comments = []
    # choose up to 5 tasks to attach demo comments
    sample_tasks = tasks.head(5)
    user_email = 'system@example.com'
    if users is not None and not users.empty:
        user_email = users.iloc[0]['email']

    comment_id = 1
    for _, t in sample_tasks.iterrows():
        tid = t['#']
        example_comments.append({'comment_id': comment_id, 'task_id': tid, 'user_email': user_email, 'timestamp': datetime.now(), 'comment_text': f"Demo comment for task {tid}: Please review the milestones."})
        comment_id += 1
        example_comments.append({'comment_id': comment_id, 'task_id': tid, 'user_email': user_email, 'timestamp': datetime.now(), 'comment_text': f"Second demo comment for task {tid}: Follow-up needed."})
        comment_id += 1

    new_comments_df = pd.DataFrame(example_comments)
    saved = dm.save_table(new_comments_df, 'comments')
    if saved:
        print('Example comments saved:', len(new_comments_df))
    else:
        print('Failed to save example comments.')
else:
    print('Comments table already has data (rows =', len(comments), '). No action taken.')
