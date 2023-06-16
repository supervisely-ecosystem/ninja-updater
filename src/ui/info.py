from supervisely.app.widgets import Text, Card, Container
import supervisely as sly

import src.globals as g

ssh_text = Text()
ssh_text.hide()


card = Card(
    title="1️⃣ Info",
    description="Check that everything is set up correctly.",
    collapsable=True,
    content=Container(widgets=[ssh_text]),
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
