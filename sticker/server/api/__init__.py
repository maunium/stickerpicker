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
from aiohttp import web

from ..config import Config
from .auth import (routes as auth_routes, init as auth_init,
                   token_middleware, widget_secret_middleware)
from .fed_connector import init as init_fed_connector
from .packs import routes as packs_routes, init as packs_init
from .setup import routes as setup_routes

integrations_app = web.Application()
integrations_app.add_routes(auth_routes)

packs_app = web.Application(middlewares=[widget_secret_middleware])
packs_app.add_routes(packs_routes)

setup_app = web.Application(middlewares=[token_middleware])
setup_app.add_routes(setup_routes)


def init(config: Config) -> None:
    init_fed_connector()
    auth_init(config)
    packs_init(config)
