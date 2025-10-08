import sys
sys.path.insert(0, r'C:\Users\troy.noeldner\OneDrive - North Dakota University System\Documents\ProjectReporter\hrl-project-tracker')
from ics_export import generate_ics_from_df
import pandas as pd

all_df = pd.DataFrame([{'TASK':'All Day Event','START':'2025-10-10','END':'2025-10-10','PLANNER BUCKET':'Admin','Fiscal Year':2025}])
print('--- ALL DAY ---')
print(generate_ics_from_df(all_df).decode('utf-8'))

timed_df = pd.DataFrame([{'TASK':'Timed Event','START':'2025-10-10 14:30','END':'2025-10-10 15:30','PLANNER BUCKET':'Admin','Fiscal Year':2025}])
print('--- TIMED ---')
print(generate_ics_from_df(timed_df).decode('utf-8'))
