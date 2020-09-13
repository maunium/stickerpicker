import sys
import json

index_path = "../web/packs/index.json"

try:
    with open(index_path) as index_file:
        index_data = json.load(index_file)
except (FileNotFoundError, json.JSONDecodeError):
    index_data = {"packs": []}

with open(sys.argv[-1]) as file:
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
    with open(pack_path, "w") as pack_file:
        json.dump(pack_data, pack_file)
    print(f"Wrote {title} to {pack_path}")
    if filename not in index_data["packs"]:
        index_data["packs"].append(filename)

with open(index_path, "w") as index_file:
    json.dump(index_data, index_file, indent="  ")
print(f"Updated {index_path}")
