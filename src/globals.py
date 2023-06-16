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

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/ninja.env"))
api: sly.Api = sly.Api.from_env()

TEAM_ID = sly.io.env.team_id()
WORKSPACE_ID = sly.io.env.workspace_id()

REMOTE_SSH_KEY = sly.env.file()
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
        self.ssh_status = False
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

    response = process.communicate()
    for line in response:
        sly.logger.info(line)
    if not any(line.startswith("Hi") for line in response):
        raise RuntimeError(
            "Could not connect to GitHub. Check that the SSH key is set up correctly."
        )

    return True


AppState.ssh_status = setup_ssh_key()
