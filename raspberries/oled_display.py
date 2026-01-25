import logging
from enum import Enum

import lib.oled.SSD1331 as SSD1331
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

from constants import NO_LOCKERS_MESSAGE, DEFAULT_MESSAGE, FONT_PATH, FONT_SIZE 

logger = logging.getLogger(__name__)

class OnDisplay(Enum):
    DEFAULT = 1
    LOCKER_NR = 2
    ERROR = 3

class OLEDDisplay:
    
    def __init__(self):
        self._display: Optional[SSD1331.SSD1331] = None
        self._font_path = FONT_PATH
        self._font_size = FONT_SIZE
        self._font: Optional[ImageFont.FreeTypeFont] = None
        self.currently_displaying: OnDisplay = None 
    
    def initialize(self) -> bool:
        try:
            self._display = SSD1331.SSD1331()
            self._display.Init()
            self._font = ImageFont.truetype(self._font_path, self._font_size)

            return True
        except Exception as e:
            logger.error(f"Display initialization failed: {e}")
            return False
    
    def show_default(self):
        self._draw_text(DEFAULT_MESSAGE)
        self.currently_displaying = OnDisplay.DEFAULT

    def show_locker(self, locker_number: str):
        self._draw_text(f"Locker: {locker_number}")
        self.currently_displaying = OnDisplay.LOCKER_NR
    
    def show_error(self):
        self._draw_text(NO_LOCKERS_MESSAGE)
        self.currently_displaying = OnDisplay.ERROR

    def _draw_text(self, text: str):
        if not self._display:
            return
        
        self._display.clear()
        
        image = Image.new("RGB", (self._display.width, self._display.height), "BLACK")
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), text, font=self._font)

        self._display.ShowImage(image, 0, 0)
