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

from ..database import User, AccessToken

routes = web.RouteTableDef()


@routes.get("/whoami")
async def whoami(req: web.Request) -> web.Response:
    user: User = req["user"]
    token: AccessToken = req["token"]
    return web.json_response({
        "id": user.id,
        "widget_secret": user.widget_secret,
        "homeserver_url": user.homeserver_url,
        "last_seen": int(token.last_seen_date.timestamp() / 60) * 60,
    })
