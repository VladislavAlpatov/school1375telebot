from PIL import ImageDraw, ImageFont, Image


class Card:
    """
    Если пип выёбывается:
    pip install --compile --install-option=-O1 Pillow
    """
    def __init__(self, color_bg_title: str = '#00ff55'):
        self.__img = Image.new('RGB', (1000, 400), '#23272a')
        self.__draw = ImageDraw.Draw(self.__img)
        self.__draw.rectangle([0, 0, 1000, 70], fill=color_bg_title)

    def title(self, font: str, color, text: str):
        loaded_font = ImageFont.truetype(font, 62, encoding="utf-8")
        self.__draw.text((0, 0), text, font=loaded_font, fill=color)

    def text(self, font: str, color, font_size: int, text):
        loaded_font = ImageFont.truetype(font, font_size, encoding="utf-8")
        self.__draw.text((0, 85), text, font=loaded_font, fill=color)

    def save(self, name: str):
        self.__img.save(name)
        self.__img.close()

