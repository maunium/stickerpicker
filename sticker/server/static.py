# Simplified version of aiohttp's StaticResource with support for index.html
# https://github.com/aio-libs/aiohttp/blob/v3.6.2/aiohttp/web_urldispatcher.py#L496-L678
# Licensed under Apache 2.0
from typing import Callable, Awaitable, Tuple, Optional, Union, Dict, Set, Iterator, Any
from pathlib import Path, PurePath

from aiohttp.web import (Request, StreamResponse, FileResponse, ResourceRoute, AbstractResource,
                         AbstractRoute, UrlMappingMatchInfo, HTTPNotFound, HTTPForbidden)
from aiohttp.abc import AbstractMatchInfo
from yarl import URL

Handler = Callable[[Request], Awaitable[StreamResponse]]


class StaticResource(AbstractResource):
    def __init__(self, prefix: str, directory: Union[str, PurePath], *, name: Optional[str] = None,
                 error_path: Optional[str] = "index.html", chunk_size: int = 256 * 1024) -> None:
        super().__init__(name=name)
        try:
            directory = Path(directory).resolve()
            if not directory.is_dir():
                raise ValueError("Not a directory")
        except (FileNotFoundError, ValueError) as error:
            raise ValueError(f"No directory exists at '{directory}'") from error
        self._directory = directory
        self._chunk_size = chunk_size
        self._prefix = prefix
        self._error_file = (directory / error_path) if error_path else None

        self._routes = {
            "GET": ResourceRoute("GET", self._handle, self),
            "HEAD": ResourceRoute("HEAD", self._handle, self),
        }

    @property
    def canonical(self) -> str:
        return self._prefix

    def add_prefix(self, prefix: str) -> None:
        assert prefix.startswith("/")
        assert not prefix.endswith("/")
        assert len(prefix) > 1
        self._prefix = prefix + self._prefix

    def raw_match(self, prefix: str) -> bool:
        return False

    def url_for(self, *, filename: Union[str, Path]) -> URL:
        if isinstance(filename, Path):
            filename = str(filename)
        while filename.startswith("/"):
            filename = filename[1:]
        return URL.build(path=f"{self._prefix}/{filename}")

    def get_info(self) -> Dict[str, Any]:
        return {
            "directory": self._directory,
            "prefix": self._prefix,
        }

    def set_options_route(self, handler: Handler) -> None:
        if "OPTIONS" in self._routes:
            raise RuntimeError("OPTIONS route was set already")
        self._routes["OPTIONS"] = ResourceRoute("OPTIONS", handler, self)

    async def resolve(self, request: Request) -> Tuple[Optional[AbstractMatchInfo], Set[str]]:
        path = request.rel_url.raw_path
        method = request.method
        allowed_methods = set(self._routes)
        if not path.startswith(self._prefix):
            return None, set()

        if method not in allowed_methods:
            return None, allowed_methods

        return UrlMappingMatchInfo({
            "filename": URL.build(path=path[len(self._prefix):], encoded=True).path
        }, self._routes[method]), allowed_methods

    def __len__(self) -> int:
        return len(self._routes)

    def __iter__(self) -> Iterator[AbstractRoute]:
        return iter(self._routes.values())

    async def _handle(self, request: Request) -> StreamResponse:
        try:
            filename = Path(request.match_info["filename"])
            if not filename.anchor:
                filepath = (self._directory / filename).resolve()
                if filepath.is_file():
                    return FileResponse(filepath, chunk_size=self._chunk_size)
                index_path = (self._directory / filename / "index.html").resolve()
                if index_path.is_file():
                    return FileResponse(index_path, chunk_size=self._chunk_size)
        except (ValueError, FileNotFoundError) as error:
            raise HTTPNotFound() from error
        except HTTPForbidden:
            raise
        except Exception as error:
            request.app.logger.exception("Error while trying to serve static file")
            raise HTTPNotFound() from error

    def __repr__(self) -> str:
        name = f"'{self.name}'" if self.name is not None else ""
        return f"<StaticResource {name} {self._prefix} -> {self._directory!r}>"
