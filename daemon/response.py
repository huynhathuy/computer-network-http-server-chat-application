#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import os
import mimetypes
import json
from .dictionary import CaseInsensitiveDict

BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.

    Instances are generated from a :class:`Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    :class:`Response <Response>` object encapsulates headers, content, 
    status code, cookies, and metadata related to the request-response cycle.
    It is used to construct and serve HTTP responses in a custom web server.

    :attrs status_code (int): HTTP status code (e.g., 200, 404).
    :attrs headers (dict): dictionary of response headers.
    :attrs url (str): url of the response.
    :attrsencoding (str): encoding used for decoding response content.
    :attrs history (list): list of previous Response objects (for redirects).
    :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
    :attrs cookies (CaseInsensitiveDict): response cookies.
    :attrs elapsed (datetime.timedelta): time taken to complete the request.
    :attrs request (PreparedRequest): the original request object.

    Usage::

      >>> import Response
      >>> resp = Response()
      >>> resp.build_response(req)
      >>> resp
      <Response>
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
        "reason",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = False
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.

        "params path (str): Path to the file.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html'):
        """
        Prepares the Content-Type header and determines the base directory
        for serving the file based on its MIME type.

        :params mime_type (str): MIME type of the requested resource.

        :rtype str: Base directory path for locating the resource.

        :raises ValueError: If the MIME type is unsupported.
        """
        
        base_dir = ""

        # Processing mime_type based on main_type and sub_type
        main_type, sub_type = mime_type.split('/', 1)
        print("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
        if main_type == 'text':
            self.headers['Content-Type']='text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR+"static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR+"www/"
            elif sub_type == 'javascript':
                base_dir = BASE_DIR+"static/"
            else:
                handle_text_other(sub_type)
        elif main_type == 'image':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='image/{}'.format(sub_type)
        elif main_type == 'application':
            if sub_type == 'javascript':
                base_dir = BASE_DIR+"static/"
                self.headers['Content-Type']='application/javascript'
            elif sub_type == 'json':
                base_dir = BASE_DIR+"apps/"
                self.headers['Content-Type']='application/json'
            else:
                base_dir = BASE_DIR+"apps/"
                self.headers['Content-Type']='application/{}'.format(sub_type)
        #
        #  TODO: process other mime_type
        #        application/xml       
        #        application/zip
        #        ...
        #        text/csv
        #        text/xml
        #        ...
        #        video/mp4 
        #        video/mpeg
        #        ...
        #
        else:
            raise ValueError("Invalid MEME type: main_type={} sub_type={}".format(main_type,sub_type))

        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.

        :params path (str): relative path to the file.
        :params base_dir (str): base directory where the file is located.

        :rtype tuple: (int, bytes) representing content length and content data.
        """

        filepath = os.path.join(base_dir, path.lstrip('/'))

        print("[Response] serving the object at location {}".format(filepath))
            #
            #  TODO: implement the step of fetch the object file
            #        store in the return value of content
            #
        return len(content), content


    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the class:`Request <Request>
        and internal attributes.

        :params request (class:`Request <Request>`): incoming request object.

        :rtypes bytes: encoded HTTP response header.
        """
        reqhdr = request.headers
        rsphdr = self.headers

        #Build dynamic headers
        headers = {
                "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                "Authorization": "{}".format(reqhdr.get("Authorization", "Basic <credentials>")),
                "Cache-Control": "no-cache",
                "Content-Type": "{}".format(self.headers['Content-Type']),
                "Content-Length": "{}".format(len(self._content)),
#                "Cookie": "{}".format(reqhdr.get("Cookie", "sessionid=xyz789")), #dummy cooki
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
                "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
                "Max-Forward": "10",
                "Pragma": "no-cache",
                "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
                "Warning": "199 Miscellaneous warning",
                "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
            }

        # Header text alignment
            #
            #  TODO: implement the header building to create formated
            #        header from the provied headers
            #
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return str(fmt_header).encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """

        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')


    def build_response(self, request):
        """
        Builds a full HTTP response including headers and content based on the request.

        :params request (class:`Request <Request>`): incoming request object.

        :rtype bytes: complete HTTP response using prepared headers and content.
        """

        path = request.path

        mime_type = self.get_mime_type(path)
        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

        base_dir = ""

        #If HTML, parse and serve embedded objects
        if path.endswith('.html') or mime_type == 'text/html':
            base_dir = self.prepare_content_type(mime_type = 'text/html')
        elif mime_type == 'text/css':
            base_dir = self.prepare_content_type(mime_type = 'text/css')
        #
        # TODO: add support objects
        #
        else:
            return self.build_notfound()

        c_len, self._content = self.build_content(path, base_dir)
        self._header = self.build_response_header(request)

        return self._header + self._content
    
    def build_response_from_handler(self, request, handler_result):
        """
        Build HTTP response from route handler return value.
        
        Supports multiple return types:
        - Dict with _status/_content/_mime → Custom response
        - Dict → JSON response
        - Bytes → Binary response  
        - String (filepath) → File response
        
        :param request: Request object
        :param handler_result: Return value from route handler
        :return: Complete HTTP response bytes
        """
        
        if isinstance(handler_result, dict):
            # Check for custom response format
            if '_status' in handler_result or '_content' in handler_result:
                status_code = handler_result.get('_status', 200)
                content = handler_result.get('_content', b'')
                mime_type = handler_result.get('_mime', 'application/octet-stream')
                
                # Build status line
                status_text = {
                    200: 'OK',
                    201: 'Created',
                    400: 'Bad Request',
                    401: 'Unauthorized',
                    404: 'Not Found',
                    405: 'Method Not Allowed',
                    500: 'Internal Server Error'
                }.get(status_code, 'OK')
                
                response = "HTTP/1.1 {} {}\r\n".format(status_code, status_text)
                
                # Add custom headers
                for key, value in handler_result.items():
                    if not key.startswith('_'):
                        response += "{}: {}\r\n".format(key, value)
                
                # Add standard headers
                response += "Content-Type: {}\r\n".format(mime_type)
                response += "Content-Length: {}\r\n".format(len(content))
                response += "Connection: close\r\n"
                response += "\r\n"
                
                return response.encode('utf-8') + content
            else:
                # Regular dict → JSON response
                try:
                    json_data = json.dumps(handler_result)
                    content = json_data.encode('utf-8')
                    
                    response = "HTTP/1.1 200 OK\r\n"
                    response += "Content-Type: application/json\r\n"
                    response += "Content-Length: {}\r\n".format(len(content))
                    response += "Connection: close\r\n"
                    response += "\r\n"
                    
                    return response.encode('utf-8') + content
                except Exception as e:
                    print("[Response] Error encoding JSON: {}".format(e))
                    return self.build_error_response(500, "Internal Server Error")
        
        elif isinstance(handler_result, bytes):
            # Binary response
            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type: application/octet-stream\r\n"
            response += "Content-Length: {}\r\n".format(len(handler_result))
            response += "Connection: close\r\n"
            response += "\r\n"
            
            return response.encode('utf-8') + handler_result
        
        elif isinstance(handler_result, str):
            # File path response
            try:
                # Handler returns the path directly (e.g., "www/login.html")
                file_path = handler_result
                
                # Determine MIME type
                mime_type = self.get_mime_type(handler_result)
                
                if not os.path.exists(file_path):
                    print("[Response] File not found: {}".format(file_path))
                    return self.build_notfound()
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                response = "HTTP/1.1 200 OK\r\n"
                response += "Content-Type: {}\r\n".format(mime_type or 'application/octet-stream')
                response += "Content-Length: {}\r\n".format(len(content))
                response += "Connection: close\r\n"
                response += "\r\n"
                
                return response.encode('utf-8') + content
                
            except Exception as e:
                print("[Response] Error serving file {}: {}".format(handler_result, e))
                return self.build_error_response(500, "Internal Server Error")
        
        else:
            # Unknown type, return error
            return self.build_error_response(500, "Invalid handler return type")
    
    def build_error_response(self, status_code, message):
        """Build a simple error response"""
        content = message.encode('utf-8')
        status_text = {
            400: 'Bad Request',
            401: 'Unauthorized',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error'
        }.get(status_code, 'Error')
        
        response = "HTTP/1.1 {} {}\r\n".format(status_code, status_text)
        response += "Content-Type: text/plain\r\n"
        response += "Content-Length: {}\r\n".format(len(content))
        response += "Connection: close\r\n"
        response += "\r\n"
        
        return response.encode('utf-8') + content