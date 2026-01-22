#!/usr/bin/env python3

import time

from config import *

import RPi.GPIO as GPIO
from mfrc522 import MFRC522

from constants import BROKER_HOST, GATE_TOPIC_SEND, CARD_READ_DELAY
from client_handler import ClientHandler
from signal_handler import SignalHandler

def run(client: ClientHandler):
    signal_handler: SignalHandler = SignalHandler()

    reader = MFRC522()
    firstContact = True
    previousStatus = reader.MI_ERR

    print("Gate station started, waiting for cards...")

    try:
        while signal_handler.is_running:
            status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)

            while status == reader.MI_OK or previousStatus == reader.MI_OK:
                status, uid = reader.MFRC522_Anticoll()
                
                if status == reader.MI_OK and firstContact:

                    uid_str = "".join([str(x) for x in uid])
                    print(f"Card detected {uid_str}")
                    
                    client.publish(uid_str)

                    firstContact = False

                time.sleep(CARD_READ_DELAY)
                previousStatus = status
                status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)

            else:
                if not firstContact:
                    firstContact = True

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
    except:
        client.disconnect()
    
    GPIO.cleanup()

if __name__ == "__main__":
    main()
