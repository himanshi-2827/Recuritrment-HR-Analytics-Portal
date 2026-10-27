# HireWise — Recruitment & HR Analytics Portal

A beginner-friendly Python web application for managing job applications, candidate information, interview schedules, recruitment status, and hiring analytics.

## Features
- Dashboard with recruitment KPIs and pipeline chart
- Add, edit, search, filter, and delete candidates
- Track status: Applied, Screening, Interview Scheduled, Selected, Rejected, Hired
- Schedule interviews with date/time and interviewer
- HR analytics charts for status and role distribution
- CSV export of candidate recruitment records
- SQLite database created automatically with sample records
- Responsive interface using HTML, CSS, Chart.js, and Flask

## Run on Windows
1. Install Python 3.10 or newer.
2. Extract the ZIP folder.
3. Open Command Prompt inside the `hr_recruitment_analytics_portal` folder.
4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Start the website:
   ```bash
   python app.py
   ```
6. Open `http://127.0.0.1:5000` in your browser.

The SQLite database (`hr_portal.db`) is created on first run. Sample records are added only when the database is empty.

## Main files
- `app.py` — Flask routes, database operations, reporting
- `templates/` — HTML templates
- `static/style.css` — responsive styling
- `requirements.txt` — Python dependency

## Notes
This is a local educational/demo project. Before production use, add authentication and role-based permissions, CSRF protection, secure secret configuration, data retention controls, backups, and privacy safeguards. Candidate data is sensitive: use fictional data for demos and restrict access. Analytics are descriptive and should support, not replace, structured human evaluation.
