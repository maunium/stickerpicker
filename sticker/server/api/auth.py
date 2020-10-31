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
from typing import Tuple, Callable, Awaitable, Optional, TYPE_CHECKING
import logging
import json

from mautrix.client import Client
from mautrix.types import UserID
from mautrix.util.logging import TraceLogger
from aiohttp import web, hdrs, ClientError, ClientSession
from yarl import URL

from ..database import AccessToken, User
from ..config import Config
from .errors import Error
from . import fed_connector

if TYPE_CHECKING:
    from typing import TypedDict


    class OpenIDPayload(TypedDict):
        access_token: str
        token_type: str
        matrix_server_name: str
        expires_in: int


    class OpenIDResponse(TypedDict):
        sub: str

Handler = Callable[[web.Request], Awaitable[web.Response]]

log: TraceLogger = logging.getLogger("mau.api.auth")
routes = web.RouteTableDef()
config: Config


def get_ip(request: web.Request) -> str:
    if config["server.trust_forward_headers"]:
        try:
            return request.headers["X-Forwarded-For"]
        except KeyError:
            pass
    return request.remote


def get_auth_header(request: web.Request) -> str:
    try:
        auth = request.headers["Authorization"]
        if not auth.startswith("Bearer "):
            raise Error.invalid_auth_header
        return auth[len("Bearer "):]
    except KeyError:
        raise Error.missing_auth_header


async def get_user(request: web.Request) -> Tuple[User, AccessToken]:
    auth = get_auth_header(request)
    try:
        token_id, token_val = auth.split(":")
        token_id = int(token_id)
    except ValueError:
        raise Error.invalid_auth_token
    token = await AccessToken.get(token_id)
    if not token or not token.check(token_val):
        raise Error.invalid_auth_token
    elif token.expired:
        raise Error.auth_token_expired
    await token.update_ip(get_ip(request))
    return await User.get(token.user_id), token


@web.middleware
async def token_middleware(request: web.Request, handler: Handler) -> web.Response:
    if request.method == hdrs.METH_OPTIONS:
        return await handler(request)
    user, token = await get_user(request)
    request["user"] = user
    request["token"] = token
    return await handler(request)


async def get_widget_user(request: web.Request) -> User:
    try:
        user_id = UserID(request.headers["X-Matrix-User-ID"])
    except KeyError:
        raise Error.missing_user_id_header
    user = await User.get(user_id)
    if user is None:
        raise Error.user_not_found
    return user


@web.middleware
async def widget_secret_middleware(request: web.Request, handler: Handler) -> web.Response:
    if request.method == hdrs.METH_OPTIONS:
        return await handler(request)
    user = await get_widget_user(request)
    request["user"] = user
    return await handler(request)


account_cors_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS, GET, POST",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
}


@routes.get("/account")
async def get_auth(request: web.Request) -> web.Response:
    user, token = await get_user(request)
    return web.json_response({"user_id": token.user_id}, headers=account_cors_headers)


async def check_openid_token(homeserver: str, token: str) -> Optional[UserID]:
    server_info = await fed_connector.resolve_server_name(homeserver)
    headers = {"Host": server_info.host_header}
    userinfo_url = URL.build(scheme="https", host=server_info.host, port=server_info.port,
                             path="/_matrix/federation/v1/openid/userinfo",
                             query={"access_token": token})
    try:
        async with fed_connector.http.get(userinfo_url, headers=headers) as resp:
            data: 'OpenIDResponse' = await resp.json()
            return UserID(data["sub"])
    except (ClientError, json.JSONDecodeError, KeyError, ValueError) as e:
        log.debug(f"Failed to check OpenID token from {homeserver}", exc_info=True)
        return None


@routes.route(hdrs.METH_OPTIONS, "/account/register")
@routes.route(hdrs.METH_OPTIONS, "/account/logout")
@routes.route(hdrs.METH_OPTIONS, "/account")
async def cors_token(_: web.Request) -> web.Response:
    return web.Response(status=200, headers=account_cors_headers)


async def resolve_client_well_known(server_name: str) -> str:
    url = URL.build(scheme="https", host=server_name, port=443, path="/.well-known/matrix/client")
    async with ClientSession() as sess, sess.get(url) as resp:
        data = await resp.json()
        return data["m.homeserver"]["base_url"]


@routes.post("/account/register")
async def exchange_token(request: web.Request) -> web.Response:
    try:
        data: 'OpenIDPayload' = await request.json()
    except json.JSONDecodeError:
        raise Error.request_not_json
    try:
        matrix_server_name = data["matrix_server_name"]
        access_token = data["access_token"]
    except KeyError:
        raise Error.invalid_openid_payload
    log.trace(f"Validating OpenID token from {matrix_server_name}")
    user_id = await check_openid_token(matrix_server_name, access_token)
    if user_id is None:
        raise Error.invalid_openid_token
    _, homeserver = Client.parse_user_id(user_id)
    if homeserver != data["matrix_server_name"]:
        raise Error.homeserver_mismatch

    permissions = config.get_permissions(user_id)
    if not permissions.access:
        raise Error.no_access

    try:
        log.trace(f"Trying to resolve {matrix_server_name}'s client .well-known")
        homeserver_url = await resolve_client_well_known(matrix_server_name)
        log.trace(f"Got {homeserver_url} from {matrix_server_name}'s client .well-known")
    except (ClientError, json.JSONDecodeError, KeyError, ValueError, TypeError):
        log.trace(f"Failed to resolve {matrix_server_name}'s client .well-known", exc_info=True)
        raise Error.client_well_known_error

    user = await User.get(user_id)
    if user is None:
        log.debug(f"Creating user {user_id} with homeserver client URL {homeserver_url}")
        user = User.new(user_id, homeserver_url=homeserver_url)
        await user.insert()
    elif user.homeserver_url != homeserver_url:
        log.debug(f"Updating {user_id}'s homeserver client URL from {user.homeserver_url} "
                  f"to {homeserver_url}")
        await user.set_homeserver_url(homeserver_url)
    token = await user.new_access_token(get_ip(request))
    return web.json_response({
        "user_id": user_id,
        "token": token,
        "permissions": permissions._asdict(),
    }, headers=account_cors_headers)


@routes.post("/account/logout")
async def logout(request: web.Request) -> web.Response:
    user, token = await get_user(request)
    await token.delete()
    return web.json_response({}, status=204, headers=account_cors_headers)


def init(cfg: Config) -> None:
    global config
    config = cfg
