from flask import Flask, jsonify
import requests
from flask_mqtt import Mqtt
import os, sys
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import raspberries.constants as const
import db_operations as db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = const.BROKER_HOST
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

mqtt = Mqtt(app)


def notify_frontend():
    try:
        requests.post(const.FRONTEND_WEBHOOK, json={}, timeout=0.1)
        logger.debug("Frontend notification sent successfully.")
    except Exception as e:
        logger.warning(f"Failed to notify frontend: {e}")


@mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Successfully connected to MQTT broker!")
        client.subscribe(const.LOCKER_TOPIC_SEND)
        client.subscribe(const.GATE_TOPIC_SEND)
        logger.info(f"Subscribed to topics: {const.LOCKER_TOPIC_SEND}, {const.GATE_TOPIC_SEND}")
    else:
        logger.error(f"MQTT Connection failed. Return code: {rc}")


@mqtt.on_message()
def on_message(client, userdata, message):
    try:
        uid = message.payload.decode("utf-8")
        topic = message.topic
        db_changed = False

        logger.info(f"MQTT Message received | Topic: {topic} | UID: {uid}")

        if topic == const.LOCKER_TOPIC_SEND:
            locker_nr, db_changed = db.allocate_or_retrieve_locker(uid)
            
            if locker_nr != -1:
                mess = str(locker_nr) if locker_nr is not None else "null"
                client.publish(const.LOCKER_TOPIC_RECEIVE, mess)
                logger.info(f"Locker allocated/retrieved. Sent '{mess}' to hardware.")
            else:
                logger.warning(f"Locker allocation returned -1 (Error) for UID: {uid}")

        elif topic == const.GATE_TOPIC_SEND:
            db_changed = db.process_gate_event(uid)
            logger.info(f"Gate event processed for UID: {uid}")

        if db_changed:
            notify_frontend()

    except Exception as e:
        logger.error(f"Critical error handling MQTT message: {e}", exc_info=True)



@app.route('/api/lockers', methods=['GET'])
def api_lockers():
    """
    Endpoint for app.py to get locker status.
    Expected format: [{"NR": 1, "UID": "..."}]
    """
    try:
        data = db.get_all_lockers()
        response = [{"NR": row['nr'], "UID": row['uid']} for row in data]
        return jsonify(response)
    except Exception as e:
        logger.error(f"API Error (get_lockers): {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route('/api/history', methods=['GET'])
def api_history():
    """
    Endpoint for app.py to get history.
    Expected format keys: ID, UID, ENTRY_TIMESTAMP, EXIT_TIMESTAMP
    """
    try:
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
    except Exception as e:
        logger.error(f"API Error (get_history): {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route('/api/open/<int:locker_id>', methods=['POST'])
def api_open(locker_id):
    """
    Manual open command from Dashboard.
    Publishes MQTT message to hardware.
    """
    logger.info(f"API: Received manual OPEN command for Locker #{locker_id}")
    try:
        mqtt.publish(const.LOCKER_TOPIC_RECEIVE, str(locker_id))
        return jsonify({"status": "sent", "locker": locker_id})
    except Exception as e:
        logger.error(f"Failed to publish manual open command: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/release/<int:locker_id>', methods=['POST'])
def api_release(locker_id):
    """
    Admin command to force release a locker.
    Updates DB and closes history.
    """
    logger.info(f"API: Received ADMIN RELEASE command for Locker #{locker_id}")
    try:
        success = db.force_release_locker(locker_id)

        if success:
            logger.info(f"Locker #{locker_id} released successfully.")
            notify_frontend()
            return jsonify({"status": "released", "locker": locker_id})
        else:
            logger.warning(f"Release command ignored. Locker #{locker_id} was not occupied.")
            return jsonify({"status": "ignored", "message": "Locker was not occupied"}), 200

    except Exception as e:
        logger.error(f"Error executing force release: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    logger.info("Starting Backend Server...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
