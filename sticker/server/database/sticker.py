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
from typing import Dict, Any

from attr import dataclass
import attr

from mautrix.types import ContentURI

from .base import Base


@dataclass(kw_only=True)
class Sticker(Base):
    pack_id: str
    order: int
    id: str
    url: ContentURI = attr.ib(order=False)
    body: str = attr.ib(order=False)
    meta: Dict[str, Any] = attr.ib(order=False)

    async def delete(self) -> None:
        await self.db.execute("DELETE FROM sticker WHERE id=$1", self.id)

    async def insert(self) -> None:
        await self.db.execute('INSERT INTO sticker (id, pack_id, url, body, meta, "order") '
                              "VALUES ($1, $2, $3, $4, $5, $6)",
                              self.id, self.pack_id, self.url, self.body, self.meta, self.order)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.meta,
            "body": self.body,
            "url": self.url,
            "id": self.id,
        }
