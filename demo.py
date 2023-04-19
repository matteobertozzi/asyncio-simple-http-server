from asyncio_simple_http_server import HttpServer, HttpRequest, HttpResponse, HttpHeaders, uri_mapping, uri_variable_mapping, uri_pattern_mapping
import logging
import asyncio


class MyHandler:
    @uri_mapping('/foo', method=('GET', 'POST'))
    def foo(self, request: HttpRequest):
        pass

    @uri_mapping('/bar')
    def bar(self, body, headers):
        return {'a': 10}


    @uri_mapping('/test-post', method='POST')
    def test_post(self, body):
      foo = body.get('foo')
      print('foo:', foo)
      return body

    @uri_mapping('/async-sleep')
    async def test_async_sleep(self):
        await asyncio.sleep(4)

    @uri_variable_mapping('/aaa/{bbb}')
    async def test_variable(self, uri_variables):
        await asyncio.sleep(4)
        return uri_variables

    @uri_variable_mapping('/aaa/{bbb}/ccc/{ddd}')
    async def test_due(self, uri_variables: dict):
        return uri_variables

    @uri_pattern_mapping('/any/(.*)')
    def test_pattern(self, request: HttpRequest):
        return request.path

    @uri_pattern_mapping('/send-file')
    def test_file(self) -> HttpResponse:
        return HttpResponse(200, file_path='LICENSE')

    @uri_mapping('/test-custom-response')
    def test_custom_resp(self) -> HttpResponse:
        headers = HttpHeaders()
        headers.set('X-Foo', 'custom stuff')
        return HttpResponse(200, headers, b'test-body')


async def main():
    http_server = HttpServer()
    http_server.add_handler(MyHandler())
    http_server.add_default_response_headers({
        'Access-Control-Allow-Origin': '*'
    })

    await http_server.start('127.0.0.1', 8888)
    print(f'Serving on {http_server.bind_address_description()}')

    await http_server.serve_forever()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
