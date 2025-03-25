# maunium-stickerpicker - A fast and simple Matrix sticker picker widget.
# Copyright (C) 2025 Tulir Asokan
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
from pathlib import Path
from typing import Dict
import argparse
import asyncio
import json

from aiohttp import ClientSession
from yarl import URL

from .lib import matrix, util

parser = argparse.ArgumentParser()
parser.add_argument("--config",
                    help="Path to JSON file with Matrix homeserver and access_token",
                    type=str, default="config.json", metavar="file")
parser.add_argument("path", help="Path to the sticker pack JSON file", type=str)


async def main(args: argparse.Namespace) -> None:
    await matrix.load_config(args.config)
    with util.open_utf8(args.path) as pack_file:
        pack = json.load(pack_file)
        print(f"Loaded existing pack meta from {args.path}")

    stickers_data: Dict[str, bytes] = {}
    async with ClientSession() as sess:
        for sticker in pack["stickers"]:
            dl_url = URL(matrix.homeserver_url) / "_matrix/client/v1/media/download" / sticker["url"].removeprefix("mxc://")
            print("Downloading", sticker["url"])
            async with sess.get(dl_url, headers={"Authorization": f"Bearer {matrix.access_token}"}) as resp:
                resp.raise_for_status()
                stickers_data[sticker["url"]] = await resp.read()

    print("All stickers downloaded, generating thumbnails...")
    util.add_thumbnails(pack["stickers"], stickers_data, Path(args.path).parent)
    print("Done!")

def cmd():
    asyncio.run(main(parser.parse_args()))


if __name__ == "__main__":
    cmd()
