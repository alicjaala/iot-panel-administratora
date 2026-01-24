from flask import Flask, jsonify, request
from flask_mqtt import Mqtt
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import raspberries.constants as const
import db_operations as db

app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = const.BROKER_HOST
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

mqtt = Mqtt(app)


@mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker!")
        client.subscribe(const.LOCKER_TOPIC_SEND)
        client.subscribe(const.GATE_TOPIC_SEND)
    else:
        print(f"Connection error, code: {rc}")


@mqtt.on_message()
def on_message(client, userdata, message):
    try:
        uid = message.payload.decode("utf-8")
        topic = message.topic

        if topic == const.LOCKER_TOPIC_SEND:
            locker_nr = db.allocate_or_retrieve_locker(uid)
            
            mess = str(locker_nr) if locker_nr is not None else "null"
            client.publish(const.LOCKER_TOPIC_RECEIVE, mess)

        elif topic == const.GATE_TOPIC_SEND:
            db.process_gate_event(uid)

    except Exception as e:
        print(f"Error handling MQTT message: {e}")



@app.route('/api/lockers', methods=['GET'])
def api_lockers():
    """
    Endpoint for app.py to get locker status.
    Expected format: [{"NR": 1, "UID": "..."}]
    """
    data = db.get_all_lockers()
    response = [{"NR": row['nr'], "UID": row['uid']} for row in data]
    return jsonify(response)


@app.route('/api/history', methods=['GET'])
def api_history():
    """
    Endpoint for app.py to get history.
    Expected format keys: ID, UID, ENTRY_TIMESTAMP, EXIT_TIMESTAMP
    """
    data = db.get_all_entries()
    response = []
    for row in data:
        response.append({
            "ID": row['id'],
            "UID": row['uid'],
            "NR": row['locker_nr'],
            "ENTRY_TIMESTAMP": row['entry_tmsp'],
            "EXIT_TIMESTAMP": row['exit_tmsp']
        })
    return jsonify(response)


@app.route('/api/open/<int:locker_id>', methods=['POST'])
def api_open(locker_id):
    """
    Manual open command from Dashboard.
    Publishes MQTT message to hardware.
    """
    mqtt.publish(const.LOCKER_TOPIC_RECEIVE, str(locker_id))
    return jsonify({"status": "sent", "locker": locker_id})


@app.route('/api/release/<int:locker_id>', methods=['POST'])
def api_release(locker_id):
    """
    Admin command to force release a locker.
    Updates DB and closes history.
    """
    success = db.force_release_locker(locker_id)

    if success:
        return jsonify({"status": "released", "locker": locker_id})
    else:
        return jsonify({"status": "ignored", "message": "Locker was not occupied"}), 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

