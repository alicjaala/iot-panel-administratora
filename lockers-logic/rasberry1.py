#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
import board
import neopixel
from config import *
import paho.mqtt.client as mqtt
import lib.oled.SSD1331 as SSD1331
from PIL import Image, ImageDraw, ImageFont


BROKER_HOST = "10.108.33.123"
TOPIC_RECIEVE = "lockers/from_server"
TOPIC_SEND = "lockers/to_server"

client = mqtt.Client()

buttonRedState = GPIO.HIGH
usedFont = ImageFont.truetype('./lib/oled/Font.ttf', 14)

display = None

def setUpDisplay():
    global display
    display = SSD1331.SSD1331()
    display.Init()
    display.clear()

    image1 = Image.new("RGB", (display.width, display.height), "BLACK")
    draw = ImageDraw.Draw(image1)

    draw.text((10, 10), "Tap your card", font=usedFont)
    display.ShowImage(image1, 0, 0)


def displayInfo(info: str):
    global display
    display.clear()
    
    image1 = Image.new("RGB", (display.width, display.height), "BLACK")
    draw = ImageDraw.Draw(image1)

    draw.text((10, 10), info, font=usedFont)
    display.ShowImage(image1, 0, 0)

    time.sleep(5)
    
    display.clear()

    image2 = Image.new("RGB", (display.width, display.height), "BLACK")
    draw = ImageDraw.Draw(image2)
    draw.text((10, 10), "Tap your card", font=usedFont)

    display.ShowImage(image2, 0, 0)

def buttonCallback(channel):
    global buttonRedState
    buttonRedState = GPIO.input(buttonRed)

def process_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")

        if not payload or payload.lower() == "null":
            print("No locker available")
            displayInfo("No locker free")
        else:
            print(f"Opening locker nr {payload}")
            displayInfo(f"Locker: {payload}")
    except Exception as e:
        print(e)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Subscribing to topic")
        client.subscribe(TOPIC_RECIEVE)
    else:
        print(f"Error, code: {rc}")

def connect_to_broker():
    client.on_message = process_message
    client.on_connect = on_connect
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
    
    setUpDisplay()
    readRIFD()

    disconnect_from_broker()
    GPIO.cleanup()

if __name__ == "__main__":
    main()