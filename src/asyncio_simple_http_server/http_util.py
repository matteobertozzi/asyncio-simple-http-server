#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import annotations
from collections.abc import Generator, KeysView
from dataclasses import dataclass
from http import HTTPStatus
import asyncio
import os


class HttpHeaders:
    def __init__(self) -> None:
        self._headers = {}

    def set(self, key, value):
        self._headers[key.lower()] = [value]
        return self

    def add(self, key, value):
        self._headers.setdefault(key.lower(), []).append(value)
        return self

    def get_list(self, key):
        return self._headers.get(key.lower())

    def get(self, key, default=None, transform=lambda x: x):
        v = self.get_list(key)
        return transform(v[0]) if v else default

    def merge(self, other):
        if isinstance(other, HttpHeaders):
            for k, l in other._headers.items():
                self._headers.setdefault(k, []).extend(l)
        else:
            for k, v in other.items():
                hlist = self._headers.setdefault(k, [])
                if isinstance(v, list):
                    hlist.extend(v)
                else:
                    hlist.append(v)

    def keys(self) -> KeysView:
        return self._headers.keys()

    def items(self) -> Generator[tuple[str, str]]:
        for k, l in self._headers.items():
            for v in l:
                yield k, v

    def __len__(self) -> int:
        return sum(len(l) for l in self._headers.values())

    def __getitem__(self, key):
        return self._headers[key.lower()]

    def __repr__(self) -> str:
        return repr(self._headers)


@dataclass
class HttpRequest:
    method: str
    path: str
    version: str
    headers: HttpHeaders
    body: bytes | None = None


@dataclass
class HttpResponse:
    status_code: int
    headers: HttpHeaders | None = None
    body: bytes | None = None
    file_path: str | None = None


def _clean_path(path):
    # gh-87389: The purpose of replacing '//' with '/' is to protect
    # against open redirect attacks possibly triggered if the path starts
    # with '//' because http clients treat //path as an absolute URI
    # without scheme (similar to http://path) rather than a path.
    if path.startswith('//'):
        path = '/' + path.lstrip('/')  # Reduce to a single /
    return path


async def http_parser(reader: asyncio.StreamReader, timeout=10) -> HttpRequest:
    line = await asyncio.wait_for(reader.readuntil(b'\r\n'), timeout)
    if not line:
        return None

    words = line.decode().split()

    method, path, version = (words[0], words[1], words[2])
    path = _clean_path(path)

    headers = HttpHeaders()
    while True:
        line = await asyncio.wait_for(reader.readuntil(b'\r\n'), timeout)
        if not line or line == b'\r\n':
            break

        key, value = line.decode().split(': ', 1)
        headers.add(key.strip(), value.strip())

    content_length = headers.get('content-length', -1, int)

    if content_length > 0:
        body = await asyncio.wait_for(reader.readexactly(content_length), timeout)
    else:
        body = None

    return HttpRequest(method, path, version, headers, body)


async def http_send_response(writer: asyncio.StreamWriter, request: HttpRequest, response: HttpResponse):
    http_status = HTTPStatus(response.status_code)
    headers = response.headers if response.headers else HttpHeaders()

    content_length = 0
    if response.body:
        content_length = len(response.body)
    elif response.file_path:
        content_length = os.stat(response.file_path).st_size
    headers.set('content-length', content_length)

    writer.write(f'HTTP/1.1 {http_status.value} {http_status.phrase}\r\n'.encode('utf-8'))
    for key, value in headers.items():
        writer.write(f'{key}: {value}\r\n'.encode('utf-8'))
    writer.write(b'\r\n')
    if response.body:
        writer.write(response.body)
    elif response.file_path:
        await writer.drain()
        with open(response.file_path, 'rb') as fd:
            await asyncio.get_event_loop().sendfile(writer.transport, fd, 0, fallback=True)
    await writer.drain()
