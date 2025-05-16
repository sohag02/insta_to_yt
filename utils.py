import os
import csv
import json
import emoji

def load_uploaded_reels():
    with open("uploaded_reels.json", "r") as file:
        return json.load(file)["reels"]


def is_reel_uploaded(reel_id):
    uploaded_reels = load_uploaded_reels()
    return reel_id in uploaded_reels


def save_uploaded_reels(reel_id):
    uploaded_reels = load_uploaded_reels()
    uploaded_reels.append(reel_id)
    with open("uploaded_reels.json", "w") as file:
        json.dump({"reels": uploaded_reels}, file, indent=4)


def generate_required_files():
    if not os.path.exists("uploaded_reels.json"):
        with open("uploaded_reels.json", "w") as file:
            json.dump({"reels": []}, file, indent=4)

    if not os.path.exists("latest_reel.txt"):
        with open("latest_reel.txt", "w") as file:
            file.write("")


def get_accounts():
    with open("accounts.csv", "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        return list(reader)


def get_uploding_account():
    accs = get_accounts()
    return accs[0]


def get_monitoring_account():
    accs = get_accounts()
    if len(accs) < 2:
        return accs[0]
    return accs[1]


# Load titles and descriptions from a JSON file
def load_titles():
    with open("titles.json", "r") as file:
        data = json.load(file)
    return data["Titles"]


# Read Instagram username from file
def read_username():
    with open("username.txt", "r") as file:
        return file.readline().strip()


def get_proxy():
    with open("proxy.txt", "r") as file:
        proxy_list = file.readlines()
        if len(proxy_list) == 0:
            return None
        proxy = proxy_list[0].strip()

    # remove selected proxy from file
    with open("proxy.txt", "w") as file:
        file.writelines(proxy_list[1:])

    return proxy


def save_old_reels(reels):
    with open("old_reels.json", "w") as file:
        json.dump({"reels": reels}, file, indent=4)


def get_old_reels():
    with open("old_reels.json", "r") as file:
        return json.load(file)["reels"]


def remove_emojis(text: str) -> str:
    return emoji.replace_emoji(text, replace='')
