import os
import json
import subprocess
import shutil
import requests

import supervisely as sly

from dotenv import load_dotenv

ABSOLUTE_PATH = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(ABSOLUTE_PATH)
REPOS_JSON = os.path.join(ROOT_DIR, "repos.json")

REPOS_DATA = json.load(open(REPOS_JSON, "r"))
REPOS_OWNERS = list(REPOS_DATA.keys())
REPOS_URLS = []
for repos_list in REPOS_DATA.values():
    REPOS_URLS.extend(repos_list)
REPOS_NAMES = [url.split("/")[-1].replace(".git", "") for url in REPOS_URLS]
sly.logger.info(f"Loaded list with {len(REPOS_URLS)} repos from {REPOS_JSON}.")
REPOS = list(zip(REPOS_NAMES, REPOS_URLS))

FILES_DIR = os.path.join(ROOT_DIR, "files")
os.makedirs(FILES_DIR, exist_ok=True)

REPOS_DIR = os.path.join(ROOT_DIR, "repos")
os.makedirs(REPOS_DIR, exist_ok=True)

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/ninja.env"))
api: sly.Api = sly.Api.from_env()

TEAM_ID = sly.io.env.team_id()
WORKSPACE_ID = sly.io.env.workspace_id()

REMOTE_SSH_KEY = sly.env.file()
LOCAL_SSH_KEY = os.path.join(FILES_DIR, "id_rsa")

STATS_OPTIONS = [
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
    "Poster",
    "SideAnnotationsGrid",
    "HorizontalGrid",
    "VerticalGrid",
]
TEXTS_OPTIONS = ["citation", "license", "readme", "download", "summary"]

REPO_STATUSES = {
    "waiting": "⏺️ Waiting",
    "working": "🔄 Working",
    "finished": "✅ Finished",
    "error": "🅾️ Error",
}


class State:
    def __init__(self):
        self.ssh_status = False
        self.continue_processing = True
        self.selected_repos = []


AppState = State()


def download_files():
    try:
        api.file.download(TEAM_ID, REMOTE_SSH_KEY, LOCAL_SSH_KEY)
        sly.logger.info(f"Environment file and SSH key were downloaded to {FILES_DIR}.")

    except Exception:
        raise RuntimeError(
            f"Failed to download SSH key. Check that {REMOTE_SSH_KEY} exist in the TeamFiles."
        )


download_files()


def setup_ssh_key():
    ssh_key_path = LOCAL_SSH_KEY
    local_ssh_dir = os.path.expanduser("~/.ssh")
    local_ssh_key_path = os.path.join(local_ssh_dir, "id_rsa")

    if not os.path.exists(local_ssh_dir):
        sly.logger.warning(f"Directory .ssh does not exist. Creating {local_ssh_dir}")
        os.makedirs(local_ssh_dir)

    sly.logger.info(f"Trying to copy {ssh_key_path} to {local_ssh_key_path}")
    shutil.copy(ssh_key_path, local_ssh_key_path)

    sly.logger.info(f"Copied {ssh_key_path} to {local_ssh_key_path}")

    os.chmod(local_ssh_key_path, 0o600)

    sly.logger.info(f"Changed permissions for {local_ssh_key_path}")

    cmd = "ssh -T -o StrictHostKeyChecking=no git@github.com"

    sly.logger.info(f"Will run command: {cmd}")

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    stdout, stderr = process.communicate()
    sly.logger.info(f"stdout: {stdout}")
    sly.logger.info(f"stderr: {stderr}")

    if (
        "successfully authenticated" not in stdout
        and "successfully authenticated" not in stderr
    ):
        raise RuntimeError(
            f"Could not setup SSH key for GutHub. Check that {REMOTE_SSH_KEY} is correct."
        )

    return True


AppState.ssh_status = setup_ssh_key()


def install_chrome():
    sly.logger.info("Installing Google Chrome...")
    subprocess.run(["apt-get", "update"])
    subprocess.run(["apt-get", "install", "-y", "gnupg2"])

    sly.logger.info("Dependencies installed, adding Google Chrome repository...")

    response = requests.get("https://dl-ssl.google.com/linux/linux_signing_key.pub")
    subprocess.run(["apt-key", "add", "-"], input=response.text, encoding="utf-8")

    subprocess.run(
        [
            "sh",
            "-c",
            'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list',
        ]
    )

    sly.logger.info("Repository added, installing Google Chrome...")

    subprocess.run(["apt-get", "update"])
    subprocess.run(["apt-get", "install", "-y", "google-chrome-stable"])

    sly.logger.info("Google Chrome installed.")


install_chrome()
