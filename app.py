import csv
import io
import sqlite3
from flask import Flask, Response, jsonify, render_template, request
from database import (
    add_club,
    cancel_registration,
    create_event,
    delete_event,
    get_clubs,
    get_events_and_overview,
    get_registrations,
    init_db,
    register_student,
    update_attendance,
    update_event_status,
)

app = Flask(__name__)
init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/clubs", methods=["GET"])
def list_clubs_route():
    return jsonify({"clubs": get_clubs()})


@app.route("/api/clubs", methods=["POST"])
def create_club_route():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    coordinator = str(data.get("coordinator", "")).strip()
    category = str(data.get("category", "General")).strip() or "General"

    if not name or not coordinator:
        return jsonify({"error": "Club name and coordinator are required."}), 400

    try:
        club = add_club(name, coordinator, category)
        return jsonify({"club": club}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Club already exists."}), 409


@app.route("/api/events", methods=["GET"])
def list_events_route():
    search = request.args.get("search", "").strip()
    club_id = request.args.get("club_id", "All").strip()
    status = request.args.get("status", "All").strip()

    events, overview = get_events_and_overview(search=search, club_id=club_id, status=status)
    return jsonify({"events": events, "overview": overview})


@app.route("/api/events", methods=["POST"])
def create_event_route():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    venue = str(data.get("venue", "")).strip()
    event_date = str(data.get("event_date", "")).strip()
    status = str(data.get("status", "Open")).strip()
    description = str(data.get("description", "")).strip()

    try:
        club_id = int(data.get("club_id"))
        capacity = int(data.get("capacity", 50))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid club_id and numeric capacity are required."}), 400

    if not title or not venue or not event_date or capacity < 1:
        return jsonify({"error": "Title, venue, event_date, and capacity (>=1) are required."}), 400

    if status not in {"Open", "Closed", "Completed"}:
        status = "Open"

    ev = create_event(club_id, title, venue, event_date, capacity, status, description)
    if ev is None:
        return jsonify({"error": "Selected club does not exist."}), 404

    return jsonify({"event": ev}), 201


@app.route("/api/events/<int:event_id>", methods=["PATCH"])
def patch_event_route(event_id):
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()
    if status not in {"Open", "Closed", "Completed"}:
        return jsonify({"error": "Invalid event status."}), 400

    updated = update_event_status(event_id, status)
    if updated is None:
        return jsonify({"error": "Event not found."}), 404

    return jsonify({"event": updated})


@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def delete_event_route(event_id):
    if not delete_event(event_id):
        return jsonify({"error": "Event not found."}), 404
    return jsonify({"deleted": True, "id": event_id})


@app.route("/api/registrations", methods=["GET"])
def list_registrations_route():
    event_id_raw = request.args.get("event_id", "").strip()
    event_id = int(event_id_raw) if event_id_raw.isdigit() else None
    return jsonify({"registrations": get_registrations(event_id=event_id)})


@app.route("/api/registrations", methods=["POST"])
def create_registration_route():
    data = request.get_json(silent=True) or {}
    student_name = str(data.get("student_name", "")).strip()
    student_email = str(data.get("student_email", "")).strip().lower()
    roll_no = str(data.get("roll_no", "")).strip()

    try:
        event_id = int(data.get("event_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid event_id is required."}), 400

    if not student_name or not student_email or not roll_no:
        return jsonify({"error": "Student name, email, and roll number are required."}), 400

    try:
        reg, err_msg, code = register_student(event_id, student_name, student_email, roll_no)
        if err_msg:
            return jsonify({"error": err_msg}), code
        return jsonify({"registration": reg}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "This email is already registered for the selected event."}), 409


@app.route("/api/registrations/<int:reg_id>", methods=["PATCH"])
def patch_registration_route(reg_id):
    data = request.get_json(silent=True) or {}
    att = str(data.get("attendance_status", "")).strip()
    if att not in {"Registered", "Checked-In", "Absent"}:
        return jsonify({"error": "Invalid attendance status."}), 400

    updated = update_attendance(reg_id, att)
    if updated is None:
        return jsonify({"error": "Registration not found."}), 404
    return jsonify({"registration": updated})


@app.route("/api/registrations/<int:reg_id>", methods=["DELETE"])
def delete_registration_route(reg_id):
    if not cancel_registration(reg_id):
        return jsonify({"error": "Registration not found."}), 404
    return jsonify({"deleted": True, "id": reg_id})


@app.route("/api/export.csv", methods=["GET"])
def export_registrations_csv():
    regs = get_registrations()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Reg ID", "Club", "Event", "Student Name", "Roll No", "Email", "Attendance", "Registered At"])
    for r in regs:
        writer.writerow([
            r["id"],
            r["club_name"],
            r["event_title"],
            r["student_name"],
            r["roll_no"],
            r["student_email"],
            r["attendance_status"],
            r["registered_at"],
        ])

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=eventpulse_registrations.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)