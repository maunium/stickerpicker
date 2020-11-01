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
from typing import List, Dict, Any
import json

from attr import dataclass

from mautrix.types import UserID

from .base import Base
from .sticker import Sticker


@dataclass(kw_only=True)
class Pack(Base):
    id: str
    owner: UserID
    title: str
    meta: Dict[str, Any]

    async def delete(self) -> None:
        await self.db.execute("DELETE FROM pack WHERE id=$1", self.id)

    async def insert(self) -> None:
        await self.db.execute("INSERT INTO pack (id, owner, title, meta) VALUES ($1, $2, $3, $4)",
                              self.id, self.owner, self.title, json.dumps(self.meta))

    @classmethod
    def from_data(cls, **data: Any) -> 'Pack':
        meta = json.loads(data.pop("meta"))
        return cls(**data, meta=meta)

    async def get_stickers(self) -> List[Sticker]:
        res = await self.db.fetch('SELECT id, url, body, meta, "order" '
                                  'FROM sticker WHERE pack_id=$1 ORDER BY "order"', self.id)
        return [Sticker.from_data(**row, pack_id=self.id) for row in res]

    async def set_stickers(self, stickers: List[Sticker]) -> None:
        data = ((sticker.id, self.id, sticker.url, sticker.body, json.dumps(sticker.meta), order)
                for order, sticker in enumerate(stickers))
        columns = ["id", "pack_id", "url", "body", "meta", "order"]
        async with self.db.acquire() as conn, conn.transaction():
            await conn.execute("DELETE FROM sticker WHERE pack_id=$1", self.id)
            await conn.copy_records_to_table("sticker", records=data, columns=columns)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.meta,
            "title": self.title,
            "id": self.id,
        }
