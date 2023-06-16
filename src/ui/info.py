from supervisely.app.widgets import Text, Card, Container
import supervisely as sly

import src.globals as g

api_text = Text("Successfully connected to the Assets API.", "success")
ssh_text = Text("Successfully set up SSH key.", "success")
api_text.hide()
ssh_text.hide()

card = Card(
    title="1️⃣ Info",
    description="Check that everything is set up correctly.",
    collapsable=True,
    content=Container(widgets=[api_text, ssh_text]),
)

if g.assets_api and g.ssh_status:
    sly.logger.info("Api is connected and SSH key is set up.")
    api_text.show()
    ssh_text.show()
