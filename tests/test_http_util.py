#!/usr/bin/env python3
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

from asyncio import StreamReader
import unittest
import asyncio

from asyncio_simple_http_server.http_util import http_parser


class TestHttpUtils(unittest.IsolatedAsyncioTestCase):
    async def test_http_parse(self):
        reader = StreamReader()
        reader.feed_data(b'GET /foo HTTP/1.1\r\n\r\n')
        reader.feed_eof()
        request = await http_parser(reader)
        self.assertEqual('GET', request.method)
        self.assertEqual('/foo', request.path)
        self.assertEqual(0, len(request.headers))
        self.assertEqual(None, request.body)

        reader = StreamReader()
        reader.feed_data(b'POST /foo HTTP/1.1\r\nContent-Length: 3\r\nX-Foo: 10\r\n\r\nabc')
        reader.feed_eof()
        request = await http_parser(reader)
        self.assertEqual('POST', request.method)
        self.assertEqual('/foo', request.path)
        self.assertEqual(2, len(request.headers))
        self.assertEqual({'content-length', 'x-foo'}, request.headers.keys())
        self.assertEqual(b'abc', request.body)

    async def test_http_parser_timeout(self):
        reader = StreamReader()
        reader.feed_data(b'GET /foo ')
        try:
            await http_parser(reader, 1)
            self.fail('expected timeout error')
        except TimeoutError as e:
            self.assertIsInstance(e, TimeoutError)
        except asyncio.exceptions.TimeoutError as e:
            # Python 3.10 TimeoutError is different from TimeoutError in 3.11
            self.assertIsInstance(e, asyncio.exceptions.TimeoutError)


if __name__ == '__main__':
    unittest.main()