from instagrapi import Client
import os

class Scrapper(Client):
    def __init__(self, username:str, password:str, new_session=False, proxy=None):
        super().__init__()
        if proxy:
            self.set_proxy(proxy)
        if os.path.exists(f'session_{username}.json') and new_session is False:
            self.load_settings(f'session_{username}.json')
            self.login(username, password)
            try:
                self.get_timeline_feed()
                print('Logged in with old session')
            except Exception as e:
                print('Login failed with old session, deleting old session file...')
                os.remove(f'session_{username}.json')
                print('Run the program again to login with new session.')
                exit()
        else:
            self.login(username, password)
            self.dump_settings(f'session_{username}.json')
            print('Logged in with new session')

    def use_proxy(self, proxy):
        self.set_proxy(proxy)

    def download_reels(self, username, count=0):

        user_id = self.user_id_from_username(username)
        medias = self.user_clips(user_id, 0)
        reels = []
        count = 0
        for media in medias:
            if media.video_url is not None:
                path = self.clip_download_by_url(media.video_url)
                reels.append(path)
                count += 1
    
        print(f"Downloaded {count} reels")
            
        return reels
    
    def get_reels(self, username, count=0):
        user_id = self.user_id_from_username(username)
        medias = self.user_clips(user_id, count)

        to_ret = []
        reel_aspect_ratio = 1080/1920

        print("Filtering Reels by Aspect Ratio")
        for media in medias:
            w = media.image_versions2['candidates'][0]['width']
            h = media.image_versions2['candidates'][0]['height']
            ratio = w/h
            if ratio == reel_aspect_ratio:
                to_ret.append(media)
        
        return to_ret
    
    def check_for_new_reel(self, username, latest_reel):
        user_id = self.user_id_from_username(username)

        media = self.user_clips(user_id, 1)
        if media[0].code != latest_reel:
            return media[0].video_url, media[0].code
        
        return None

    def download_reel(self, url):
        path = self.clip_download_by_url(url)
        return path