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
from asyncpg import Connection

from mautrix.util.async_db.upgrade import UpgradeTable

upgrade_table = UpgradeTable()


@upgrade_table.register(description="Initial revision")
async def upgrade_v1(conn: Connection) -> None:
    await conn.execute("""CREATE TABLE "user" (
        id             TEXT PRIMARY KEY,
        widget_secret  TEXT NOT NULL,
        homeserver_url TEXT NOT NULL
    )""")
    await conn.execute("""CREATE TABLE access_token (
        token_id       SERIAL PRIMARY KEY,
        user_id        TEXT   NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
        token_hash     BYTEA  NOT NULL,
        last_seen_ip   TEXT,
        last_seen_date TIMESTAMP
    )""")
    await conn.execute("""CREATE TABLE pack (
        id    TEXT  PRIMARY KEY,
        owner TEXT  REFERENCES "user"(id) ON DELETE SET NULL,
        title TEXT  NOT NULL,
        meta  JSONB NOT NULL
    )""")
    await conn.execute("""CREATE TABLE user_pack (
        user_id TEXT REFERENCES "user"(id) ON DELETE CASCADE,
        pack_id TEXT REFERENCES pack(id) ON DELETE CASCADE,
        "order" INT  NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, pack_id)
    )""")
    await conn.execute("""CREATE TABLE sticker (
        id      TEXT,
        pack_id TEXT  REFERENCES pack(id) ON DELETE CASCADE,
        url     TEXT  NOT NULL,
        body    TEXT  NOT NULL,
        meta    JSONB NOT NULL,
        "order" INT   NOT NULL DEFAULT 0,
        PRIMARY KEY (id, pack_id)
    )""")
