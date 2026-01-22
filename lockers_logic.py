import time

from config import *

import RPi.GPIO as GPIO
import lib.oled.SSD1331 as SSD1331
import paho.mqtt.client as mqtt
from mfrc522 import MFRC522
from PIL import Image, ImageDraw, ImageFont

from constants import (
    BROKER_HOST, LOCKER_TOPIC_RECEIVE, 
    LOCKER_TOPIC_SEND, CARD_READ_DELAY)

from signal_handler import SignalHandler
from client_handler import ClientHandler

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

def run(client: ClientHandler):
    signal_handler: SignalHandler = SignalHandler()
    
    reader = MFRC522()
    firstContact = True
    previousStatus = reader.MI_ERR

    print("Locker station started, waiting for cards...")

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
        print("Locker station stopped")

def main():
    client: ClientHandler = ClientHandler(
        broker_host = BROKER_HOST,
        topic_send = LOCKER_TOPIC_SEND,
        topic_receive = LOCKER_TOPIC_RECEIVE,
        on_message = process_message
    )
    client.connect()
    
    if not client.is_connected:
        print("Failed to connect to broker, exiting")
        return
    
    setUpDisplay()
    
    try:
        run(client = client)
    except:
        client.disconnect()

    client.disconnect()
    GPIO.cleanup()

if __name__ == "__main__":
    main()