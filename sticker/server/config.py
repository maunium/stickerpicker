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
from typing import NamedTuple

from mautrix.util.config import BaseFileConfig, ConfigUpdateHelper
from mautrix.types import UserID
from mautrix.client import Client


class Permissions(NamedTuple):
    access: bool = False
    create_packs: bool = False
    telegram_import: bool = False


class Config(BaseFileConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        copy = helper.copy

        copy("database")

        copy("server.host")
        copy("server.port")
        copy("server.public_url")
        copy("server.override_resource_path")
        copy("server.trust_forward_headers")

        copy("telegram_import.bot_token")
        copy("telegram_import.homeserver.address")
        copy("telegram_import.homeserver.access_token")

        copy("permissions")

        copy("logging")

    def get_permissions(self, mxid: UserID) -> Permissions:
        _, homeserver = Client.parse_user_id(mxid)
        return Permissions(**{
            **self["permissions"].get("*", {}),
            **self["permissions"].get(homeserver, {}),
            **self["permissions"].get(mxid, {}),
        })
