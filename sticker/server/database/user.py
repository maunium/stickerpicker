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
from typing import Optional, List, ClassVar
import random
import string

from attr import dataclass
import asyncpg

from mautrix.types import UserID

from .base import Base
from .pack import Pack
from .access_token import AccessToken


@dataclass(kw_only=True)
class User(Base):
    token_charset: ClassVar[str] = string.ascii_letters + string.digits

    id: UserID
    widget_secret: str
    homeserver_url: str

    @classmethod
    def _random_token(cls) -> str:
        return "".join(random.choices(cls.token_charset, k=64))

    @classmethod
    def new(cls, id: UserID, homeserver_url: str) -> 'User':
        return User(id=id, widget_secret=cls._random_token(), homeserver_url=homeserver_url)

    @classmethod
    async def get(cls, id: UserID) -> Optional['User']:
        q = 'SELECT id, widget_secret, homeserver_url FROM "user" WHERE id=$1'
        row: asyncpg.Record = await cls.db.fetchrow(q, id)
        if row is None:
            return None
        return cls(**row)

    async def regenerate_widget_secret(self) -> None:
        self.widget_secret = self._random_token()
        await self.db.execute('UPDATE "user" SET widget_secret=$1 WHERE id=$2',
                              self.widget_secret, self.id)

    async def set_homeserver_url(self, url: str) -> None:
        self.homeserver_url = url
        await self.db.execute('UPDATE "user" SET homeserver_url=$1 WHERE id=$2', url, self.id)

    async def new_access_token(self, ip: str) -> str:
        token = self._random_token()
        token_id = await AccessToken.insert(self.id, token, ip)
        return f"{token_id}:{token}"

    async def delete(self) -> None:
        await self.db.execute('DELETE FROM "user" WHERE id=$1', self.id)

    async def insert(self) -> None:
        q = 'INSERT INTO "user" (id, widget_secret, homeserver_url) VALUES ($1, $2, $3)'
        await self.db.execute(q, self.id, self.widget_secret, self.homeserver_url)

    async def get_packs(self) -> List[Pack]:
        res = await self.db.fetch("SELECT id, owner, title, meta FROM user_pack "
                                  "LEFT JOIN pack ON pack.id=user_pack.pack_id "
                                  'WHERE user_id=$1 ORDER BY "order"', self.id)
        return [Pack(**row) for row in res]

    async def get_pack(self, pack_id: str) -> Optional[Pack]:
        row = await self.db.fetchrow("SELECT id, owner, title, meta FROM user_pack "
                                     "LEFT JOIN pack ON pack.id=user_pack.pack_id "
                                     "WHERE user_id=$1 AND pack_id=$2", self.id, pack_id)
        if row is None:
            return None
        return Pack(**row)

    async def set_packs(self, packs: List[Pack]) -> None:
        data = ((self.id, pack.id, order)
                for order, pack in enumerate(packs))
        columns = ["user_id", "pack_id", "order"]
        async with self.db.acquire() as conn, conn.transaction():
            await conn.execute("DELETE FROM user_pack WHERE user_id=$1", self.id)
            await conn.copy_records_to_table("user_pack", records=data, columns=columns)
