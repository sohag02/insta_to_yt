from configparser import ConfigParser

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

        self.validate()

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