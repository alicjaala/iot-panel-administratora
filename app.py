from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_socketio import SocketIO
import requests
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tajny_klucz_do_sesji'

socketio = SocketIO(app)

BACKEND_URL = "http://127.0.0.1:5000"


def calculate_duration(start_str, end_str=None):
    try:
        start = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        if end_str:
            end = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        else:
            end = datetime.now()

        diff = end - start
        hours, remainder = divmod(diff.seconds, 3600)
        minutes = remainder // 60
        hours += diff.days * 24
        return f"{hours}h {minutes}m"
    except:
        return "-"


@app.route('/')
def dashboard():
    try:
        resp_lockers = requests.get(f"{BACKEND_URL}/api/lockers")
        resp_entries = requests.get(f"{BACKEND_URL}/api/history")

        if resp_lockers.status_code == 200 and resp_entries.status_code == 200:
            lockers_source = resp_lockers.json()
            entries_source = resp_entries.json()
        else:
            flash("Błąd pobierania danych z backendu (zły status)", "danger")
            lockers_source = []
            entries_source = []
    except requests.exceptions.RequestException:
        flash("Nie można połączyć się z serwerem backendu", "danger")
        lockers_source = []
        entries_source = []

    processed_lockers = []

    for row in lockers_source:
        nr = row['NR']
        uid = row['UID']
        is_occupied = (uid is not None)
        duration_str = ""

        if is_occupied:
            active_entry = next((e for e in entries_source if e['UID'] == uid and e['EXIT_TIMESTAMP'] is None), None)

            if active_entry:
                duration_str = calculate_duration(active_entry['ENTRY_TIMESTAMP'])
            else:
                duration_str = "Błąd czasu"

        processed_lockers.append({
            "id": nr,
            "number": nr,
            "is_occupied": is_occupied,
            "uid": uid,
            "time": duration_str
        })

    total = len(processed_lockers)
    occupied = sum(1 for l in processed_lockers if l['is_occupied'])
    free = total - occupied

    return render_template('panel.html', lockers=processed_lockers, total=total, occupied=occupied, free=free)


@app.route('/otworz/<int:locker_id>', methods=['POST'])
def open_locker(locker_id):
    try:
        requests.post(f"{BACKEND_URL}/api/open/{locker_id}")
    except requests.exceptions.RequestException:
        flash("Błąd połączenia podczas otwierania szafki", "danger")

    return redirect(url_for('dashboard'))


@app.route('/zwolnij/<int:locker_id>', methods=['POST'])
def release_locker(locker_id):
    try:
        requests.post(f"{BACKEND_URL}/api/release/{locker_id}")
    except requests.exceptions.RequestException:
        flash("Błąd połączenia podczas zwalniania szafki", "danger")

    return redirect(url_for('dashboard'))


@app.route('/historia')
def history():
    filter_type = request.args.get('filter', 'all')

    try:
        resp_entries = requests.get(f"{BACKEND_URL}/api/history")

        if resp_entries.status_code == 200:
            entries_source = resp_entries.json()
        else:
            entries_source = []
            flash("Błąd pobierania historii", "warning")

    except requests.exceptions.RequestException:
        flash("Błąd połączenia z historią", "danger")
        entries_source = []

    display_logs = []

    sorted_entries = sorted(entries_source, key=lambda x: x['ENTRY_TIMESTAMP'], reverse=True)

    for entry in sorted_entries:
        is_active = (entry['EXIT_TIMESTAMP'] is None)

        if filter_type == 'active' and not is_active:
            continue
        if filter_type == 'finished' and is_active:
            continue

        locker_nr = str(entry.get('NR')) if entry.get('NR') is not None else "-"

        display_logs.append({
            "card_uid": entry['UID'],
            "locker_number": locker_nr,
            "start_time": entry['ENTRY_TIMESTAMP'],
            "end_time": entry['EXIT_TIMESTAMP'],
            "duration": calculate_duration(entry['ENTRY_TIMESTAMP'], entry['EXIT_TIMESTAMP']),
            "is_active": is_active
        })

    return render_template('historia.html', logs=display_logs, active_filter=filter_type)


@app.route('/webhook/refresh', methods=['POST'])
def webhook_refresh():
    print("Odebrano sygnał webhook! Odświeżam przeglądarki...")
    socketio.emit('force_reload')
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)