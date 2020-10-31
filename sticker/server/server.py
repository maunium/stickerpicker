# maunium-stickerpicker - A fast and simple Matrix sticker picker widget.
# Copyright (C) 2020 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from pkg_resources import resource_filename
from aiohttp import web

from .api import packs_app, setup_app, integrations_app, init as init_api
from .static import StaticResource
from .config import Config


class Server:
    config: Config
    runner: web.AppRunner
    app: web.Application
    site: web.TCPSite

    def __init__(self, config: Config) -> None:
        init_api(config)
        self.config = config
        self.app = web.Application()
        self.app.add_subapp("/_matrix/integrations/v1", integrations_app)
        self.app.add_subapp("/setup/api", setup_app)
        self.app.add_subapp("/packs", packs_app)

        resource_path = (config["server.override_resource_path"]
                         or resource_filename("sticker.server", "frontend"))
        self.app.router.register_resource(StaticResource("/", resource_path, name="frontend"))
        self.runner = web.AppRunner(self.app)

    async def start(self) -> None:
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.config["server.host"],
                                self.config["server.port"])
        await self.site.start()

    async def stop(self) -> None:
        await self.runner.cleanup()
