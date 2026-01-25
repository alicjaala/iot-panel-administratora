import logging
import time

from config import *

import RPi.GPIO as GPIO

from constants import (
    BROKER_HOST, LOCKER_TOPIC_RECEIVE, 
    LOCKER_TOPIC_SEND, CARD_READ_DELAY, MESSAGE_DISPLAY_TIME)

from signal_handler import SignalHandler
from client_handler import ClientHandler
from rfid_reader import RFIDReader
from oled_display import OLEDDisplay, OnDisplay

logger = logging.getLogger(__name__)

display: OLEDDisplay = None

next_read = 0

def process_message(client, userdata, message):
    global display
    
    try:
        payload = message.payload.decode("utf-8")

        if not payload or payload.lower() == "null":
            logger.info("No locker available")
            display.show_error()
        
        else:
            logger.info(f"Opening locker nr {payload}")
            display.show_locker(payload)

    except Exception as e:
        logger.error(f"Error processing message: {e}")

def run(client: ClientHandler):
    global display

    signal_handler: SignalHandler = SignalHandler()
    card_reader: RFIDReader = RFIDReader()

    logger.info("Locker station started, waiting for cards...")

    try:
        while signal_handler.is_running:
            
            if time.time() > next_read and display.currently_displaying != OnDisplay.DEFAULT:
                display.show_default()

            uid = card_reader.check_for_card()

            if uid and time.time() > next_read:
                next_read = time.time() + MESSAGE_DISPLAY_TIME
                logger.info(f"Card detected: {uid}")
                client.publish(uid)

            time.sleep(CARD_READ_DELAY)

    except Exception as e:
        logger.error(f"Error in the main loop: {e}")
    finally:
        GPIO.cleanup()
        logger.info("Locker station stopped")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    client: ClientHandler = ClientHandler(
        broker_host = BROKER_HOST,
        topic_send = LOCKER_TOPIC_SEND,
        topic_receive = LOCKER_TOPIC_RECEIVE,
        on_message = process_message
    )
    client.connect()
    
    if not client.is_connected:
        logger.error("Failed to connect to broker, exiting")
        return

    global display
    display = OLEDDisplay()
    if display.initialize():
        display.show_default()
    else:
        logger.warning("Running without display")
        

    try:
        run(client = client)
    finally:
        client.disconnect()
        GPIO.cleanup()

if __name__ == "__main__":
    main()