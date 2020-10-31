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

from ..database import User
from ..config import Config
from .errors import Error

routes = web.RouteTableDef()
config: Config


@routes.get("/index.json")
async def get_packs(req: web.Request) -> web.Response:
    user: User = req["user"]
    packs = await user.get_packs()
    return web.json_response({
        "homeserver_url": user.homeserver_url,
        "is_sticker_server": True,
        "packs": [f"{pack.id}.json" for pack in packs],
    })


@routes.get("/{pack_id}.json")
async def get_pack(req: web.Request) -> web.Response:
    user: User = req["user"]
    pack = await user.get_pack(req.match_info["pack_id"])
    if pack is None:
        raise Error.pack_not_found
    stickers = await pack.get_stickers()
    return web.json_response({
        **pack.to_dict(),
        "stickers": [sticker.to_dict() for sticker in stickers],
    })


def init(cfg: Config) -> None:
    global config
    config = cfg
