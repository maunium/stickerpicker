# Copyright (c) 2020 Tulir Asokan
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from typing import Optional, TYPE_CHECKING
import json

from aiohttp import ClientSession
from yarl import URL

access_token: Optional[str] = None
homeserver_url: Optional[str] = None

upload_url: Optional[URL] = None

if TYPE_CHECKING:
    from typing import TypedDict


    class MediaInfo(TypedDict):
        w: int
        h: int
        size: int
        mimetype: str
        thumbnail_url: Optional[str]
        thumbnail_info: Optional['MediaInfo']


    class StickerInfo(TypedDict, total=False):
        body: str
        url: str
        info: MediaInfo
        id: str
else:
    MediaInfo = None
    StickerInfo = None


async def load_config(path: str) -> None:
    global access_token, homeserver_url, upload_url
    try:
        with open(path) as config_file:
            config = json.load(config_file)
            homeserver_url = config["homeserver"]
            access_token = config["access_token"]
    except FileNotFoundError:
        print("Matrix config file not found. Please enter your homeserver and access token.")
        homeserver_url = input("Homeserver URL: ")
        access_token = input("Access token: ")
        whoami_url = URL(homeserver_url) / "_matrix" / "client" / "r0" / "account" / "whoami"
        user_id = await whoami(whoami_url, access_token)
        with open(path, "w") as config_file:
            json.dump({
                "homeserver": homeserver_url,
                "user_id": user_id,
                "access_token": access_token
            }, config_file)
        print(f"Wrote config to {path}")

    upload_url = URL(homeserver_url) / "_matrix" / "media" / "r0" / "upload"


async def whoami(url: URL, access_token: str) -> str:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with ClientSession() as sess, sess.get(url, headers=headers) as resp:
        resp.raise_for_status()
        user_id = (await resp.json())["user_id"]
        print(f"Access token validated (user ID: {user_id})")
        return user_id


async def upload(data: bytes, mimetype: str, filename: str) -> str:
    url = upload_url.with_query({"filename": filename})
    headers = {"Content-Type": mimetype, "Authorization": f"Bearer {access_token}"}
    async with ClientSession() as sess, sess.post(url, data=data, headers=headers) as resp:
        return (await resp.json())["content_uri"]
