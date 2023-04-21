## asyncio simple HTTP Server

This package contains a really Simple Http API Server using asyncio.
**It is not meant to be used in production**. It is more a lightweight alternative to SimpleHTTPServer but for writing HTTP APIs.

### Install the package
You can find the package at https://pypi.org/project/asyncio-simple-http-server. and install it using pip. (Python >=3.8 is required)
```bash
$ pip install asyncio-simple-http-server
```

### Usage Example
To start the server is the usual straightforward asyncio server code,
plus some registration for your HTTP API handlers.

```python
from asyncio_simple_http_server import HttpServer
import asyncio

async def main():
    # Create an instance of the HTTP Server
    http_server = HttpServer()

    # Register one or more handlers
    # The handlers are classes containing your APIs
    # See below for an example and more information.
    http_server.add_handler(MyHandler())

    # If you need to enable CORS to call the APIs
    # from a web console that you are building (e.g. angular, react, ...)
    # just add the following line,
    # to add the required header to all the responses.
    http_server.add_default_response_headers({
        'Access-Control-Allow-Origin': '*'
    })

    # start the server and serve/wait forever
    await http_server.start('127.0.0.1', 8888)
    await http_server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
```

An handler is a simple class where some methods can be exposed as an HTTP API, using a simple annotation. It also tries to simplify things for REST by converting the request body from json to a dict and the response object to json using the json.loads() and json.dumps() methods.
```python
from asyncio_simple_http_server import uri_mapping

class MyHandler:
    # The @uri_mapping decorator exposes this method as an HTTP API
    # so you can just do a HTTP GET /test-get
    # and you'll get back a 200 OK with a json body of {a: 10}
    # return values will be converted with json.dumps()
    @uri_mapping('/test-get')
    def test_get(self):
        return {'a': 10}

    # In this case the mapping says that we want a POST method
    # and by passing an argument named 'body' we will get the
    # body passed to the endpoint parsed with json.loads()
    # We execute "some logic" and we return the body
    @uri_mapping('/test-post', method='POST')
    def test_post(self, body):
      foo = body.get('foo')
      print('foo:', foo)
      return body
```

### Special Parameter Names
To receive the data of the HTTP request we use special parameter names, so if name a variable:
 * **request**: will contains an HttpRequest object, which is the full request (method, path, header, body).
 * **headers**: will contains an HttpHeaders object, which is a map of header name to values (a key can have multiple values).
 * **raw_body**: will contains the raw body as bytes.
 * **body**: will contains the body converted from json using json.loads().
 * **uri_variables**: will contains a dict of the variable specified in the @uri_variable_mapping and extracted from the path.

### Custom HTTP responses (status code, headers, ...)
You can return an HttpResponse object to customize the response with your status code, headers and body encoding. You can also send a file by specifying the file path instead of the body.
```python
from asyncio_simple_http_server import uri_mapping, HttpResponse, HttpHeaders

class MyHandler:
    # You can return an HttpResponse object to set
    # custom status code, headers and body
    @uri_mapping('/test-custom-response')
    def test_custom_resp(self) -> HttpResponse:
        headers = HttpHeaders()
        headers.set('X-Foo', 'custom stuff')
        return HttpResponse(200, headers, b'test-body')

    # With an HttpResponse object
    # you can also send a file that is on disk
    @uri_pattern_mapping('/send-my-file')
    def test_file(self) -> HttpResponse:
        return HttpResponse(200, file_path='/path/of/my-file')
```

## Routes with patterns
Sometimes static routes are not enough. and you want a dynamic pattern.
You can use @uri_variable_mapping and @uri_pattern_mapping to do exactly that.
```python
from asyncio_simple_http_server import HttpRequest, uri_variable_mapping, uri_pattern_mapping

class MyHandler:
    # You can also map routes with variables
    # for example you can call this one with /aaa/FOO/ccc/BAR
    # and you'll get {'bbb': 'FOO', 'ddd', 'BAR'} as uri_variables
    @uri_variable_mapping('/aaa/{bbb}/ccc/{ddd}')
    def test_due(self, uri_variables: dict):
        return uri_variables

    # Or you can use regex patterns to match what you want
    # for example here you can call it as /any/FOO/BAR or /any/ZOO
    @uri_pattern_mapping('/any/(.*)')
    def test_pattern(self, request: HttpRequest):
        return request.path
```

## Oh, It uses asyncio
Oh yeah, I almost forgot. This server uses asyncio,
so your function can be async too. just add async to the method and use all the awaits that you want.
```python
class MyHandler:
    @uri_mapping('/async-sleep')
    async def test_async_sleep(self):
        await asyncio.sleep(4)
```