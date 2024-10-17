import time
import os
import shutil
import schedule
import random
import json
import requests
from scrapper import Scrapper
from utils import *
from yt import get_authenticated_service, upload_video


def get_all_reels(scrapper: Scrapper):
    username = read_username()
    print(f"Scrapping all reels from @{username}...")
    reels = scrapper.get_reels(username)
    with open("old_reels.json", "w") as file:
        json.dump(
            {
                "reels": [reel.pk for reel in reels],
            },
            file,
            indent=4,
        )
    print(f"Scrapped {len(reels)} reels Successfully!")


def old_video_upload(scrapper: Scrapper):
    for _ in range(2):
        path = None
        old_reels = get_old_reels()
        reel = old_reels[-1]
        retries = 3  # Number of retries
        for attempt in range(retries):
            try:
                path = scrapper.clip_download(reel)
                reel_info = scrapper.media_info(reel)
                youtube = get_authenticated_service()
                titles = load_titles()
                title = random.choice(titles) + " #shorts"
                description = title + "\n" + reel_info.caption_text
                print("Uploading Reel to YT")
                res = upload_video(
                    youtube,
                    path,
                    title,
                    description,
                    tags=["money", "trading", "ebook"],
                )
                print(
                    "Reel uploaded Successfully : ",
                    "https://www.youtube.com/shorts/" + res["id"],
                )
                save_uploaded_reels(reel)
                save_old_reels(old_reels[:-1])
                break  # Exit loop if successful
            except (Exception, requests.exceptions.ReadTimeout) as e:
                print(f"Error uploading reel on attempt {attempt + 1}: ", reel)
                if attempt < retries - 1:
                    print("Retrying...")
                    time.sleep(5)  # Wait before retrying
                else:
                    print(e)
            finally:
                if path and os.path.exists(path):
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
            reel_pk = scrapper.media_pk_from_code(new_reel_code)
            reel_info = scrapper.media_info(reel_pk)
            youtube = get_authenticated_service()
            titles = load_titles()
            title = random.choice(titles) + " #shorts"
            description = title + "\n" + reel_info.caption_text
            print("Uploading Reel to YT")
            res = upload_video(
                youtube,
                path,
                title,
                description,
                tags=["money", "trading", "ebook"],
            )
            print(
                "Reel uploaded Successfully : ",
                "https://www.youtube.com/shorts/" + res["id"],
            )
            save_uploaded_reels(new_reel_code)
            with open("latest_reel.txt", "w") as file:
                file.write(new_reel_code)
        except Exception as e:
            print("Error uploading reel : ", new_reel_code)
            print(e)
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

    proxy = None
    if os.path.exists("proxy.txt"):
        proxy = get_proxy()
        if proxy is not None: print(f'Using proxy: {proxy}')

    upload_scrapper = Scrapper(upload_acc[0], upload_acc[1], proxy=proxy)

    # scrape old reels
    if not os.path.exists("old_reels.json"):
        get_all_reels(upload_scrapper)

    if monitoring_acc == upload_acc:
        monitoring_scrapper = upload_scrapper
    else:
        monitoring_scrapper = Scrapper(monitoring_acc[0], monitoring_acc[1])
        if os.path.exists("proxy.txt"):
            proxy = get_proxy()
            upload_scrapper.set_proxy(proxy)
    if len(times) >= 1:
        schedule.every().day.at(times[0], 'Asia/Kolkata').do(old_video_upload, upload_scrapper)
        schedule.every().hour.do(new_video_upload, monitoring_scrapper)
        print("Reels will be uploaded every day at " + times[0])
        print("Monitoring For new reels every hour")
    else:
        print(
            "Error: Schedule file does not have enough times. Please provide two times in 'schedule.txt'."
        )


# Main loop to schedule tasks
if __name__ == "__main__":
    generate_required_files()
    schedule_jobs_from_file()  # Schedule jobs based on file contents
    while True:
        schedule.run_pending()
        time.sleep(1)
