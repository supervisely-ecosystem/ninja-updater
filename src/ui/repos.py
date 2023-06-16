from typing import List

from supervisely.app.widgets import (
    Text,
    Card,
    Container,
    Transfer,
    Button,
    Table,
)
import supervisely as sly

import src.globals as g
import src.ui.update as update

tr_items = [
    Transfer.Item(key=repo_url, label=repo_name) for repo_name, repo_url in g.REPOS
]
tr = Transfer(
    items=tr_items,
    titles=["Repositories", "Selected repositories"],
    filterable=True,
    filter_placeholder="Search repos",
)

COLUMNS = ["#", "Repository", "Status"]
repo_table = Table(fixed_cols=1)
repo_table.hide()

not_selected_text = Text("No repositories selected.", "warning")
not_selected_text.hide()
lock_button = Button("Lock", icon="zmdi zmdi-lock-outline")
unlock_button = Button("Unlock", icon="zmdi zmdi-lock-open")
unlock_button.hide()


card = Card(
    title="2️⃣ Repositories",
    description="Select repositories to update.",
    content=Container(widgets=[tr, repo_table, not_selected_text, lock_button]),
    content_top_right=unlock_button,
    collapsable=True,
)


@lock_button.click
def lock():
    not_selected_text.hide()
    selected_repos = tr.get_transferred_items()
    if not selected_repos:
        not_selected_text.show()
        return

    unlock_button.show()
    lock_button.hide()
    tr.hide()

    update_table(selected_repos)

    g.AppState.selected_repos = selected_repos
    sly.logger.info(f"Selected repos: {selected_repos} saved to AppState.")

    update.card.unlock()
    update.card.uncollapse()


@unlock_button.click
def unlock():
    unlock_button.hide()
    lock_button.show()
    not_selected_text.hide()
    tr.show()

    update_table()

    g.AppState.selected_repos = []
    sly.logger.info("Selected repos cleared from AppState.")

    update.card.lock()
    update.card.collapse()


def update_table(selected_repos: List = None):
    if selected_repos:
        idx = 1
        rows = []
        for repo_url in selected_repos:
            row = [
                idx,
                f"<a href={repo_url}>{repo_url}</a>",
                g.REPO_STATUSES["waiting"],
            ]
            idx += 1
            rows.append(row)

        repo_table.show()
    else:
        rows = []
        repo_table.hide()

    table_data = {"columns": COLUMNS, "data": rows}
    repo_table.read_json(table_data)
