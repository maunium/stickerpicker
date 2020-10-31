from typing import ClassVar, TYPE_CHECKING

from mautrix.util.async_db import Database

fake_db = Database("") if TYPE_CHECKING else None


class Base:
    db: ClassVar[Database] = fake_db
