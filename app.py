from flask import Flask, render_template, redirect, url_for, flash, request
import requests
from datetime import datetime, timedelta


app = Flask(__name__)
app.config['SECRET_KEY'] = 'tajny_klucz_do_sesji'

# tu trzeba dać ip serwera, który będzie wysyłał jsony
BACKEND_URL = "http://127.0.0.1:5000"
MOCK_MODE = False

# WAŻNE RZECZY
# BACKEND MUSI MIEĆ DOKŁADNIE TAKIE ENDPOINTY (ALBO MY MUSIMY ZMIENIĆ TU)
# GET /api/szafki
# GET /api/historia
# POST /api/otworz/<id>
# POST /api/zwolnij/<id>

# muszą być dokładnie takie same klucze w jsonach
# musi być taki sam format daty


MOCK_LOCKERS_TABLE = [
                         {"NR": 1, "UID": None},
                         {"NR": 2, "UID": None},
                         {"NR": 3, "UID": "A1B2C3D4"},
                         {"NR": 4, "UID": None},
                         {"NR": 5, "UID": None},
                         {"NR": 6, "UID": None},
                         {"NR": 7, "UID": None},
                         {"NR": 8, "UID": "E5F6G7H8"},
                         {"NR": 9, "UID": None},
                         {"NR": 10, "UID": None},
                         {"NR": 11, "UID": None},
                         {"NR": 12, "UID": "I9J0K1L2"},
                         {"NR": 13, "UID": None},
                         {"NR": 14, "UID": None},
                         {"NR": 15, "UID": None},
                         {"NR": 16, "UID": "M3N4O5P6"},
                     ] + [{"NR": i, "UID": None} for i in range(17, 25)]

teraz = datetime.now()
MOCK_ENTRIES_TABLE = [
    {"ID": 101, "UID": "A1B2C3D4", "ENTRY_TIMESTAMP": (teraz - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
     "EXIT_TIMESTAMP": None},
    {"ID": 102, "UID": "E5F6G7H8",
     "ENTRY_TIMESTAMP": (teraz - timedelta(hours=2, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"), "EXIT_TIMESTAMP": None},
    {"ID": 103, "UID": "I9J0K1L2", "ENTRY_TIMESTAMP": (teraz - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
     "EXIT_TIMESTAMP": None},
    {"ID": 104, "UID": "M3N4O5P6",
     "ENTRY_TIMESTAMP": (teraz - timedelta(hours=1, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"), "EXIT_TIMESTAMP": None},

    {"ID": 50, "UID": "OLD_USER1", "ENTRY_TIMESTAMP": "2026-01-10 08:00:00", "EXIT_TIMESTAMP": "2026-01-10 09:30:00"},
    {"ID": 51, "UID": "OLD_USER2", "ENTRY_TIMESTAMP": "2026-01-11 12:00:00", "EXIT_TIMESTAMP": "2026-01-11 13:00:00"},
]



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
    # 1. ZDECYDUJ SKĄD BRAĆ DANE (MOCK CZY API)
    if MOCK_MODE:
        lockers_source = MOCK_LOCKERS_TABLE
        entries_source = MOCK_ENTRIES_TABLE
    else:
        try:
            resp_lockers = requests.get(f"{BACKEND_URL}/api/lockers")
            resp_entries = requests.get(f"{BACKEND_URL}/api/history")

            if resp_lockers.status_code == 200 and resp_entries.status_code == 200:
                lockers_source = resp_lockers.json()
                entries_source = resp_entries.json()
            else:
                flash("Błąd pobierania danych z backendu", "danger")
                lockers_source = []
                entries_source = []
        except requests.exceptions.RequestException:
            flash("Nie można połączyć się z serwerem", "danger")
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

# rule musi być takie samo na serwerze łączącym się z bazą
@app.route('/otworz/<int:locker_id>', methods=['POST'])
def open_locker(locker_id):
    if MOCK_MODE:
        for row in MOCK_LOCKERS_TABLE:
            if row['NR'] == locker_id:
                if row['UID'] is None:
                    new_uid = "TEST_USER"
                    row['UID'] = new_uid
                    MOCK_ENTRIES_TABLE.append({
                        "ID": 999,
                        "UID": new_uid,
                        "ENTRY_TIMESTAMP": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "EXIT_TIMESTAMP": None
                    })
                break
    else:
        requests.post(f"{BACKEND_URL}/api/open/{locker_id}")

    return redirect(url_for('dashboard'))


@app.route('/zwolnij/<int:locker_id>', methods=['POST'])
def release_locker(locker_id):
    if MOCK_MODE:
        target_uid = None
        for row in MOCK_LOCKERS_TABLE:
            if row['NR'] == locker_id:
                target_uid = row['UID']
                row['UID'] = None
                break

        if target_uid:
            for entry in MOCK_ENTRIES_TABLE:
                if entry['UID'] == target_uid and entry['EXIT_TIMESTAMP'] is None:
                    entry['EXIT_TIMESTAMP'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
    else:
        requests.post(f"{BACKEND_URL}/api/release/{locker_id}")

    return redirect(url_for('dashboard'))


@app.route('/historia')
def history():
    filter_type = request.args.get('filter', 'all')

    if MOCK_MODE:
        entries_source = MOCK_ENTRIES_TABLE
    else:
        try:
            resp_entries = requests.get(f"{BACKEND_URL}/api/history")

            if resp_entries.status_code == 200:
                entries_source = resp_entries.json()
            else:
                entries_source = []

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

        display_logs.append({
            "card_uid": entry['UID'],
            "locker_number": str(entry['NR']) if entry['NR'] is not None else "-",
            "start_time": entry['ENTRY_TIMESTAMP'],
            "end_time": entry['EXIT_TIMESTAMP'],
            "duration": calculate_duration(entry['ENTRY_TIMESTAMP'], entry['EXIT_TIMESTAMP']),
            "is_active": is_active
        })

    return render_template('historia.html', logs=display_logs, active_filter=filter_type)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
