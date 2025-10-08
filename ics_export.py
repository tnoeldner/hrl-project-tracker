import uuid
from datetime import datetime, timedelta, timezone
import pandas as pd


def _to_utc_string(ts: pd.Timestamp) -> str:
    """Convert a pandas Timestamp to a UTC 'YYYYMMDDTHHMMSSZ' string.

    - If ts is naive, treat it as local time (system local tz) and convert to UTC.
    - If ts has tzinfo, convert to UTC.
    """
    if pd.isna(ts):
        return None
    # ensure Timestamp
    ts = pd.to_datetime(ts)
    # If naive, assume local timezone
    if ts.tzinfo is None:
        try:
            local_tz = datetime.now().astimezone().tzinfo
            ts = ts.tz_localize(local_tz) if hasattr(ts, 'tz_localize') else ts.replace(tzinfo=local_tz)
        except Exception:
            # Fallback: assume UTC
            ts = ts.replace(tzinfo=timezone.utc)
    # Convert to UTC
    ts_utc = ts.astimezone(timezone.utc)
    return ts_utc.strftime('%Y%m%dT%H%M%SZ')


def _format_date(dt: pd.Timestamp):
    """Return tuple (is_all_day, formatted_date_or_dtstring).

    If the timestamp has no time component (00:00:00), treat as all-day and return a DATE string (YYYYMMDD).
    Otherwise, return a UTC datetime string (YYYYMMDDTHHMMSSZ) using _to_utc_string.
    """
    if pd.isna(dt):
        return None
    ts = pd.to_datetime(dt)
    # Check if time component is midnight (all-day)
    if ts.time() == datetime.min.time():
        return True, ts.strftime('%Y%m%d')
    return False, _to_utc_string(ts)


def _escape_text(text: str) -> str:
    if text is None:
        return ''
    # Basic escaping for comma, semicolon and newline per RFC
    return str(text).replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')


def generate_ics_from_df(df: pd.DataFrame, calendar_name: str = 'HRL Project Tracker') -> bytes:
    """Generate an ICS file (as bytes) from a DataFrame with at least the
    columns: 'TASK', 'START', 'END', 'PLANNER BUCKET', 'Fiscal Year'.

    START and END should be parsable by pandas.to_datetime.
    """
    lines = []
    lines.append('BEGIN:VCALENDAR')
    lines.append('VERSION:2.0')
    lines.append('PRODID:-//HRL Project Tracker//EN')
    lines.append('METHOD:PUBLISH')
    lines.append(f'X-WR-CALNAME:{_escape_text(calendar_name)}')
    lines.append('CALSCALE:GREGORIAN')

    now_stamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    has_timed = False
    for _, row in df.iterrows():
        start = row.get('START')
        end = row.get('END')
        if pd.isna(start) or pd.isna(end):
            continue

        start_ts = pd.to_datetime(start)
        end_ts = pd.to_datetime(end)

        is_all_day_start, start_str = _format_date(start_ts)
        is_all_day_end, end_str = _format_date(end_ts)

        if not (is_all_day_start and is_all_day_end):
            has_timed = True

        uid = str(uuid.uuid4()) + '@hrl-project-tracker'

        lines.append('BEGIN:VEVENT')
        lines.append(f'UID:{uid}')
        lines.append(f'DTSTAMP:{now_stamp}')

        # If both are all-day (date-only), use VALUE=DATE and RFC5545 exclusive DTEND
        if is_all_day_start and is_all_day_end:
            # make DTEND exclusive by adding one day to the end date
            end_exclusive = (end_ts + timedelta(days=1)).strftime('%Y%m%d')
            lines.append(f'DTSTART;VALUE=DATE:{start_str}')
            lines.append(f'DTEND;VALUE=DATE:{end_exclusive}')
        else:
            # Ensure we have Zulu times; if input lacked tz we used formatting with Z above
            lines.append(f'DTSTART:{start_str}')
            # For non all-day, make DTEND inclusive as provided
            lines.append(f'DTEND:{end_str}')

        summary = f"{row.get('PLANNER BUCKET','')} - {row.get('TASK','')}"
        description_parts = []
        if 'TASK' in row:
            description_parts.append(str(row.get('TASK')))
        if 'PLANNER BUCKET' in row:
            description_parts.append(f"Bucket: {row.get('PLANNER BUCKET')}")
        if 'Fiscal Year' in row:
            description_parts.append(f"FY: {row.get('Fiscal Year')}")
        description = '\n'.join([p for p in description_parts if p])

        lines.append(f'SUMMARY:{_escape_text(summary)}')
        if description:
            lines.append(f'DESCRIPTION:{_escape_text(description)}')

        lines.append('END:VEVENT')

    lines.append('END:VCALENDAR')

    # If there were timed events, include a simple VTIMEZONE for UTC to improve Outlook compatibility
    if has_timed:
        tz_lines = [
            'BEGIN:VTIMEZONE',
            'TZID:UTC',
            'BEGIN:STANDARD',
            'DTSTART:19700101T000000',
            'TZOFFSETFROM:+0000',
            'TZOFFSETTO:+0000',
            'TZNAME:UTC',
            'END:STANDARD',
            'END:VTIMEZONE'
        ]
        # Insert VTIMEZONE before END:VCALENDAR
        ics_text = '\r\n'.join(lines[:-1] + tz_lines + [lines[-1]]) + '\r\n'
    else:
        ics_text = '\r\n'.join(lines) + '\r\n'

    return ics_text.encode('utf-8')
