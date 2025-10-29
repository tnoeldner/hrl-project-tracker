from pathlib import Path
from data_manager import load_table, generate_calendar_from_tasks


def main():
    # Load tasks from the configured DB (works with local SQLite fallback)
    tasks = load_table('tasks')
    cal = generate_calendar_from_tasks(tasks)
    out = Path(__file__).parent / 'calendar.ics'
    out.write_bytes(cal.to_ical())
    print(f"Wrote calendar to: {out.resolve()}")


if __name__ == '__main__':
    main()
