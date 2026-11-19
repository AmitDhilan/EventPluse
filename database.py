import sqlite3
from datetime import datetime

DB_PATH = "eventpulse.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clubs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                coordinator TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                club_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                venue TEXT NOT NULL,
                event_date TEXT NOT NULL,
                capacity INTEGER NOT NULL DEFAULT 50,
                status TEXT NOT NULL DEFAULT 'Open',
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                student_name TEXT NOT NULL,
                student_email TEXT NOT NULL,
                roll_no TEXT NOT NULL,
                attendance_status TEXT NOT NULL DEFAULT 'Registered',
                registered_at TEXT NOT NULL,
                UNIQUE(event_id, student_email),
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
            """
        )

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if conn.execute("SELECT COUNT(*) AS c FROM clubs").fetchone()["c"] == 0:
            clubs_seed = [
                ("CodeCraft Club", "Dr. R. Sharma", "Technical", now),
                ("Design & Media Guild", "Prof. N. Verma", "Creative", now),
                ("Startup & Innovation Cell", "Prof. A. Joshi", "Entrepreneurship", now),
            ]
            conn.executemany(
                "INSERT INTO clubs (name, coordinator, category, created_at) VALUES (?, ?, ?, ?)",
                clubs_seed,
            )

        if conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"] == 0:
            c1 = conn.execute("SELECT id FROM clubs WHERE name = 'CodeCraft Club'").fetchone()["id"]
            c2 = conn.execute("SELECT id FROM clubs WHERE name = 'Design & Media Guild'").fetchone()["id"]
            c3 = conn.execute("SELECT id FROM clubs WHERE name = 'Startup & Innovation Cell'").fetchone()["id"]

            events_seed = [
                (c1, "Full-Stack Web Hackathon", "Main Auditorium", "2026-12-05", 80, "Open", "Build a complete web app in 12 hours", now),
                (c1, "Git & Backend API Workshop", "Lab 204", "2026-11-28", 40, "Open", "Hands-on Flask, REST APIs and SQLite session", now),
                (c2, "UI/UX & Poster Design Sprint", "Design Studio", "2026-12-02", 35, "Open", "Wireframing, typography and responsive layouts", now),
                (c3, "Pitch Deck & Startup Bootcamp", "Seminar Hall B", "2026-12-10", 60, "Open", "Idea validation, business model and pitching", now),
            ]
            conn.executemany(
                """
                INSERT INTO events (club_id, title, venue, event_date, capacity, status, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                events_seed,
            )

        if conn.execute("SELECT COUNT(*) AS c FROM registrations").fetchone()["c"] == 0:
            e1 = conn.execute("SELECT id FROM events WHERE title = 'Full-Stack Web Hackathon'").fetchone()["id"]
            e2 = conn.execute("SELECT id FROM events WHERE title = 'Git & Backend API Workshop'").fetchone()["id"]

            regs_seed = [
                (e1, "Riya Kumari", "riya@example.com", "CS2301", "Checked-In", now),
                (e1, "Karan Mehta", "karan@example.com", "CS2302", "Registered", now),
                (e2, "Ananya Patel", "ananya@example.com", "IT2304", "Registered", now),
            ]
            conn.executemany(
                """
                INSERT INTO registrations (event_id, student_name, student_email, roll_no, attendance_status, registered_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                regs_seed,
            )


def get_clubs():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT c.*, COUNT(e.id) AS event_count
            FROM clubs c
            LEFT JOIN events e ON e.club_id = c.id
            GROUP BY c.id
            ORDER BY c.name ASC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def add_club(name, coordinator, category):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO clubs (name, coordinator, category, created_at) VALUES (?, ?, ?, ?)",
            (name, coordinator, category, now),
        )
        row = conn.execute("SELECT * FROM clubs WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def get_events_and_overview(search="", club_id="All", status="All"):
    query = """
        SELECT
            e.*,
            c.name AS club_name,
            c.category AS club_category,
            COUNT(r.id) AS registered_count
        FROM events e
        JOIN clubs c ON c.id = e.club_id
        LEFT JOIN registrations r ON r.event_id = e.id
        WHERE 1=1
    """
    params = []

    if club_id != "All":
        query += " AND e.club_id = ?"
        params.append(int(club_id))

    if status != "All":
        query += " AND e.status = ?"
        params.append(status)

    query += " GROUP BY e.id ORDER BY e.event_date ASC, e.id DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        total_events = conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"]
        open_events = conn.execute("SELECT COUNT(*) AS c FROM events WHERE status = 'Open'").fetchone()["c"]
        total_regs = conn.execute("SELECT COUNT(*) AS c FROM registrations").fetchone()["c"]
        checked_in = conn.execute(
            "SELECT COUNT(*) AS c FROM registrations WHERE attendance_status = 'Checked-In'"
        ).fetchone()["c"]

    events = []
    q = search.strip().lower()
    for r in rows:
        item = dict(r)
        item["seats_left"] = max(0, item["capacity"] - item["registered_count"])
        if not q or q in item["title"].lower() or q in item["venue"].lower() or q in item["club_name"].lower():
            events.append(item)

    overview = {
        "total_events": total_events,
        "open_events": open_events,
        "total_registrations": total_regs,
        "checked_in": checked_in,
    }
    return events, overview


def create_event(club_id, title, venue, event_date, capacity, status, description):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_db() as conn:
        club = conn.execute("SELECT id FROM clubs WHERE id = ?", (club_id,)).fetchone()
        if not club:
            return None
        cur = conn.execute(
            """
            INSERT INTO events (club_id, title, venue, event_date, capacity, status, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (club_id, title, venue, event_date, capacity, status, description, now),
        )
        row = conn.execute(
            """
            SELECT e.*, c.name AS club_name, c.category AS club_category, 0 AS registered_count
            FROM events e
            JOIN clubs c ON c.id = e.club_id
            WHERE e.id = ?
            """,
            (cur.lastrowid,),
        ).fetchone()
    res = dict(row)
    res["seats_left"] = res["capacity"]
    return res


def update_event_status(event_id, new_status):
    with get_db() as conn:
        cur = conn.execute("UPDATE events SET status = ? WHERE id = ?", (new_status, event_id))
        if cur.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return dict(row)


def delete_event(event_id):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        return cur.rowcount > 0


def get_registrations(event_id=None):
    query = """
        SELECT r.*, e.title AS event_title, c.name AS club_name
        FROM registrations r
        JOIN events e ON e.id = r.event_id
        JOIN clubs c ON c.id = e.club_id
    """
    params = []
    if event_id:
        query += " WHERE r.event_id = ?"
        params.append(int(event_id))
    query += " ORDER BY r.id DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def register_student(event_id, student_name, student_email, roll_no):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_db() as conn:
        ev = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if not ev:
            return None, "Event not found.", 404
        if ev["status"] != "Open":
            return None, "Registrations are closed for this event.", 400

        reg_count = conn.execute(
            "SELECT COUNT(*) AS c FROM registrations WHERE event_id = ?", (event_id,)
        ).fetchone()["c"]
        if reg_count >= ev["capacity"]:
            return None, "Event seat capacity is full.", 409

        cur = conn.execute(
            """
            INSERT INTO registrations (event_id, student_name, student_email, roll_no, attendance_status, registered_at)
            VALUES (?, ?, ?, ?, 'Registered', ?)
            """,
            (event_id, student_name, student_email, roll_no, now),
        )
        row = conn.execute("SELECT * FROM registrations WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row), None, 201


def update_attendance(reg_id, attendance_status):
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE registrations SET attendance_status = ? WHERE id = ?",
            (attendance_status, reg_id),
        )
        if cur.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM registrations WHERE id = ?", (reg_id,)).fetchone()
    return dict(row)


def cancel_registration(reg_id):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM registrations WHERE id = ?", (reg_id,))
        return cur.rowcount > 0