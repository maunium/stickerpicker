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
from typing import Any
import random
import string
import json

from aiohttp import web
from pkg_resources import resource_stream
import jsonschema

from ..database import User, AccessToken, Pack, Sticker
from .errors import Error

routes = web.RouteTableDef()

pack_schema = json.load(resource_stream("sticker.server.api", "pack.schema.json"))


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


@routes.get("/packs")
async def packs(req: web.Request) -> web.Response:
    user: User = req["user"]
    packs = await user.get_packs()
    return web.json_response([pack.to_dict() for pack in packs])


async def get_json(req: web.Request, schema: str) -> Any:
    try:
        data = await req.json()
    except json.JSONDecodeError:
        raise Error.request_not_json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise Error.schema_error(e.message, e.path)
    return data


@routes.post("/packs/create")
async def upload_pack(req: web.Request) -> web.Response:
    data = await get_json(req, pack_schema)
    user: User = req["user"]
    title = data.pop("title")
    raw_stickers = data.pop("stickers")
    pack_id_suffix = data.pop("id", "".join(random.choices(string.ascii_lowercase, k=12)))
    pack = Pack(id=f"{user.id}_{pack_id_suffix}", owner=user.id, title=title, meta=data)
    stickers = [Sticker(pack_id=pack.id, id=sticker.pop("id"), url=sticker.pop("url"),
                        body=sticker.pop("body"), meta=sticker) for sticker in raw_stickers]
    await pack.insert()
    await pack.set_stickers(stickers)
    await user.add_pack(pack)

    return web.json_response({
        **pack.to_dict(),
        "stickers": [sticker.to_dict() for sticker in stickers],
    })


@routes.get("/pack/{pack_id}")
async def get_pack(req: web.Request) -> web.Response:
    user: User = req["user"]
    pack = await user.get_pack(req.match_info["pack_id"])
    if pack is None:
        raise Error.pack_not_found
    return web.json_response({
        **pack.to_dict(),
        "stickers": [sticker.to_dict() for sticker in await pack.get_stickers()],
    })


@routes.delete("/pack/{pack_id}")
async def delete_pack(req: web.Request) -> web.Response:
    user: User = req["user"]
    pack = await user.get_pack(req.match_info["pack_id"])
    if pack is None:
        raise Error.pack_not_found

    if pack.owner != user.id:
        await user.remove_pack(pack)
    else:
        await pack.delete()
    return web.Response(status=204)
