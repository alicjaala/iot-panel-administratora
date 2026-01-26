import logging
import time

import RPi.GPIO as GPIO

from constants import BROKER_HOST, GATE_TOPIC_SEND, CARD_READ_DELAY
from client_handler import ClientHandler
from signal_handler import SignalHandler
from rfid_reader import RFIDReader

logger = logging.getLogger(__name__)

def run(client: ClientHandler):
    signal_handler: SignalHandler = SignalHandler()
    card_reader: RFIDReader = RFIDReader()

    logger.info("Gate station started, waiting for cards...")

    try:
        while signal_handler.is_running:
            uid = card_reader.check_for_card()

            if uid:
                logger.info(f"Card detected: {uid}")
                client.publish(uid)

            time.sleep(CARD_READ_DELAY)

    except Exception as e:
        logger.error(f"Error in the main loop: {e}")
    finally:
        GPIO.cleanup()
        logger.info("Gate station stopped")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    client: ClientHandler = ClientHandler(
        broker_host = BROKER_HOST,
        topic_send = GATE_TOPIC_SEND
    )
    client.connect()
    
    if not client.is_connected:
        logger.error("Failed to connect to broker, exiting")
        return

    try:
        run(client = client)
    finally:
        client.disconnect()
        GPIO.cleanup()
    

if __name__ == "__main__":
    main()
