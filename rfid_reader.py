from config import *

from mfrc522 import MFRC522

class RFIDReader:
    def __init__(self):
        self._reader = MFRC522()
        self._previous_state = self._reader.MI_ERR
        self._card_present = False

    def check_for_card(self):
        status, _ = self._reader.MFRC522_Request(self._reader.PICC_REQIDL)

        if status == self._reader.MI_OK or self._previous_state == self._reader.MI_OK:
            status, uid = self._reader.MFRC522_Anticoll()

            if status == self._reader.MI_OK and not self._card_present:
                self._card_present = True
                self._previous_state = status

                return "".join([str(x) for x in uid])

            self._previous_state = status
        else:
            self._card_present = False
        
        return None
