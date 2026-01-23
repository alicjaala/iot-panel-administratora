# MQTT config
BROKER_HOST = "10.108.33.123"

LOCKER_TOPIC_RECEIVE = "lockers/from_server"
LOCKER_TOPIC_SEND = "lockers/to_server"
GATE_TOPIC_SEND = "gate/to_server"

# (Internet of) Things
## RFID reader
CARD_READ_DELAY = 0.1

## OLED display
FONT_PATH = './lib/oled/Font.ttf'
FONT_SIZE = 14
DEFAULT_MESSAGE = "Tap your card"
NO_LOCKERS_MESSAGE = "No free lockers"