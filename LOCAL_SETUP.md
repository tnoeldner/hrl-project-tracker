Local setup
===========

If you want to run the app locally without a cloud DB, initialize the local SQLite database used by the app.

1. Ensure you have Python dependencies installed:

```powershell
pip install -r requirements.txt
```

2. Run the initializer script from the project root:

```powershell
python init_local_db.py
```

This will create `project_tracker.db` in the project root and populate tables: `tasks`, `users`, `settings`, `bucket_icons`, `comments`, `changelog`, `notifications`.

3. Start the Streamlit app:

```powershell
streamlit run Main.py
```

If you prefer to use your cloud DB, set `db_connection_string` in your Streamlit secrets file (`.streamlit/secrets.toml`).
