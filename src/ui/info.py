import subprocess

from supervisely.app.widgets import Text, Card, Container, Button
import supervisely as sly

import src.globals as g

ssh_text = Text()
ssh_text.hide()

update_dtools_button = Button("Update dtools", icon="zmdi zmdi-refresh")

card = Card(
    title="1️⃣ Info",
    description="Check that everything is set up correctly.",
    collapsable=True,
    content=Container(widgets=[ssh_text]),
    content_top_right=update_dtools_button,
)

if g.AppState.ssh_status:
    sly.logger.info("SSH keys are set up correctly.")
    ssh_text.text = "SSH keys are set up correctly."
    ssh_text.status = "success"
else:
    sly.logger.error("SSH keys are not set up correctly.")
    ssh_text.text = "SSH keys are not set up correctly."
    ssh_text.status = "error"

ssh_text.show()


@update_dtools_button.click
def update_dtools():
    update_dtools_button.text = "Updating..."

    return_code = subprocess.check_call(
        "pip install git+https://github.com/supervisely/dataset-tools",
        shell=True,
        stdout=subprocess.PIPE,
        text=True,
    )

    if return_code != 0:
        sly.logger.error(f"Failed to update dtools. Return code: {return_code}")

        sly.app.show_dialog(
            title="Update dtools failed",
            description=(
                f"Updated of dtools failed with return code {return_code}. "
                "It's recommended to restart the app."
            ),
            status="error",
        )

    else:
        sly.logger.info("dtools updated successfully.")

    update_dtools_button.text = "Update dtools"
