import os
import json
import subprocess
import shutil

import supervisely as sly

from dotenv import load_dotenv

ABSOLUTE_PATH = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(ABSOLUTE_PATH)
REPOS_JSON = os.path.join(ROOT_DIR, "repos.json")
REPOS_URLS = json.load(open(REPOS_JSON, "r"))
REPOS_NAMES = [url.split("/")[-1].replace(".git", "") for url in REPOS_URLS]
sly.logger.info(f"Loaded list with {len(REPOS_URLS)} repos from {REPOS_JSON}.")
REPOS = list(zip(REPOS_NAMES, REPOS_URLS))

FILES_DIR = os.path.join(ROOT_DIR, "files")
os.makedirs(FILES_DIR, exist_ok=True)

REPOS_DIR = os.path.join(ROOT_DIR, "repos")
os.makedirs(REPOS_DIR, exist_ok=True)

load_dotenv("ninja.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
api: sly.Api = sly.Api.from_env()

TEAM_ID = sly.io.env.team_id()
WORKSPACE_ID = sly.io.env.workspace_id()

REMOTE_ENV_FILE = "/ninja-updater/ninja.env"
REMOTE_SSH_KEY = "/ninja-updater/id_rsa"
LOCAL_ENV_FILE = os.path.join(FILES_DIR, "ninja.env")
LOCAL_SSH_KEY = os.path.join(FILES_DIR, "id_rsa")

STATS_OPTIONS = [
    "all",
    "ClassBalance",
    "ClassCooccurrence",
    "ClassesPerImage",
    "ObjectsDistribution",
    "ObjectSizes",
    "ClassSizes",
    "ClassesHeatmaps",
    "ClassesPreview",
    "Previews",
    "ClassesTreemap",
]

VISUALS_OPTIONS = [
    "all",
    "Poster",
    "SideAnnotationsGrid",
    "HorizontalGrid",
    "VerticalGrid",
]
TEXTS_OPTIONS = ["all", "citation", "license", "readme", "download", "summary"]

REPO_STATUSES = {
    "waiting": "⏺️ Waiting",
    "working": "🔄 Working",
    "finished": "✅ Finished",
    "error": "🅾️ Error",
}


class State:
    def __init__(self):
        self.selected_repos = []


AppState = State()


def download_files():
    try:
        api.file.download(TEAM_ID, REMOTE_ENV_FILE, LOCAL_ENV_FILE)
        api.file.download(TEAM_ID, REMOTE_SSH_KEY, LOCAL_SSH_KEY)
        sly.logger.info(f"Environment file and SSH key were downloaded to {FILES_DIR}.")

        with open(LOCAL_ENV_FILE, "r") as f:
            address_line = f.readline().strip()
            server_address = address_line.split("=")[1].replace('"', "")
            api_token_line = f.readline().strip()
            api_token = api_token_line.split("=")[1].replace('"', "")

    except Exception:
        raise RuntimeError(
            f"Failed to download environment file and SSH key. Check that {REMOTE_ENV_FILE} and "
            f"{REMOTE_SSH_KEY} exist in the TeamFiles."
        )

    return server_address, api_token


def setup_ssh_key():
    ssh_key_path = LOCAL_SSH_KEY
    local_ssh_dir = os.path.expanduser("~/.ssh")
    local_ssh_key_path = os.path.join(local_ssh_dir, "id_rsa")

    if not os.path.exists(local_ssh_dir):
        os.makedirs(local_ssh_dir)

    shutil.copy(ssh_key_path, local_ssh_key_path)

    os.chmod(local_ssh_key_path, 0o600)

    cmd = "ssh -T -o StrictHostKeyChecking=no git@github.com"
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    warning, login = process.communicate()

    if not login or not login.startswith("Hi"):
        raise RuntimeError(
            "Could not connect to GitHub. Check that the SSH key is set up correctly."
        )
    if warning:
        sly.logger.warning(warning)
    sly.logger.info(login)

    return True


assets_server_address, api_token = download_files()
assets_api = sly.Api(assets_server_address, api_token)
sly.logger.info(f"Created API instance for assets server: {assets_server_address}")

ssh_status = setup_ssh_key()
