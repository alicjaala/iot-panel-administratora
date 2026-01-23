import logging
import time

import lib.oled.SSD1331 as SSD1331
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

logger = logging.getLogger(__name__)

class OLEDDisplay:
    
    def __init__(self):
        self._display: Optional[SSD1331.SSD1331] = None
        self._font_path = './lib/oled/Font.ttf'
        self._font_size = 14
        self._font: Optional[ImageFont.FreeTypeFont] = None
    
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
        self._draw_text("Tap your card")

    def show_locker(self, locker_number: str):
        self._show_info(f"Locker: {locker_number}")
    
    def show_error(self):
        self._show_info("No free lockers")

    def _show_info(self, message: str):
        self._draw_text(message)
        time.sleep(5)
        self.show_default()

    def _draw_text(self, text: str):
        if not self._display:
            return
        
        self._display.clear()
        
        image = Image.new("RGB", (self._display.width, self._display.height), "BLACK")
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), text, font=self._font)

        self._display.ShowImage(image, 0, 0)
