import os
import subprocess
import json
import shutil
from typing import List, Dict, Literal

import supervisely as sly
from supervisely.app.widgets import (
    Container,
    Card,
    Progress,
    Button,
    Flexbox,
    Select,
    Field,
    Checkbox,
)
from git import Repo

import src.globals as g

stats_select = Select(
    [Select.Item(stat) for stat in g.STATS_OPTIONS], multiple=True, filterable=True
)
reset_stats_button = Button("Clean selection", "text", "small")
stats_field = Field(
    content=Container([stats_select, reset_stats_button], gap=0),
    title="Force statistics",
)

visuals_select = Select(
    [Select.Item(visual) for visual in g.VISUALS_OPTIONS],
    multiple=True,
    filterable=True,
)
reset_visuals_button = Button("Clean selection", "text", "small")
visuals_field = Field(
    content=Container([visuals_select, reset_visuals_button], gap=0),
    title="Force visuals",
)

texts_select = Select(
    [Select.Item(text) for text in g.TEXTS_OPTIONS], multiple=True, filterable=True
)
reset_texts_button = Button("Clean selection", "text", "small")
texts_field = Field(
    content=Container([texts_select, reset_texts_button], gap=0),
    title="Force texts",
)
download_sly_url_checkbox = Checkbox("Force download sly url")
demo_checkbox = Checkbox("Force demo sample project")


select_container = Container(
    [
        stats_field,
        visuals_field,
        texts_field,
        download_sly_url_checkbox,
        demo_checkbox,
    ]
)


start_button = Button("Start", icon="zmdi zmdi-play-circle-outline")
stop_button = Button("Stop", icon="zmdi zmdi-stop", button_type="danger")
stop_button.hide()

buttons_flexbox = Flexbox([start_button, stop_button])

repos_progress = Progress()
repos_progress.hide()

card = Card(
    title="3️⃣ Update",
    description="Select what to update and start the process.",
    content=Container(widgets=[select_container, repos_progress]),
    collapsable=True,
    content_top_right=buttons_flexbox,
)
card.lock()
card.collapse()


@start_button.click
def start():
    force_stats = stats_select.get_value()
    force_visuals = visuals_select.get_value()
    force_texts = texts_select.get_value()

    if "ClassesPreview" in force_visuals:
        force_stats.append(force_visuals.pop(force_visuals.index("ClassesPreview")))

    start_button.text = "Processing..."
    stop_button.show()

    forces = {
        "force_stats": force_stats or [],
        "force_visuals": force_visuals or [],
        "force_texts": force_texts or [],
        "force_download_sly_url": download_sly_url_checkbox.is_checked(),
        "force_demo": demo_checkbox.is_checked(),
    }

    repos_to_update = g.AppState.selected_repos

    repos_progress.show()
    with repos_progress(
        message="Processing repositories...", total=len(repos_to_update)
    ) as pbar:
        idx = 1
        for repo_url in repos_to_update:
            if g.AppState.continue_processing:
                process_repo(repo_url, idx, forces)
                pbar.update(1)
                idx += 1
            else:
                break

    sly.logger.info("Finished processing all repositories.")
    stop_button.hide()
    start_button.text = "Start"


@stop_button.click
def stop():
    stop_button.hide()
    start_button.text = "Stopping..."
    g.AppState.continue_processing = False


@reset_stats_button.click
def reset():
    stats_select.set_value(value=[])


@reset_visuals_button.click
def reset():
    visuals_select.set_value(value=[])


@reset_texts_button.click
def reset():
    texts_select.set_value(value=[])


def process_repo(repo_url: str, idx: int, forces: Dict[str, List[str]]):
    repo_name = repo_url.split("/")[-1].split(".")[0]
    git_url = f"{repo_url.split('.com/')[-1]}.git"
    ssh_url = f"git@github.com:{git_url}"

    update_table(idx, "working")

    sly.logger.info(
        f"Started processing repo {repo_name} from {repo_url} and following forces: {forces}"
    )

    local_repo_path = os.path.join(g.REPOS_DIR, repo_name)
    sly.fs.mkdir(local_repo_path, remove_content_if_exists=True)

    repo = Repo.clone_from(ssh_url, local_repo_path)

    sly.logger.info(f"Cloned repo from git url {git_url} to {local_repo_path}.")

    repo_requirements_path = os.path.join(local_repo_path, "requirements.txt")
    # Installing repo requirements to local environment, if requirements.txt exists.
    if os.path.exists(repo_requirements_path):
        sly.logger.info(
            f"Found requirements.txt in {repo_name} repo, will install requirements."
        )
        # Excluding supervisely and dataset-tools from requirements.txt
        repo_requirements = open(repo_requirements_path, "r").readlines()
        to_install = []
        for line in repo_requirements:
            if "supervisely" not in line and "dataset-tools" not in line:
                to_install.append(line.strip())

        sly.logger.info(f"Found {len(to_install)} requirements to install.")
        # Installing requirements.

        for line in to_install:
            sly.logger.info(f"Installing {line}...")
            return_code = subprocess.check_call(
                f"{find_pip3_path()} install {line}",
                shell=True,
                cwd=local_repo_path,
                stdout=subprocess.PIPE,
                text=True,
            )

            if return_code != 0:
                sly.logger.error(f"Failed to install {line}.")
                update_table(idx, "error")
                return

            sly.logger.info(f"Successfully installed {line}.")

    script_path = os.path.join(local_repo_path, "src", "main.py")
    command = f"PYTHONPATH=\"{local_repo_path}:${{PYTHONPATH}}\" python {script_path} --forces '{json.dumps(forces)}'"

    sly.logger.info(f"Preparing to run command: {command}")

    process = subprocess.Popen(
        command, shell=True, cwd=local_repo_path, stdout=subprocess.PIPE, text=True
    )

    for line in iter(process.stdout.readline, ""):
        print(line.strip())

    # Wait for the process to finish and get the return code.
    return_code = process.wait()

    if return_code != 0:
        sly.logger.error(f"Script finished with error code {return_code}.")
        update_table(idx, "error")
        return
    else:
        sly.logger.info("Script finished successfully.")

    delete_pycache(local_repo_path)

    # Adding all files to index.
    index = repo.index
    index.add("*")

    # If there is no changes in index, then there is nothing to commit.
    if not index.diff("HEAD"):
        sly.logger.info(
            f"No files was added to index in {repo_name} repo. Nothing to commit."
        )
        sly.fs.remove_dir(local_repo_path)
        update_table(idx, "finished")
        return

    repo.index.commit("Automatic commit by repo-updater.")

    sly.logger.info("Created commit. Pushing...")

    remote = repo.remote("origin")
    remote.push()

    update_table(idx, "finished")


def find_pip3_path():
    try:
        result = subprocess.run(["which", "pip3"], capture_output=True, text=True)
        if result.returncode == 0:
            pip3_path = result.stdout.strip()
            return pip3_path
        else:
            print(f"Command 'which pip3' exited with return code {result.returncode}")
    except FileNotFoundError:
        print("Command 'which' not found")

    return None


def delete_pycache(local_repo_path):
    pycache_dir = os.path.join(local_repo_path, "src", "__pycache__")
    shutil.rmtree(pycache_dir, ignore_errors=True)


def update_table(repo_url, status: Literal["waiting", "working", "finished", "error"]):
    from src.ui.repos import repo_table

    key_column_name = column_name = "#"
    key_cell_value = repo_url
    column_name = "Status"
    new_value = g.REPO_STATUSES[status]

    repo_table.loading = True

    repo_table.update_cell_value(
        key_column_name, key_cell_value, column_name, new_value
    )

    repo_table.loading = False
