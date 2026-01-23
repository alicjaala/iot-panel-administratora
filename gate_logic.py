#!/usr/bin/env python3

import time

from config import *

import RPi.GPIO as GPIO

from constants import BROKER_HOST, GATE_TOPIC_SEND, CARD_READ_DELAY
from client_handler import ClientHandler
from signal_handler import SignalHandler
from rfid_reader import RFIDReader

def run(client: ClientHandler):
    signal_handler: SignalHandler = SignalHandler()
    card_reader: RFIDReader = RFIDReader()

    print("Gate station started, waiting for cards...")

    try:
        while signal_handler.is_running:
            uid = card_reader.check_for_card()

            if uid:
                print(f"Card detected {uid}")
                client.publish(uid)

            time.sleep(CARD_READ_DELAY)

    except Exception as e:
        print(f"Error in the main loop {e}")
    finally:
        GPIO.cleanup()
        print("Gate station stopped")

def main():
    client: ClientHandler = ClientHandler(
        broker_host = BROKER_HOST,
        topic_send = GATE_TOPIC_SEND
    )
    client.connect()
    
    if not client.is_connected:
        print("Failed to connect to broker, exiting")
        return

    try:
        run(client = client)
    finally:
        client.disconnect()
        GPIO.cleanup()
    

if __name__ == "__main__":
    main()
