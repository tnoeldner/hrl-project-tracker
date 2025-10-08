from flask import Flask, request, Response
import sys
import os

# Make sure project root is importable
proj_root = os.path.dirname(__file__)
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

import data_manager
import ics_export
import pandas as pd

app = Flask(__name__)

@app.route('/calendar.ics')
def calendar_feed():
    """Return an ICS calendar for all tasks or filtered by query params.

    Query params supported:
    - bucket: planner bucket name (exact match)
    - year: fiscal year (string or number)
    """
    try:
        df = data_manager.load_table('tasks')
        if df is None:
            return Response('No data available', status=500)

        bucket = request.args.get('bucket')
        year = request.args.get('year')

        if bucket:
            df = df[df['PLANNER BUCKET'] == bucket]
        if year:
            df = df[df['Fiscal Year'].astype(str) == str(year)]

        # Keep only rows with START and END
        df = df[pd.notna(df['START']) & pd.notna(df['END'])]

        ics_bytes = ics_export.generate_ics_from_df(df, calendar_name='HRL Project Tracker')
        return Response(ics_bytes, mimetype='text/calendar')
    except Exception as e:
        return Response(f'Error generating calendar: {e}', status=500)

if __name__ == '__main__':
    # Default host/port; can be changed by environment variables
    host = os.environ.get('CALENDAR_SERVER_HOST', '0.0.0.0')
    port = int(os.environ.get('CALENDAR_SERVER_PORT', 5005))
    app.run(host=host, port=port)
