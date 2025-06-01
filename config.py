from configparser import ConfigParser
from dataclasses import dataclass

@dataclass
class GreenScreen:
    do: bool

@dataclass
class PngOverlay:
    do: bool

@dataclass
class GifOverlay:
    do: bool

class Config:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read('config.ini')

        self.upload_time = self.config['SCHEDULE']['upload_time']

        self.username = self.config['INSTAGRAM']['username']
        self.youtube_listed = self.config.getboolean('YOUTUBE', 'listed')
        self.tags = self.get_tags()

        self.caption_before = self.config['CAPTION']['before']
        self.caption_after = self.config['CAPTION']['after']

        self.replacements = dict(self.config.items('replacements'))

        self.green_screen = self._get_green_screen()
        self.png_overlay = self._get_png_overlay()
        self.gif_overlay = self._get_gif_overlay()

        self.validate()

    def _get_green_screen(self):
        do = self.config["OVERLAYS"]["green_screen"]
        return GreenScreen(do)
    
    def _get_png_overlay(self):
        do = self.config["OVERLAYS"]["png_overlay"]
        return PngOverlay(do)

    def _get_gif_overlay(self):
        do = self.config["OVERLAYS"]["gif_overlay"]
        return GifOverlay(do)

    def get_tags(self):
        return [tag.strip() for tag in self.config['YOUTUBE']['tags'].split(',')]

    def validate(self):
        if not self.username:
            raise ValueError('Instagram Username is not set')
        
        if self.youtube_listed is None:
            raise ValueError('Youtube listed is not set')
        
if __name__ == '__main__':
    config = Config()
    print(config.replacements)
    print(config.tags)