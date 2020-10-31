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
from typing import Dict
import json

from aiohttp import web


class _ErrorMeta:
    def __init__(self, *args, **kwargs) -> None:
        pass

    @staticmethod
    def _make_error(errcode: str, error: str) -> Dict[str, str]:
        return {
            "body": json.dumps({
                "error": error,
                "errcode": errcode,
            }).encode("utf-8"),
            "content_type": "application/json",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, GET, POST, PUT, DELETE, HEAD",
                "Access-Control-Allow-Headers": "Authorization, Content-Type",
            }
        }

    @property
    def request_not_json(self) -> web.HTTPException:
        return web.HTTPBadRequest(**self._make_error("M_NOT_JSON",
                                                     "Request body is not valid JSON"))

    @property
    def missing_auth_header(self) -> web.HTTPException:
        return web.HTTPForbidden(**self._make_error("M_MISSING_TOKEN",
                                                    "Missing authorization header"))

    @property
    def missing_user_id_header(self) -> web.HTTPException:
        return web.HTTPForbidden(**self._make_error("NET.MAUNIUM_MISSING_USER_ID",
                                                    "Missing user ID header"))

    @property
    def user_not_found(self) -> web.HTTPException:
        return web.HTTPNotFound(**self._make_error("NET.MAUNIUM_USER_NOT_FOUND",
                                                   "User not found"))

    @property
    def invalid_auth_header(self) -> web.HTTPException:
        return web.HTTPForbidden(**self._make_error("M_UNKNOWN_TOKEN",
                                                    "Invalid authorization header"))

    @property
    def invalid_auth_token(self) -> web.HTTPException:
        return web.HTTPForbidden(**self._make_error("M_UNKNOWN_TOKEN",
                                                    "Invalid authorization token"))

    @property
    def auth_token_expired(self) -> web.HTTPException:
        return web.HTTPForbidden(**self._make_error("NET.MAUNIUM_TOKEN_EXPIRED",
                                                    "Authorization token has expired"))

    @property
    def invalid_openid_payload(self) -> web.HTTPException:
        return web.HTTPBadRequest(**self._make_error("M_BAD_JSON", "Missing one or more "
                                                                   "fields in OpenID payload"))

    @property
    def invalid_openid_token(self) -> web.HTTPException:
        return web.HTTPForbidden(**self._make_error("M_UNKNOWN_TOKEN",
                                                    "Invalid OpenID token"))

    @property
    def no_access(self) -> web.HTTPException:
        return web.HTTPUnauthorized(**self._make_error(
            "M_UNAUTHORIZED",
            "You are not authorized to access this maunium-stickerpicker instance"))

    @property
    def homeserver_mismatch(self) -> web.HTTPException:
        return web.HTTPUnauthorized(**self._make_error(
            "M_UNAUTHORIZED", "Request matrix_server_name and OpenID sub homeserver don't match"))

    @property
    def pack_not_found(self) -> web.HTTPException:
        return web.HTTPNotFound(**self._make_error("NET.MAUNIUM_PACK_NOT_FOUND",
                                                   "Sticker pack not found"))

    @property
    def client_well_known_error(self) -> web.HTTPException:
        return web.HTTPForbidden(**self._make_error("NET.MAUNIUM_CLIENT_WELL_KNOWN_ERROR",
                                                    "Failed to resolve homeserver URL "
                                                    "from client .well-known"))


class Error(metaclass=_ErrorMeta):
    pass
