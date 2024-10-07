import instaloader

# Scrapfly API Key
SCRAPFLY_API_KEY = "scp-live-0793983fd35e43cebd278a24def8ece4"
PROXY_URL = f"https://proxy.scrapfly.io/?key={SCRAPFLY_API_KEY}"

# Function to configure Instaloader with or without proxy
def configure_instaloader_with_proxy(use_proxy=True):
    L = instaloader.Instaloader()
    if use_proxy:
        # Setting up Scrapfly proxy
        L.context._session.proxies = {
            "https": PROXY_URL
        }
    return L

# Function to login using a saved session or with username and password
def login_with_session(L, username, password):
    try:
        # Try to load a previously saved session
        L.load_session_from_file(username)
        print(f"Logged in with saved session for user {username}")
    except FileNotFoundError:
        # If no saved session exists, login with username and password
        L.login(username, password)
        print(f"Saving session for user {username}")
        L.save_session_to_file(username)

# Configure and login to Instagram
L = configure_instaloader_with_proxy(use_proxy=False)  # Set to False to test without proxy
USERNAME = 'mad.hav1236'
PASSWORD = 'Cars@567'

# Try to login with saved session, or login with username/password if session not found
login_with_session(L, USERNAME, PASSWORD)

# URL of the Instagram post to download
post_url = 'https://www.instagram.com/p/CUfjL_EFmKC/'

# Extract shortcode from the URL
shortcode = post_url.split("/")[-2]

# Load the post using the shortcode
post = instaloader.Post.from_shortcode(L.context, shortcode)

# Download the post
L.download_post(post, target=post.owner_username)
