import time
import os
import shutil
import schedule
import random

from scrapper import Scrapper
from utils import *
from yt import get_authenticated_service, upload_video


# Create directory for downloads
def create_directory(username):
    directory = f"./{username}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


# Remove directory and its contents
def remove_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)


def old_video_upload(scrapper: Scrapper):
    username = read_username()
    uploaded = load_uploaded_reels()
    reels = scrapper.get_reels(username, len(uploaded) + 1)
    reels.reverse()
    for reel in reels:
        if not is_reel_uploaded(reel.code):
            path = None
            try:
                path = scrapper.download_reel(reel.video_url)
                youtube = get_authenticated_service()
                titles = load_titles()
                title = random.choice(titles) + " #shorts"
                description = title + "\n" + reel.caption_text
                print("Uploading Reel to YT")
                res = upload_video(
                    youtube,
                    path,
                    title,
                    description,
                    tags=["money", "trading", "ebook"],
                    privacy_status="public",
                )
                print(
                    "Reel uploaded Successfully : ",
                    "https://www.youtube.com/shorts/" + res["id"],
                )
                save_uploaded_reels(reel.code)
            except Exception as e:
                print("Error uploading reel : ", reel.code)
                raise
            finally:
                if path:
                    os.remove(path)


def new_video_upload(scrapper: Scrapper):
    print("Checking for new Reel")
    username = read_username()
    uploaded = load_uploaded_reels()

    with open("latest_reel.txt", "r") as file:
        latest_reel = file.readline().strip()

    new_reel, new_reel_code = scrapper.check_for_new_reel(username, latest_reel)
    if new_reel and new_reel not in uploaded:
        print("New Reel Detected")
        path = None
        try:
            path = scrapper.download_reel(new_reel)
            youtube = get_authenticated_service()
            titles = load_titles()
            title = random.choice(titles) + " #shorts"
            description = title + "\n" + new_reel
            print("Uploading Reel to YT")
            res = upload_video(
                youtube,
                path,
                title,
                description,
                tags=["money", "trading", "ebook"],
                privacy_status="public",
            )
            print(
                "Reel uploaded Successfully : ",
                "https://www.youtube.com/shorts/" + res["id"],
            )
            save_uploaded_reels(new_reel)
            with open("latest_reel.txt", "w") as file:
                file.write(new_reel)
        except Exception as e:
            print("Error uploading reel : ", new_reel_code)
            raise
        finally:
            if path:
                os.remove(path)

    else:
        print("No New Reel Found")


# Read schedule times from file
def read_schedule_file(file_path="schedule.txt"):
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path of the schedule file
    abs_file_path = os.path.join(script_dir, file_path)

    if not os.path.exists(abs_file_path):
        print(
            f"Error: The file '{abs_file_path}' was not found. Please create it with two times, one for live video uploads and one for old video uploads."
        )
        return []

    with open(abs_file_path, "r") as file:
        times = [line.strip() for line in file.readlines() if line.strip()]
    return times


# Schedule jobs based on times from file
def schedule_jobs_from_file():
    times = read_schedule_file()

    upload_acc = get_uploding_account()
    monitoring_acc = get_monitoring_account()

    upload_scrapper = Scrapper(upload_acc[0], upload_acc[1])
    if os.path.exists("proxy.txt"):
        proxy = get_proxy()
        upload_scrapper.set_proxy(proxy)
    if monitoring_acc == upload_acc:
        monitoring_scrapper = upload_scrapper
    else:
        monitoring_scrapper = Scrapper(monitoring_acc[0], monitoring_acc[1])
        if os.path.exists("proxy.txt"):
            proxy = get_proxy()
            upload_scrapper.set_proxy(proxy)
    if len(times) >= 1:
        schedule.every().day.at(times[0]).do(old_video_upload, upload_scrapper)
        schedule.every().hour.do(new_video_upload, monitoring_scrapper)
        print("Reels will be uploaded every day at " + times[0])
        print("Monitoring For new reels every hour")
    else:
        print(
            "Error: Schedule file does not have enough times. Please provide two times in 'schedule.txt'."
        )


# Main loop to schedule tasks
if __name__ == "__main__":
    get_authenticated_service(generate_session=True)
    generate_required_files()
    schedule_jobs_from_file()  # Schedule jobs based on file contents
    while True:
        schedule.run_pending()
        time.sleep(1)
