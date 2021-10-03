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
import sys
import json

index_path = "../web/packs/index.json"

try:
    with util.open_utf8(index_path) as index_file:
        index_data = json.load(index_file)
except (FileNotFoundError, json.JSONDecodeError):
    index_data = {"packs": []}

with util.open_utf8(sys.argv[-1]) as file:
    data = json.load(file)

for pack in data["assets"]:
    title = pack["name"].title()
    if "images" not in pack["data"]:
        print(f"Skipping {title}")
        continue
    pack_id = f"scalar-{pack['asset_id']}"
    stickers = []
    for sticker in pack["data"]["images"]:
        sticker_data = sticker["content"]
        sticker_data["id"] = sticker_data["url"].split("/")[-1]
        stickers.append(sticker_data)
    pack_data = {
        "title": title,
        "id": pack_id,
        "stickers": stickers,
    }
    filename = f"scalar-{pack['name'].replace(' ', '_')}.json"
    pack_path = f"web/packs/{filename}"
    with util.open_utf8(pack_path, "w") as pack_file:
        json.dump(pack_data, pack_file)
    print(f"Wrote {title} to {pack_path}")
    if filename not in index_data["packs"]:
        index_data["packs"].append(filename)

with util.open_utf8(index_path, "w") as index_file:
    json.dump(index_data, index_file, indent="  ")
print(f"Updated {index_path}")
