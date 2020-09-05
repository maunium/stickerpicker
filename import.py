# Copyright (c) 2020 Tulir Asokan
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from typing import Dict, TypedDict
from io import BytesIO
import argparse
import os.path
import asyncio
import json
import re

from aiohttp import ClientSession
from yarl import URL
from PIL import Image

from telethon import TelegramClient
from telethon.tl.functions.messages import GetAllStickersRequest, GetStickerSetRequest
from telethon.tl.types.messages import AllStickers
from telethon.tl.types import InputStickerSetShortName, Document
from telethon.tl.types.messages import StickerSet as StickerSetFull

parser = argparse.ArgumentParser()
parser.add_argument("--list", help="List your saved sticker packs", action="store_true")
parser.add_argument("--session", help="Telethon session file name", default="sticker-import")
parser.add_argument("--config", help="Path to JSON file with Matrix homeserver and access_token",
                    type=str, default="config.json")
parser.add_argument("--output-dir", help="Directory to write packs to", default="web/packs/",
                    type=str)
parser.add_argument("pack", help="Sticker pack URLs to import", action="append", nargs="*")
args = parser.parse_args()


async def whoami(url: URL, access_token: str) -> str:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with ClientSession() as sess, sess.get(url, headers=headers) as resp:
        resp.raise_for_status()
        user_id = (await resp.json())["user_id"]
        print(f"Access token validated (user ID: {user_id})")
        return user_id


try:
    with open(args.config) as config_file:
        config = json.load(config_file)
        homeserver_url = config["homeserver"]
        access_token = config["access_token"]
except FileNotFoundError:
    print("Matrix config file not found. Please enter your homeserver and access token.")
    homeserver_url = input("Homeserver URL: ")
    access_token = input("Access token: ")
    whoami_url = URL(homeserver_url) / "_matrix" / "client" / "r0" / "account" / "whoami"
    user_id = asyncio.run(whoami(whoami_url, access_token))
    with open(args.config, "w") as config_file:
        json.dump({
            "homeserver": homeserver_url,
            "user_id": user_id,
            "access_token": access_token
        }, config_file)
    print(f"Wrote config to {args.config}")

upload_url = URL(homeserver_url) / "_matrix" / "media" / "r0" / "upload"


async def upload(data: bytes, mimetype: str, filename: str) -> str:
    url = upload_url.with_query({"filename": filename})
    headers = {"Content-Type": mimetype, "Authorization": f"Bearer {access_token}"}
    async with ClientSession() as sess, sess.post(url, data=data, headers=headers) as resp:
        return (await resp.json())["content_uri"]


class MatrixMediaInfo(TypedDict):
    w: int
    h: int
    size: int
    mimetype: str


class MatrixStickerInfo(TypedDict, total=False):
    body: str
    url: str
    info: MatrixMediaInfo


def convert_image(data: bytes) -> (bytes, int, int):
    image: Image.Image = Image.open(BytesIO(data)).convert("RGBA")
    new_file = BytesIO()
    image.save(new_file, "png")
    w, h = image.size
    return new_file.getvalue(), w, h


async def reupload_document(client: TelegramClient, document: Document) -> MatrixStickerInfo:
    print(f"Reuploading {document.id}", end="", flush=True)
    data = await client.download_media(document, file=bytes)
    print(".", end="", flush=True)
    data, width, height = convert_image(data)
    print(".", end="", flush=True)
    mxc = await upload(data, "image/png", f"{document.id}.png")
    print(".", flush=True)
    if width > 256 or height > 256:
        # Set the width and height to lower values so clients wouldn't show them as huge images
        if width > height:
            height = int(height / (width / 256))
            width = 256
        else:
            width = int(width / (height / 256))
            height = 256
    return {
        "body": "",
        "url": mxc,
        "info": {
            "w": width,
            "h": height,
            "size": len(data),
            "mimetype": "image/png",

            # Element iOS compatibility hack
            "thumbnail_url": mxc,
            "thumbnail_info": {
                "w": width,
                "h": height,
                "size": len(data),
            },
        },
    }


def add_to_index(name: str) -> None:
    index_path = os.path.join(args.output_dir, "index.json")
    try:
        with open(index_path) as index_file:
            index_data = json.load(index_file)
    except (FileNotFoundError, json.JSONDecodeError):
        index_data = {"packs": [], "homeserver_url": homeserver_url}
    if name not in index_data["packs"]:
        index_data["packs"].append(name)
        with open(index_path, "w") as index_file:
            json.dump(index_data, index_file, indent="  ")
        print(f"Added {name} to {index_path}")


async def reupload_pack(client: TelegramClient, pack: StickerSetFull) -> None:
    if pack.set.animated:
        print("Animated stickerpacks are currently not supported")
        return

    pack_path = os.path.join(args.output_dir, f"{pack.set.short_name}.json")
    try:
        os.mkdir(os.path.dirname(pack_path))
    except FileExistsError:
        pass

    print(f"Reuploading {pack.set.title} with {pack.set.count} stickers "
          f"and writing output to {pack_path}")

    already_uploaded = {}
    try:
        with open(pack_path) as pack_file:
            existing_pack = json.load(pack_file)
            already_uploaded = {sticker["net.maunium.telegram.sticker"]["id"]: sticker
                                for sticker in existing_pack["stickers"]}
            print(f"Found {len(already_uploaded)} already reuploaded stickers")
    except FileNotFoundError:
        pass

    reuploaded_documents: Dict[int, MatrixStickerInfo] = {}
    for document in pack.documents:
        try:
            reuploaded_documents[document.id] = already_uploaded[document.id]
            print(f"Skipped reuploading {document.id}")
        except KeyError:
            reuploaded_documents[document.id] = await reupload_document(client, document)

    for sticker in pack.packs:
        for document_id in sticker.documents:
            doc = reuploaded_documents[document_id]
            doc["body"] = sticker.emoticon
            doc["net.maunium.telegram.sticker"] = {
                "pack": {
                    "id": pack.set.id,
                    "short_name": pack.set.short_name,
                },
                "id": document_id,
                "emoticon": sticker.emoticon,
            }

    with open(pack_path, "w") as pack_file:
        json.dump({
            "title": pack.set.title,
            "short_name": pack.set.short_name,
            "id": pack.set.id,
            "hash": pack.set.hash,
            "stickers": list(reuploaded_documents.values()),
        }, pack_file, ensure_ascii=False)
    print(f"Saved {pack.set.title} as {pack.set.short_name}.json")

    add_to_index(os.path.basename(pack_path))


pack_url_regex = re.compile(r"^(?:(?:https?://)?(?:t|telegram)\.(?:me|dog)/addstickers/)?"
                            r"([A-Za-z0-9-_]+)"
                            r"(?:\.json)?$")


async def main():
    client = TelegramClient(args.session, 298751, "cb676d6bae20553c9996996a8f52b4d7")
    await client.start()

    if args.list:
        stickers: AllStickers = await client(GetAllStickersRequest(hash=0))
        index = 1
        width = len(str(stickers.sets))
        print("Your saved sticker packs:")
        for saved_pack in stickers.sets:
            print(f"{index:>{width}}. {saved_pack.title} "
                  f"(t.me/addstickers/{saved_pack.short_name})")
    elif args.pack[0]:
        input_packs = []
        for pack_url in args.pack[0]:
            match = pack_url_regex.match(pack_url)
            if not match:
                print(f"'{pack_url}' doesn't look like a sticker pack URL")
                return
            input_packs.append(InputStickerSetShortName(short_name=match.group(1)))
        for input_pack in input_packs:
            pack: StickerSetFull = await client(GetStickerSetRequest(input_pack))
            await reupload_pack(client, pack)
    else:
        parser.print_help()


asyncio.run(main())
