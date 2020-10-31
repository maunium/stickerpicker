from typing import Tuple, Any, NamedTuple, Dict, Optional
from time import time
import ipaddress
import logging
import asyncio
import json

from mautrix.util.logging import TraceLogger
from aiohttp import ClientRequest, TCPConnector, ClientSession, ClientTimeout, ClientError
from aiohttp.client_proto import ResponseHandler
from yarl import URL
import aiodns

log: TraceLogger = logging.getLogger("mau.federation")


class ResolvedServerName(NamedTuple):
    host_header: str
    host: str
    port: int
    expire: int


class ServerNameSplit(NamedTuple):
    host: str
    port: Optional[int]
    is_ip: bool


dns_resolver: aiodns.DNSResolver
http: ClientSession
server_name_cache: Dict[str, ResolvedServerName] = {}


class MatrixFederationTCPConnector(TCPConnector):
    """An extension to aiohttp's TCPConnector that correctly sets the TLS SNI for Matrix federation
    requests, where the TCP host may not match the SNI/Host header."""

    async def _wrap_create_connection(self, *args: Any, server_hostname: str, req: ClientRequest,
                                      **kwargs: Any) -> Tuple[asyncio.Transport, ResponseHandler]:
        split = parse_server_name(req.headers["Host"])
        return await super()._wrap_create_connection(*args, server_hostname=split.host,
                                                     req=req, **kwargs)


def parse_server_name(name: str) -> ServerNameSplit:
    port_split = name.rsplit(":", 1)
    if len(port_split) == 2 and port_split[1].isdecimal():
        name, port = port_split
    else:
        port = None
    try:
        ipaddress.ip_address(name)
        is_ip = True
    except ValueError:
        is_ip = False
    res = ServerNameSplit(host=name, port=port, is_ip=is_ip)
    log.trace(f"Parsed server name {name} into {res}")
    return res


async def resolve_server_name(server_name: str) -> ResolvedServerName:
    try:
        cached = server_name_cache[server_name]
        if cached.expire > int(time()):
            log.trace(f"Using cached server name resolution for {server_name}: {cached}")
            return cached
    except KeyError:
        log.trace(f"No cached server name resolution for {server_name}")

    host_header = server_name
    hostname, port, is_ip = parse_server_name(host_header)
    ttl = 86400
    if port is None and not is_ip:
        well_known_url = URL.build(scheme="https", host=host_header, port=443,
                                   path="/.well-known/matrix/server")
        try:
            log.trace(f"Requesting {well_known_url} to resolve {server_name}'s .well-known")
            async with http.get(well_known_url) as resp:
                if resp.status == 200:
                    well_known_data = await resp.json()
                    host_header = well_known_data["m.server"]
                    log.debug(f"Got {host_header} from {server_name}'s .well-known")
                    hostname, port, is_ip = parse_server_name(host_header)
                else:
                    log.trace(f"Got non-200 status {resp.status} from {server_name}'s .well-known")
        except (ClientError, json.JSONDecodeError, KeyError, ValueError) as e:
            log.debug(f"Failed to fetch .well-known for {server_name}: {e}")
    if port is None and not is_ip:
        log.trace(f"Querying SRV at _matrix._tcp.{host_header}")
        res = await dns_resolver.query(f"_matrix._tcp.{host_header}", "SRV")
        if res:
            hostname = res[0].host
            port = res[0].port
            ttl = max(res[0].ttl, 300)
            log.debug(f"Got {hostname}:{port} from {host_header}'s Matrix SRV record")
        else:
            log.trace(f"No SRV records found at _matrix._tcp.{host_header}")
    result = ResolvedServerName(host_header=host_header, host=hostname, port=port or 8448,
                                expire=int(time()) + ttl)
    server_name_cache[server_name] = result
    log.debug(f"Resolved server name {server_name} -> {result}")
    return result


def init():
    global http, dns_resolver
    dns_resolver = aiodns.DNSResolver(loop=asyncio.get_running_loop())
    http = ClientSession(timeout=ClientTimeout(total=10),
                         connector=MatrixFederationTCPConnector())
