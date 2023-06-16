import supervisely as sly

from supervisely.app.widgets import Container

import src.ui.info as info
import src.ui.repos as repos
import src.ui.update as update

layout = Container(widgets=[info.card, repos.card, update.card])

app = sly.Application(layout=layout)
