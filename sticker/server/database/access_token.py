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
from typing import Optional, ClassVar
from datetime import datetime, timedelta
import hashlib

from attr import dataclass
import asyncpg

from mautrix.types import UserID

from .base import Base


@dataclass(kw_only=True)
class AccessToken(Base):
    token_expiry: ClassVar[timedelta] = timedelta(days=1)

    user_id: UserID
    token_id: int
    token_hash: bytes
    last_seen_ip: str
    last_seen_date: datetime

    @classmethod
    async def get(cls, token_id: int) -> Optional['AccessToken']:
        q = ("SELECT user_id, token_hash, last_seen_ip, last_seen_date "
             "FROM access_token WHERE token_id=$1")
        row: asyncpg.Record = await cls.db.fetchrow(q, token_id)
        if row is None:
            return None
        return cls(**row, token_id=token_id)

    async def update_ip(self, ip: str) -> None:
        if self.last_seen_ip == ip and (self.last_seen_date.replace(second=0, microsecond=0)
                                        == datetime.now().replace(second=0, microsecond=0)):
            # Same IP and last seen on this minute, skip update
            return
        q = ("UPDATE access_token SET last_seen_ip=$2, last_seen_date=current_timestamp "
             "WHERE token_id=$1 RETURNING last_seen_date")
        self.last_seen_date = await self.db.fetchval(q, self.token_id, ip)
        self.last_seen_ip = ip

    def check(self, token: str) -> bool:
        return self.token_hash == hashlib.sha256(token.encode("utf-8")).digest()

    @property
    def expired(self) -> bool:
        return self.last_seen_date + self.token_expiry < datetime.now()

    async def delete(self) -> None:
        await self.db.execute("DELETE FROM access_token WHERE token_id=$1", self.token_id)

    @classmethod
    async def insert(cls, user_id: UserID, token: str, ip: str) -> int:
        q = ("INSERT INTO access_token (user_id, token_hash, last_seen_ip, last_seen_date) "
             "VALUES ($1, $2, $3, current_timestamp) RETURNING token_id")
        hashed = hashlib.sha256(token.encode("utf-8")).digest()
        return await cls.db.fetchval(q, user_id, hashed, ip)
