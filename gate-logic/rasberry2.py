#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
from config import *
import paho.mqtt.client as mqtt

BROKER_HOST = "10.108.33.123"
TOPIC_SEND = "gate/to_server"

client = mqtt.Client()

buttonRedState = GPIO.HIGH

def buttonCallback(channel):
    global buttonRedState
    buttonRedState = GPIO.input(buttonRed)

def connect_to_broker():
    print("Connecting to broker")

    try:
        client.connect(BROKER_HOST)
        client.loop_start()
    except Exception as e:
        print(f"Error while connecting to the broker: {e}")

def disconnect_from_broker():
    client.loop_stop()
    client.disconnect()
    print("Disconnected from broker")

def call_rfid(uid = ""):
    print(f"{uid} tapped")
    client.publish(TOPIC_SEND, f"{uid}")

def readRIFD():
    reader = MFRC522()
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=buttonCallback, bouncetime=5)
    firstContact = True
    previousStatus = reader.MI_ERR

    try:
        while buttonRedState != GPIO.LOW:
            status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)

            while status == reader.MI_OK or previousStatus == reader.MI_OK:
                status, uid = reader.MFRC522_Anticoll()
                
                if status == reader.MI_OK and firstContact:

                    uid_str = "".join([str(x) for x in uid])

                    call_rfid(uid_str)

                    firstContact = False

                time.sleep(0.1)
                previousStatus = status
                status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)

            else:
                if not firstContact:
                    firstContact = True

        time.sleep(0.1)

    finally:
        GPIO.cleanup()

def main():
    connect_to_broker()
    
    readRIFD()

    disconnect_from_broker()
    GPIO.cleanup()

if __name__ == "__main__":
    main()