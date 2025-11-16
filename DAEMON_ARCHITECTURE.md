# Daemon Folder Architecture Documentation

## Overview

The `daemon/` folder contains the core framework components that power the **WeApRous HTTP server framework**. Each file implements a specific layer of the HTTP server stack, working together to provide a complete web application framework built from raw Python sockets.

---

## File Descriptions & Responsibilities

### 1. backend.py - TCP Server Foundation

**Purpose**: Core TCP socket server that accepts and manages client connections.

**Key Functions**:
- `create_backend(ip, port, routes)`: Entry point to start the HTTP server
- `run_backend(ip, port, routes)`: Binds socket to IP/port and enters accept loop
- `handle_client(ip, port, conn, addr, routes)`: Spawns daemon threads for each connection

**Workflow**:
```python
# 1. Create socket and bind to port
server.bind((ip, port))
server.listen(50)

# 2. Accept connections in infinite loop
while True:
    conn, addr = server.accept()
    
    # 3. Spawn thread for each client
    client_thread = threading.Thread(
        target=handle_client,
        args=(ip, port, conn, addr, routes),
        daemon=True
    )
    client_thread.start()
```

**Used By**:
- `start_backend.py` - Launches plain backend server
- `start_sampleapp.py` - Runs chat application
- `weaprous.py` - Called by `app.run()`

**Threading Model**:
- **Daemon threads**: Automatically terminate when main thread exits
- **Concurrent handling**: Each client gets own thread, enabling multiple simultaneous connections
- **Non-blocking**: Server continues accepting new connections while handling existing ones

**Key Dependencies**:
- `httpadapter.py`: Delegates actual HTTP request processing
- `response.py`: Response utilities
- `dictionary.py`: Case-insensitive header management

---

### 2. weaprous.py - Application Router

**Purpose**: Flask-like decorator-based routing system for building RESTful applications.

**Key Class**: `WeApRous`

**Core Methods**:
- `__init__()`: Initialize empty route registry
- `route(path, methods)`: Decorator to register route handlers
- `prepare_address(ip, port)`: Configure server binding
- `run()`: Launch the backend server

**Usage Pattern**:
```python
app = WeApRous()

@app.route('/login', methods=['POST'])
def login(headers, body):
    return {"status": "ok"}

@app.route('/messages', methods=['GET'])
def get_messages(headers, body):
    return {"messages": [...]}

app.prepare_address('0.0.0.0', 9000)
app.run()
```

**Route Storage**:
```python
# Routes stored as: {(METHOD, PATH): handler_function}
routes = {
    ('POST', '/login'): login_handler,
    ('GET', '/messages'): get_messages_handler,
    ('POST', '/send'): send_message_handler
}
```

**Integration**:
- Calls `create_backend()` from `backend.py`
- Passes routes dict to HTTP adapter for request dispatching
- Provides clean, pythonic API for developers

---

### 3. httpadapter.py - Request-Response Dispatcher

**Purpose**: Bridges raw socket data to/from route handlers. Central hub for HTTP protocol handling.

**Key Class**: `HttpAdapter`

**Attributes**:
- `conn` (socket): Active client connection
- `routes` (dict): Route handler mappings
- `request` (Request): Request parser instance
- `response` (Response): Response builder instance

**Main Method**: `handle_client(conn, addr, routes)`

**Request Processing Pipeline**:
```
1. Read raw bytes from socket
   ↓
2. Parse headers until \r\n\r\n
   ↓
3. Read body based on Content-Length
   ↓
4. Call request.prepare() to parse HTTP components
   ↓
5. Match route from routes dict
   ↓
6. Invoke handler with headers and body
   ↓
7. Build response from handler return value
   ↓
8. Send via socket and close connection
```

**Handler Return Value Types**:
```python
# 1. Dict → JSON response
return {"key": "value"}
# → Content-Type: application/json

# 2. Dict with _content → Custom response
return {
    "_status": 200,
    "_content": b"...",
    "_mime": "text/html",
    "Set-Cookie": "auth=true"
}
# → Custom headers + content

# 3. Bytes → Binary response
return b"..."
# → Content-Type: application/octet-stream

# 4. String (filepath) → File response
return "www/index.html"
# → Serves file with auto-detected MIME type
```

**Key Responsibilities**:
- Socket I/O management
- HTTP request parsing coordination
- Route matching logic
- Response construction delegation
- Error handling and logging

---

### 4. request.py - HTTP Request Parser

**Purpose**: Parse raw HTTP request strings into structured objects.

**Key Class**: `Request`

**Attributes**:
- `method` (str): HTTP verb (GET, POST, etc.)
- `path` (str): URL path without query string
- `headers` (dict): HTTP headers (case-insensitive)
- `cookies` (dict): Parsed cookies
- `query_params` (dict): Parsed query parameters
- `hook` (function): Matched route handler
- `body` (bytes): Request body

**Key Methods**:
- `prepare(request, routes)`: Main parsing entry point
- `extract_request_line(request)`: Parse first line (METHOD PATH VERSION)
- `prepare_headers(request)`: Parse all headers
- `_parse_query(query_string)`: Parse URL query parameters

**Parsing Example**:
```python
req = Request()
req.prepare("GET /messages?channel=general HTTP/1.1\r\n...", routes)

# Result:
req.method = "GET"
req.path = "/messages"
req.query_params = {"channel": "general"}
req.headers = {
    "host": "localhost:9000",
    "user-agent": "curl/7.68.0",
    "path": "/messages?channel=general"  # Original path preserved
}
req.hook = <function get_messages>
```

**Query Parameter Parsing**:
```python
# URL: /search?q=hello&limit=10&offset=20
req.query_params = {
    "q": "hello",
    "limit": "10",
    "offset": "20"
}
```

**Route Matching**:
```python
# Try exact match: (METHOD, PATH)
hook = routes.get(('GET', '/messages'))

# If not found, try path-only match (backwards compatibility)
if not hook:
    hook = routes.get('/messages')
```

---

### 5. response.py - HTTP Response Builder

**Purpose**: Construct HTTP responses with proper headers and content.

**Key Class**: `Response`

**Attributes**:
- `status_code` (int): HTTP status (200, 404, etc.)
- `headers` (dict): Response headers
- `_content` (bytes): Response body
- `encoding` (str): Character encoding
- `cookies` (CaseInsensitiveDict): Response cookies

**Key Methods**:
- `build_response(request)`: Build response from static files
- `build_response_from_handler(request, handler_result)`: Build from route handler
- `get_mime_type(path)`: Detect MIME type from file extension
- `prepare_content_type(mime_type)`: Set Content-Type header
- `build_content(path, base_dir)`: Load file content
- `build_error_response(status_code, message)`: Build error responses

**MIME Type Handling**:
```python
# Maps MIME types to directory structure
'text/html'         → www/
'text/css'          → static/
'text/javascript'   → static/
'application/javascript' → static/
'image/*'           → static/
'application/json'  → apps/
```

**Response Construction**:
```python
# HTTP/1.1 Status Line
response = "HTTP/1.1 200 OK\r\n"

# Headers
response += "Content-Type: application/json\r\n"
response += "Content-Length: 123\r\n"
response += "Set-Cookie: auth=true; Path=/\r\n"
response += "Connection: close\r\n"
response += "\r\n"  # Header-body separator

# Body (bytes)
response_bytes = response.encode('utf-8') + content_bytes
```

**Handler Result Processing**:
```python
# JSON dict
{"status": "ok"} 
→ HTTP/1.1 200 OK + JSON content

# Custom response dict
{"_status": 401, "_content": b"Unauthorized", "_mime": "text/plain"}
→ HTTP/1.1 401 Unauthorized + custom content

# File path string
"www/login.html"
→ HTTP/1.1 200 OK + file content with auto-detected MIME

# Binary bytes
b"\x89PNG\r\n..."
→ HTTP/1.1 200 OK + binary content
```

---

### 6. dictionary.py - Case-Insensitive Dictionary

**Purpose**: Provide case-insensitive dictionary for HTTP headers.

**Key Class**: `CaseInsensitiveDict`

**Why Needed**:
```python
# HTTP headers are case-insensitive per RFC 2616
headers['Content-Type'] == headers['content-type']  # Should be True

# Standard dict would fail:
dict['Content-Type'] != dict['content-type']

# CaseInsensitiveDict handles this:
headers = CaseInsensitiveDict()
headers['Content-Type'] = 'application/json'
print(headers['content-type'])  # Works! → 'application/json'
```

**Usage**:
```python
from daemon.dictionary import CaseInsensitiveDict

headers = CaseInsensitiveDict()
headers['Content-Type'] = 'text/html'
headers['Set-Cookie'] = 'auth=true'

# Case-insensitive access
print(headers['content-type'])  # 'text/html'
print(headers['CONTENT-TYPE'])  # 'text/html'
print(headers['set-cookie'])    # 'auth=true'
```

**Implementation**:
- Inherits from `collections.abc.MutableMapping`
- Stores lowercase keys internally
- Preserves original key for display

---

### 7. utils.py - Utility Functions

**Purpose**: Helper functions for URL parsing and authentication extraction.

**Key Functions**:
- `get_auth_from_url(url)`: Extract username/password from URL

**Usage Example**:
```python
from daemon.utils import get_auth_from_url

# URL with embedded auth
url = "http://user:pass@example.com/path"
username, password = get_auth_from_url(url)
# Result: ("user", "pass")
```

**Note**: Currently minimal, can be extended with:
- URL encoding/decoding utilities
- Header parsing helpers
- Cookie manipulation functions
- Date/time formatting for HTTP dates

---

## Component Interaction Flow

### Startup Sequence

```
1. start_sampleapp.py
   ↓
2. app = WeApRous()
   @app.route() decorators register routes
   ↓
3. app.prepare_address('0.0.0.0', 9000)
   ↓
4. app.run()
   ↓
5. weaprous.run() → create_backend(ip, port, routes)
   ↓
6. backend.py: Create socket, bind, listen
   ↓
7. Accept loop: conn, addr = server.accept()
```

### Request Handling Sequence

```
1. Client connects → backend.handle_client() spawns thread
   ↓
2. HttpAdapter.handle_client()
   ├→ Read raw socket data
   ├→ Parse headers until \r\n\r\n
   └→ Read body based on Content-Length
   ↓
3. Request.prepare()
   ├→ extract_request_line() → method, path, version
   ├→ prepare_headers() → headers dict
   ├→ _parse_query() → query_params
   └→ Match route → hook function
   ↓
4. Invoke route handler
   handler(headers=req.headers, body=body_data)
   ↓
5. Response.build_response_from_handler()
   ├→ Detect return type (dict/bytes/string)
   ├→ Build appropriate response
   └→ Format HTTP headers + content
   ↓
6. Send response via socket
   conn.sendall(response_bytes)
   ↓
7. Close connection
   conn.close()
```

---

## Integration with P2P Peer Client (apps/peer.py)

### How peer.py Uses the Daemon Framework

The `peer.py` client is a **standalone P2P node** that:
1. **Registers with tracker** using HTTP POST requests
2. **Discovers other peers** via HTTP GET requests  
3. **Establishes direct TCP connections** to other peers
4. **Exchanges messages** using JSON-over-TCP protocol

### Peer Client Architecture

```python
class Peer:
    # Registration & Discovery (uses HTTP)
    def register_with_tracker():
        # Sends POST /submit-info to tracker server
        # Tracker runs on WeApRous framework
        
    def discover_peers():
        # Sends GET /get-list to tracker
        # Returns list of active peers
    
    # Direct P2P Communication (raw TCP)
    def connect_to_peer(peer_ip, peer_port):
        # Opens direct TCP socket to peer
        # Bypasses tracker for actual messaging
        
    def broadcast_message(message):
        # Sends message to all connected peers
        # Uses JSON protocol: {"type":"message", "from":"...", "message":"..."}
    
    # Heartbeat Mechanism
    def heartbeat_loop():
        # Periodically sends heartbeat to peers
        # Maintains connection liveness
```

### Separation of Concerns

**Tracker Server (WeApRous)**:
- Peer registration (`POST /submit-info`)
- Peer discovery (`GET /get-list`)
- Peer connectivity testing (`POST /connect-peer`)
- Web UI serving (HTML/CSS/JS)
- HTTP-based communication

**P2P Peers (peer.py)**:
- Direct TCP connections between peers
- Message broadcasting
- Heartbeat mechanism
- JSON-over-TCP protocol
- No HTTP overhead for messages

**Benefits**:
- **Scalability**: Server load doesn't increase with message volume
- **Low Latency**: Direct peer-to-peer connections
- **Resilience**: Peers can communicate even if tracker is slow
- **Simple Discovery**: Centralized tracker makes peer finding easy

---

## Thread Safety

### Threading Model

**Backend Server**:
```python
# Daemon threads for each client
client_thread = threading.Thread(
    target=handle_client,
    args=(ip, port, conn, addr, routes),
    daemon=True  # Terminates when main thread exits
)
client_thread.start()
```

**Shared Data Protection**:
```python
# In start_sampleapp.py
lock = threading.Lock()
MESSAGES = {'general': [], 'random': [], 'tech': []}
PEERS = {}

@app.route('/send', methods=['POST'])
def send_message(headers, body):
    with lock:  # Acquire lock before modifying shared data
        MESSAGES[channel].append(message)
    return {"status": "sent"}
```

**Round-Robin Load Balancing** (proxy.py):
```python
round_robin_lock = threading.Lock()

def resolve_routing_policy(hostname, routes):
    if policy == 'round-robin':
        with round_robin_lock:
            selected = proxy_map.pop(0)
            proxy_map.append(selected)
    return proxy_host, proxy_port
```

---

## Error Handling

### Socket Errors
```python
try:
    server.bind((ip, port))
    server.listen(50)
except socket.error as e:
    print("Socket error: {}".format(e))
```

### Request Parsing Errors
```python
try:
    result = req.hook(headers=req.headers, body=body_data)
except Exception as e:
    print("[HttpAdapter] Error in route handler: {}".format(e))
    response = resp.build_error_response(500, "Internal Server Error")
```

### File Not Found
```python
if not os.path.exists(file_path):
    return self.build_notfound()  # 404 response
```

---

## Extension Points

### Adding New MIME Types

**In response.py**:
```python
def prepare_content_type(self, mime_type):
    main_type, sub_type = mime_type.split('/', 1)
    
    if main_type == 'video':
        base_dir = BASE_DIR + "media/"
        self.headers['Content-Type'] = f'video/{sub_type}'
    # Add more types...
```

### Adding Authentication

**In httpadapter.py**:
```python
def handle_client(self, conn, addr, routes):
    # ... existing code ...
    
    # Check authentication
    if not self.check_auth(req.headers):
        response = resp.build_error_response(401, "Unauthorized")
        conn.sendall(response)
        conn.close()
        return
    
    # Continue with route handling...
```

### Adding Logging

**Replace print statements**:
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In handle_client():
logger.info(f"[HttpAdapter] Invoking route: {req.method} {req.path}")
logger.error(f"[HttpAdapter] Error in route handler: {e}")
```

---

## Performance Considerations

### Current Limitations

1. **Single-threaded per connection**: One thread per client (high memory with many clients)
2. **Blocking I/O**: Socket operations block the thread
3. **No connection pooling**: New socket for each request
4. **In-memory storage**: No persistent database

### Optimization Strategies

**For Production**:
```python
# 1. Use thread pool
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=100)
executor.submit(handle_client, ...)

# 2. Use async/await
import asyncio
async def handle_client_async(reader, writer):
    data = await reader.read(1024)
    # Process request...
    writer.write(response)
    await writer.drain()

# 3. Add caching
from functools import lru_cache
@lru_cache(maxsize=100)
def get_file_content(path):
    with open(path, 'rb') as f:
        return f.read()
```

---

## Testing

### Unit Testing

```python
import unittest
from daemon.request import Request
from daemon.response import Response

class TestRequest(unittest.TestCase):
    def test_parse_query_params(self):
        req = Request()
        params = req._parse_query("channel=general&limit=10")
        self.assertEqual(params['channel'], 'general')
        self.assertEqual(params['limit'], '10')

class TestResponse(unittest.TestCase):
    def test_mime_type_detection(self):
        resp = Response()
        mime = resp.get_mime_type("test.html")
        self.assertEqual(mime, 'text/html')
```

### Integration Testing

```bash
# Start server
python start_sampleapp.py --server-port 9000 &

# Test endpoints
curl -i "http://localhost:9000/login.html"
curl -i -X POST "http://localhost:9000/login" -d "username=admin&password=password"
curl -i -b cookies.txt "http://localhost:9000/channels"

# Stop server
pkill -f start_sampleapp
```

---

## Summary

The daemon folder provides a **modular, extensible HTTP server framework** with:

✅ **Clean separation of concerns**: Each file has single responsibility  
✅ **Decorator-based routing**: Flask-like developer experience  
✅ **Multi-threaded**: Handles concurrent connections  
✅ **Thread-safe**: Proper locking for shared data  
✅ **Flexible responses**: Supports JSON, files, binary, custom  
✅ **Extensible**: Easy to add new features  
✅ **Educational**: Clear code structure for learning  

**Key Innovation**: Built entirely from Python sockets without using Flask, Django, or other web frameworks - perfect for understanding HTTP protocol internals.
