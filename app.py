from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from pathlib import Path
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_PATH = Path(__file__).with_name("hr_portal.db")

STATUSES = ["Applied", "Screening", "Interview Scheduled", "Selected", "Rejected", "Hired"]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                job_role TEXT NOT NULL,
                experience REAL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Applied',
                interview_date TEXT,
                interviewer TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        if count == 0:
            sample = [
                ("Aarav Sharma", "aarav@example.com", "9876500001", "Python Developer", 2, "Interview Scheduled", "2026-11-02T10:30", "Priya Shah", "Strong Python basics"),
                ("Diya Patil", "diya@example.com", "9876500002", "HR Analyst", 1.5, "Screening", "", "", "Review analytics project"),
                ("Kabir Mehta", "kabir@example.com", "9876500003", "Frontend Developer", 3, "Selected", "", "", "Good portfolio"),
                ("Anaya Joshi", "anaya@example.com", "9876500004", "Python Developer", 4, "Hired", "", "", "Joined"),
                ("Vivaan Rao", "vivaan@example.com", "9876500005", "Data Analyst", 2, "Rejected", "", "", "Role mismatch"),
            ]
            conn.executemany("""
                INSERT INTO candidates
                (name,email,phone,job_role,experience,status,interview_date,interviewer,notes,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, [(*r, datetime.now().strftime("%Y-%m-%d %H:%M")) for r in sample])

@app.route("/")
def dashboard():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        hired = conn.execute("SELECT COUNT(*) FROM candidates WHERE status='Hired'").fetchone()[0]
        interviews = conn.execute("SELECT COUNT(*) FROM candidates WHERE status='Interview Scheduled'").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM candidates WHERE status IN ('Applied','Screening','Interview Scheduled','Selected')").fetchone()[0]
        roles = conn.execute("SELECT job_role, COUNT(*) AS total FROM candidates GROUP BY job_role ORDER BY total DESC").fetchall()
        status_counts = conn.execute("SELECT status, COUNT(*) AS total FROM candidates GROUP BY status").fetchall()
        recent = conn.execute("SELECT * FROM candidates ORDER BY id DESC LIMIT 5").fetchall()
    conversion = round((hired / total) * 100, 1) if total else 0
    return render_template("dashboard.html", total=total, hired=hired, interviews=interviews,
                           active=active, roles=roles, status_counts=status_counts,
                           recent=recent, conversion=conversion)

@app.route("/candidates")
def candidates():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    query = "SELECT * FROM candidates WHERE 1=1"
    args = []
    if search:
        query += " AND (name LIKE ? OR email LIKE ? OR job_role LIKE ?)"
        args.extend([f"%{search}%"] * 3)
    if status:
        query += " AND status=?"
        args.append(status)
    query += " ORDER BY id DESC"
    with get_db() as conn:
        rows = conn.execute(query, args).fetchall()
    return render_template("candidates.html", candidates=rows, statuses=STATUSES, q=search, selected_status=status)

@app.route("/candidate/add", methods=["GET", "POST"])
def add_candidate():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("job_role", "").strip()
        if not name or not email or not role:
            flash("Name, email, and job role are required.", "error")
            return redirect(url_for("add_candidate"))
        try:
            experience = max(0, float(request.form.get("experience") or 0))
        except ValueError:
            experience = 0
        with get_db() as conn:
            conn.execute("""
                INSERT INTO candidates
                (name,email,phone,job_role,experience,status,interview_date,interviewer,notes,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (name, email, request.form.get("phone", "").strip(), role, experience,
                  request.form.get("status", "Applied"), request.form.get("interview_date", ""),
                  request.form.get("interviewer", "").strip(), request.form.get("notes", "").strip(),
                  datetime.now().strftime("%Y-%m-%d %H:%M")))
        flash("Candidate added successfully.", "success")
        return redirect(url_for("candidates"))
    return render_template("candidate_form.html", statuses=STATUSES, candidate=None, page_title="Add Candidate")

@app.route("/candidate/<int:candidate_id>/edit", methods=["GET", "POST"])
def edit_candidate(candidate_id):
    with get_db() as conn:
        candidate = conn.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone()
        if not candidate:
            flash("Candidate not found.", "error")
            return redirect(url_for("candidates"))
        if request.method == "POST":
            try:
                experience = max(0, float(request.form.get("experience") or 0))
            except ValueError:
                experience = 0
            conn.execute("""
                UPDATE candidates SET name=?, email=?, phone=?, job_role=?, experience=?,
                status=?, interview_date=?, interviewer=?, notes=? WHERE id=?
            """, (request.form.get("name", "").strip(), request.form.get("email", "").strip(),
                  request.form.get("phone", "").strip(), request.form.get("job_role", "").strip(),
                  experience, request.form.get("status", "Applied"), request.form.get("interview_date", ""),
                  request.form.get("interviewer", "").strip(), request.form.get("notes", "").strip(), candidate_id))
            flash("Candidate details updated.", "success")
            return redirect(url_for("candidates"))
    return render_template("candidate_form.html", statuses=STATUSES, candidate=candidate, page_title="Edit Candidate")

@app.route("/candidate/<int:candidate_id>/delete", methods=["POST"])
def delete_candidate(candidate_id):
    with get_db() as conn:
        conn.execute("DELETE FROM candidates WHERE id=?", (candidate_id,))
    flash("Candidate deleted.", "success")
    return redirect(url_for("candidates"))

@app.route("/interviews")
def interviews():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM candidates
            WHERE interview_date IS NOT NULL AND interview_date != ''
            ORDER BY interview_date
        """).fetchall()
    return render_template("interviews.html", interviews=rows)

@app.route("/analytics")
def analytics():
    with get_db() as conn:
        status_counts = conn.execute("SELECT status, COUNT(*) AS total FROM candidates GROUP BY status ORDER BY total DESC").fetchall()
        role_counts = conn.execute("SELECT job_role, COUNT(*) AS total FROM candidates GROUP BY job_role ORDER BY total DESC").fetchall()
        hires_by_role = conn.execute("SELECT job_role, COUNT(*) AS total FROM candidates WHERE status='Hired' GROUP BY job_role ORDER BY total DESC").fetchall()
        avg_exp = conn.execute("SELECT AVG(experience) FROM candidates WHERE status='Hired'").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        hired = conn.execute("SELECT COUNT(*) FROM candidates WHERE status='Hired'").fetchone()[0]
    return render_template("analytics.html", status_counts=status_counts, role_counts=role_counts,
                           hires_by_role=hires_by_role, avg_exp=round(avg_exp or 0, 1),
                           total=total, hired=hired, conversion=round(hired * 100 / total, 1) if total else 0)

@app.route("/reports.csv")
def export_report():
    with get_db() as conn:
        rows = conn.execute("SELECT id,name,email,phone,job_role,experience,status,interview_date,interviewer,created_at FROM candidates ORDER BY id").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Phone", "Job Role", "Experience (years)", "Status", "Interview Date", "Interviewer", "Applied At"])
    writer.writerows([tuple(row) for row in rows])
    memory = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    memory.seek(0)
    return send_file(memory, mimetype="text/csv", as_attachment=True, download_name="hr_recruitment_report.csv")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
