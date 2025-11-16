# Chat Application Implementation

## Overview
Complete HTTP server-based chat application with **hybrid P2P architecture** - combining centralized tracker for peer discovery with decentralized P2P messaging for direct communication.

## Features Implemented

### Authentication System
- Login page with username/password authentication
- Cookie-based session management (`auth=true`)
- Protected routes requiring authentication
- Default credentials: admin/password

### Chat Functionality
- **Channels**: Pre-configured channels (general, random, tech)
- **Messaging**: Send and receive messages in real-time
- **Create Channels**: Users can create new channels dynamically
- **Message History**: All messages stored per channel with timestamps
- **User Display**: Shows sender name and timestamp for each message

### Peer-to-Peer Tracking (Hybrid Architecture)
- **Peer Registration**: Users registered as peers on login
- **Online Users**: List of currently active users
- **Peer TTL**: Automatic cleanup of stale peers (300 seconds)
- **Connectivity Testing**: Endpoint to test peer reachability
- **Direct P2P Messaging**: Peers can communicate directly without tracker
- **Heartbeat Mechanism**: Automatic peer liveness detection (30-second interval)

### P2P Standalone Client (`apps/peer.py`)
- **Direct TCP Connections**: Peers connect directly to each other
- **P2P Message Broadcasting**: Messages sent peer-to-peer, not through server
- **Automatic Peer Discovery**: Discovers and connects to all active peers
- **Heartbeat Loop**: Maintains connections with periodic health checks
- **Interactive CLI**: Command-line interface for P2P chat

### Frontend
- **Modern UI**: Responsive design with gradient backgrounds
- **Channel Sidebar**: Easy navigation between channels
- **Users Sidebar**: See who's online
- **Message Area**: Clean message display with sender highlighting
- **Real-time Updates**: 5-second polling for new messages

## Technical Architecture

### Hybrid P2P Design

**Centralized Tracker (HTTP Server)**:
- Peer registration and discovery
- Channel management
- Web UI serving
- Initial peer list distribution

**Decentralized Messaging (P2P)**:
- Direct TCP connections between peers
- Message broadcasting without server intermediation
- Reduced server load
- Lower latency for peer-to-peer communication

### Backend (Python)
- **Framework**: WeApRous (custom Flask-like decorator routing)
- **Threading**: Daemon threads for concurrent connection handling
- **Data Storage**: In-memory dictionaries with thread locks
- **HTTP Handling**: Custom HTTP adapter with Content-Length parsing
- **P2P Protocol**: JSON over TCP with newline delimiters

### Frontend (JavaScript)
- **Vanilla JS**: No frameworks, pure JavaScript
- **Fetch API**: Modern AJAX requests
- **Session Storage**: Client-side state management
- **Polling**: Periodic updates every 5 seconds

### P2P Protocol Messages
```json
// Handshake
{"type": "handshake", "from": "peer1", "username": "Alice"}

// Message
{"type": "message", "from": "peer1", "message": "Hello World"}

// Heartbeat
{"type": "heartbeat", "from": "peer1"}

// Heartbeat Response
{"type": "heartbeat_ack", "from": "peer2"}
```

### Response Types Supported
1. **JSON**: Automatic serialization of Python dicts
2. **Custom Responses**: Status code, headers, and content control
3. **File Serving**: HTML, CSS, JavaScript file serving
4. **Binary Data**: Raw bytes support

## API Endpoints

### Authentication
- `POST /login` - Login with credentials
- `GET /login.html` - Login page
- `GET /` or `/index.html` - Main chat interface (requires auth)

### Chat API
- `GET /channels` - List all channels
- `GET /messages?channel=<name>` - Get messages for channel
- `POST /send` - Send message to channel
- `POST /create-channel` - Create new channel

### Peer Tracking
- `POST /submit-info` - Register peer information
- `GET /get-list` - Get list of active peers
- `POST /connect-peer` - Test peer connectivity
- `POST /broadcast-peer` - Broadcast message to all peers via direct TCP

### Static Files
- `GET /static/css/*` - CSS files
- `GET /static/js/*` - JavaScript files
- `GET /favicon.ico` - Favicon

## Usage

### Starting the Tracker Server
```bash
python start_sampleapp.py --server-port 9000
```

### Starting P2P Peer Clients

**Peer 1:**
```bash
python apps/peer.py --id peer1 --port 5000 --tracker-host 127.0.0.1 --tracker-port 9000 --username Alice
```

**Peer 2:**
```bash
python apps/peer.py --id peer2 --port 5001 --tracker-host 127.0.0.1 --tracker-port 9000 --username Bob
```

**Peer Commands:**
- Type message and press Enter to broadcast to all connected peers
- `/refresh` - Refresh peer list and reconnect
- `/peers` - Show currently connected peers
- `/exit` - Quit the peer client

### Accessing the Web Application
1. Open browser to `http://localhost:9000/login.html`
2. Login with username: `admin`, password: `password`
3. Start chatting in the #general channel
4. Create new channels with the "+ New Channel" button
5. Switch between channels by clicking on them

### Testing with curl
```bash
# Login
curl -c cookies.txt -X POST "http://localhost:9000/login" \
  -d "username=admin&password=password"

# Get channels
curl -b cookies.txt "http://localhost:9000/channels"

# Get messages
curl -b cookies.txt "http://localhost:9000/messages?channel=general"

# Send message
curl -b cookies.txt -X POST "http://localhost:9000/send" \
  -H "Content-Type: application/json" \
  -d '{"channel":"general","sender":"admin","text":"Hello","timestamp":1234567890}'

# Broadcast to P2P peers
curl -X POST "http://localhost:9000/broadcast-peer" \
  -H "Content-Type: application/json" \
  -d '{"sender":"admin","message":"Hello to all peers"}'
```

## P2P Testing Scenario

1. **Start Tracker Server**:
   ```bash
   python start_sampleapp.py --server-port 9000
   ```

2. **Start Multiple Peers** (in separate terminals):
   ```bash
   # Terminal 2
   python apps/peer.py --id alice --port 5000 --username Alice
   
   # Terminal 3
   python apps/peer.py --id bob --port 5001 --username Bob
   
   # Terminal 4
   python apps/peer.py --id charlie --port 5002 --username Charlie
   ```

3. **Send Messages**:
   - Type messages in any peer terminal
   - Messages are delivered directly peer-to-peer
   - All connected peers receive the message
   - No messages go through the tracker server

4. **Test Heartbeat**:
   - Peers automatically send heartbeats every 30 seconds
   - Tracker updates peer `last_seen` timestamp
   - Stale peers (>300 seconds) are automatically removed

## Security Considerations

### Educational Purpose Only
This application is designed for learning and includes intentional simplifications:
- No HTTPS/TLS encryption
- Hardcoded credentials
- No password hashing
- No CSRF protection
- No input sanitization
- In-memory storage (no persistence)
- P2P messages not encrypted

### For Production Use
Would require:
- TLS/SSL certificates for HTTP and P2P connections
- Proper password hashing (bcrypt, argon2)
- Database backend (PostgreSQL, MongoDB)
- Session management (Redis)
- Input validation and sanitization
- Rate limiting
- CSRF tokens
- End-to-end encryption for P2P messages
- WebSocket for real-time updates (instead of polling)
- DHT for decentralized peer discovery

## File Structure
```
├── start_sampleapp.py         # Main application with all routes
├── daemon/
│   ├── weaprous.py            # Routing framework
│   ├── backend.py             # TCP server with threading
│   ├── proxy.py               # Reverse proxy with round-robin
│   ├── httpadapter.py         # HTTP request/response handling
│   ├── request.py             # Request parser with query params
│   ├── response.py            # Response builder
│   └── dictionary.py          # Case-insensitive dict
├── apps/
│   └── peer.py                # P2P client implementation (NEW)
├── www/
│   ├── login.html             # Login page
│   └── index.html             # Chat interface
└── static/
    ├── css/
    │   ├── login.css          # Login page styles
    │   └── chat.css           # Chat interface styles
    └── js/
        ├── login.js           # Login form handler
        └── chat.js            # Chat client
```

## Performance Characteristics
- **Concurrent Users**: Handles multiple simultaneous connections via threading
- **Message Latency**: 
  - Web UI: 5-second polling interval
  - P2P: Near-instant (direct TCP)
- **Memory Usage**: Grows with message history (no cleanup)
- **Thread Safety**: All shared data protected by locks
- **Scalability**: P2P design reduces server load as network grows

## Known Limitations
1. **No Persistence**: All data lost on server restart
2. **Web UI Polling**: 5-second delay for web-based messages
3. **No Message Search**: Can't search message history
4. **No Private Channels**: All channels are public
5. **No File Upload**: Text messages only
6. **No Edit/Delete**: Messages are immutable once sent
7. **NAT Traversal**: P2P connections require direct IP connectivity (no NAT hole punching)
8. **No DHT**: Centralized tracker required for peer discovery

## Future Enhancements
- WebSocket support for real-time web messaging
- Database integration (SQLite/PostgreSQL)
- DHT-based peer discovery (eliminate tracker dependency)
- NAT traversal (STUN/TURN servers)
- End-to-end encryption for P2P messages
- File sharing over P2P connections
- Voice/video calling
- Message acknowledgments and delivery receipts
- Offline message queuing
- User profiles and presence status

## Credits
- Framework: WeApRous by pdnguyen @ HCMC University of Technology
- Course: CO3093/CO3094 - Computer Networks
- Implementation: Hybrid P2P chat application with direct peer messaging
