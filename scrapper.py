from instagrapi import Client
import os

class Scrapper:
    def __init__(self, username:str, password:str, new_session=False):
        self.cl = Client()
        if os.path.exists(f'session_{username}.json') and new_session is False:
            self.cl.load_settings(f'session_{username}.json')
            self.cl.login(username, password)
            try:
                self.cl.get_timeline_feed()
            except Exception as e:
                print('Login failed')
                raise e
            print('Logged in with old session')
        else:
            self.cl.login(username, password)
            self.cl.dump_settings(f'session_{username}.json')
            print('Logged in with new session')

    def set_proxy(self, proxy):
        self.cl.set_proxy(proxy)

    def download_reels(self, username, count=0):

        user_id = self.cl.user_id_from_username(username)
        medias = self.cl.user_clips(user_id, 0)
        reels = []
        count = 0
        for media in medias:
            if media.video_url is not None:
                path = self.cl.clip_download_by_url(media.video_url)
                reels.append(path)
                count += 1
    
        print(f"Downloaded {count} reels")
            
        return reels
    
    def get_reels(self, username, count=0):
        user_id = self.cl.user_id_from_username(username)
        medias = self.cl.user_clips(user_id, count)
        
        return medias
    
    def check_for_new_reel(self, username, latest_reel):
        user_id = self.cl.user_id_from_username(username)

        media = self.cl.user_clips(user_id, 1)
        if media[0].code != latest_reel:
            return media[0].video_url, media[0].code
        
        return None

    def download_reel(self, url):
        path = self.cl.clip_download_by_url(url)
        return path
