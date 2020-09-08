# packs

This directory contains some ready-to-use stickerpack metadata. Currently
it's just all the packs imported from Scalar (the default integration manager).

To use these, copy the packs you want to `web/packs/`, then edit
`web/packs/index.json` to include the file names you copied in the `packs`
array. The index.json file should look something like this:

```json
{
  "homeserver_url": "https://example.com",
  "packs": [
    "your_telegram_imported_pack.json",
    "another_telegram_imported_pack.json",
    "scalar-rabbit.json",
    "scalar-loading_artist.json"
  ]
}
```
