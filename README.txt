================================================================================
CO3093 / CO3094 – P2P Tracker and Peer System
HCMC University of Technology – bksysnet
================================================================================

This project implements:
1. A backend tracker server (WeApRous application)
2. A reverse proxy web server
3. Peer-to-peer clients that register and communicate via the tracker

Directory structure (important folders):
start_backend.py        → Runs the backend tracker
start_proxy.py          → Runs the reverse proxy (optional)
start_sampleapp.py      → Sample app & route testing
apps/peer.py            → P2P client program
www/                    → HTML UI files
static/                 → CSS and images

================================================================================
1. Running the System
================================================================================

Open three terminal windows.

Terminal 1 – Start the backend server:
python start_backend.py

Terminal 2 – Start the reverse proxy (frontend server):
python start_proxy.py

Terminal 3 – Start the sample application version:
python start_sampleapp.py

Access in browser:
http://localhost:8080/

Note: If running start_sampleapp.py directly (without proxy):
python start_sampleapp.py --server-port 9000
Access: http://localhost:9000/login.html

================================================================================
2. Web Login Authentication (Task 1A / 1B)
================================================================================

Login expects:
username = admin
password = password

Test root path (unauthenticated - should return 401):
curl -i "http://localhost:8080/"

Test login (unauthenticated request):
curl -i -X POST "http://localhost:8080/login"

Submit valid login and store cookie:
curl -i -c cookies.txt -X POST "http://localhost:8080/login" -d "username=admin&password=password"

Access home page with stored cookie:
curl -i -b cookies.txt "http://localhost:8080/"

Access index.html directly:
curl -i -b cookies.txt "http://localhost:8080/index.html"

Invalid login:
curl -i -X POST "http://localhost:8080/login" -d "username=foo&password=bar"

Expected Response: HTTP/1.1 401 Unauthorized

================================================================================
3. Tracker API Testing
================================================================================

Submit a peer:
curl -i -b cookies.txt -X POST "http://localhost:8080/submit-info" \
  -H "Content-Type: application/json" \
  -d '{"id":"peer1","ip":"127.0.0.1","port":5000,"username":"Alice"}'

Expected Response:
{"status": "ok", "id": "peer1", "peers": 1}

Get list of registered peers:
curl -i -b cookies.txt "http://localhost:8080/get-list"

Expected Response:
{"peers": [{"id": "peer1", "ip": "127.0.0.1", "port": 5000, "username": "Alice", "last_seen": 1234567890.0}]}

Test peer connectivity:
curl -i -b cookies.txt -X POST "http://localhost:8080/connect-peer" \
  -H "Content-Type: application/json" \
  -d '{"id":"peer1"}'

Expected Response (if peer is reachable):
{"status": "reachable", "peer": {...}}

Expected Response (if peer is unreachable):
{"error": "Peer unreachable"}

Broadcast message to all peers:
curl -i -X POST "http://localhost:8080/broadcast-peer" \
  -H "Content-Type: application/json" \
  -d '{"sender":"admin","message":"Hello to all peers"}'

Expected Response:
{"status": "broadcast", "total_peers": 2, "successful": 2, "failed": 0}

================================================================================
4. Chat API Testing
================================================================================

Get list of channels:
curl -i -b cookies.txt "http://localhost:8080/channels"

Expected Response:
{"channels": ["general", "random", "tech"]}

Get messages for a channel:
curl -i -b cookies.txt "http://localhost:8080/messages?channel=general"

Expected Response:
{"messages": [{"sender": "admin", "text": "Hello", "timestamp": 1234567890.0}]}

Send a message:
curl -i -b cookies.txt -X POST "http://localhost:8080/send" \
  -H "Content-Type: application/json" \
  -d '{"channel":"general","sender":"admin","text":"Hello World","timestamp":1234567890}'

Expected Response:
{"status": "sent"}

Create a new channel:
curl -i -b cookies.txt -X POST "http://localhost:8080/create-channel" \
  -H "Content-Type: application/json" \
  -d '{"channel":"newchannel"}'

Expected Response:
{"status": "created", "channel": "newchannel"}

================================================================================
5. P2P Peer Client Testing
================================================================================

The P2P peer client allows direct peer-to-peer communication without
routing messages through the tracker server.

Start Tracker Server:
Terminal 1:
python start_sampleapp.py --server-port 9000

Start Peer 1 (Alice):
Terminal 2:
python apps/peer.py --id alice --port 5000 --tracker-host 127.0.0.1 --tracker-port 9000 --username Alice

Start Peer 2 (Bob):
Terminal 3:
python apps/peer.py --id bob --port 5001 --tracker-host 127.0.0.1 --tracker-port 9000 --username Bob

Start Peer 3 (Charlie):
Terminal 4:
python apps/peer.py --id charlie --port 5002 --tracker-host 127.0.0.1 --tracker-port 9000 --username Charlie

P2P Peer Commands:
- Type any message and press Enter to broadcast to all connected peers
- /refresh - Refresh peer list and reconnect to new peers
- /peers - Show list of currently connected peers
- /exit - Quit the peer client

Testing P2P Communication:
1. Start the tracker and at least 2 peers
2. Type a message in any peer terminal
3. The message should appear in all other peer terminals
4. Messages are delivered peer-to-peer (not through tracker)

P2P Features:
- Automatic peer discovery via tracker
- Direct TCP connections between peers
- Heartbeat mechanism (30-second interval)
- Automatic reconnection on /refresh
- JSON protocol over TCP

================================================================================
6. Static File Testing
================================================================================

Access CSS files:
curl -i "http://localhost:8080/static/css/login.css"
curl -i "http://localhost:8080/static/css/chat.css"
curl -i "http://localhost:8080/static/css/styles.css"

Access JavaScript files:
curl -i "http://localhost:8080/static/js/login.js"
curl -i "http://localhost:8080/static/js/chat.js"

Expected: HTTP/1.1 200 OK with appropriate Content-Type headers

================================================================================
7. Reverse Proxy Testing (Optional)
================================================================================

The reverse proxy routes requests to backend servers based on host headers
and supports round-robin load balancing.

Configuration file: config/proxy.conf

Example configuration:
host "192.168.56.103:8080" {
    proxy_pass http://192.168.56.103:9000;
}

host "app2.local" {
    proxy_pass http://192.168.56.210:9002;
    proxy_pass http://192.168.56.220:9002;
    dist_policy round-robin
}

Start proxy:
python start_proxy.py

Test proxy forwarding:
curl -H "Host: 192.168.56.103:8080" "http://localhost:8080/"

The request will be forwarded to the backend at 192.168.56.103:9000

================================================================================
8. Multi-Threading and Concurrency Testing
================================================================================

Test concurrent connections:

Create test script (test_concurrent.sh):
#!/bin/bash
for i in {1..5}; do
  curl -b cookies.txt "http://localhost:8080/channels" &
done
wait
echo "All concurrent requests completed"

Run test:
bash test_concurrent.sh

Expected: All 5 requests should complete successfully, demonstrating
thread-safe handling of concurrent connections.

================================================================================
9. Browser Testing
================================================================================

Full UI workflow:
1. Open browser to http://localhost:8080/login.html
2. Enter username: admin, password: password
3. Click Login
4. You should be redirected to the chat interface
5. Test channel switching (click on #general, #random, #tech)
6. Send a message in the active channel
7. Create a new channel with "+ New Channel" button
8. View online users in the sidebar
9. Logout with the Logout button

================================================================================
10. Error Cases and Edge Cases
================================================================================

Test 401 Unauthorized (no cookie):
curl -i "http://localhost:8080/"
Expected: HTTP/1.1 401 Unauthorized

Test 404 Not Found (invalid route):
curl -i "http://localhost:8080/nonexistent"
Expected: HTTP/1.1 404 Not Found

Test invalid JSON:
curl -i -X POST "http://localhost:8080/send" \
  -H "Content-Type: application/json" \
  -d '{invalid json}'
Expected: Error response

Test missing required fields:
curl -i -X POST "http://localhost:8080/submit-info" \
  -H "Content-Type: application/json" \
  -d '{}'
Expected: Peer registered with empty fields (graceful handling)

Test peer TTL expiration:
- Register a peer
- Wait 5+ minutes (TTL = 300 seconds)
- Call /get-list
Expected: Stale peer should be removed from list

================================================================================
11. Performance and Load Testing
================================================================================

Test query parameter parsing:
curl -i -b cookies.txt "http://localhost:8080/messages?channel=general&limit=10"

Test long message:
curl -i -b cookies.txt -X POST "http://localhost:8080/send" \
  -H "Content-Type: application/json" \
  -d '{"channel":"general","sender":"admin","text":"'$(python -c 'print("A"*1000)')'","timestamp":1234567890}'

Test many channels:
for i in {1..10}; do
  curl -b cookies.txt -X POST "http://localhost:8080/create-channel" \
    -H "Content-Type: application/json" \
    -d "{\"channel\":\"channel$i\"}"
done

Test many messages:
for i in {1..50}; do
  curl -b cookies.txt -X POST "http://localhost:8080/send" \
    -H "Content-Type: application/json" \
    -d "{\"channel\":\"general\",\"sender\":\"admin\",\"text\":\"Message $i\",\"timestamp\":1234567890}"
done

================================================================================
12. Troubleshooting
================================================================================

Issue: "Address already in use" error
Solution: Change port or kill existing process
  lsof -ti:9000 | xargs kill -9
  or
  python start_sampleapp.py --server-port 9001

Issue: Peers can't connect to each other
Solution: Check firewall, ensure peers are on same network, verify ports are open

Issue: Login not working
Solution: Check that username=admin and password=password (case-sensitive)

Issue: Messages not appearing
Solution: Wait 5 seconds (polling interval) or refresh the page

Issue: P2P connection refused
Solution: Ensure peer is listening on the specified port, check if peer is still running

================================================================================
13. Security Notes (Educational Purpose)
================================================================================

This implementation is for EDUCATIONAL PURPOSES ONLY.

Security limitations (intentional for learning):
- No HTTPS/TLS encryption
- No password hashing (plain text)
- No CSRF protection
- No input sanitization
- No rate limiting
- Hardcoded credentials
- In-memory storage (no persistence)
- P2P messages not encrypted

For production use, you would need:
- TLS/SSL certificates
- Proper password hashing (bcrypt, argon2)
- Database backend (PostgreSQL, MongoDB)
- Input validation and sanitization
- Rate limiting and DDoS protection
- CSRF tokens
- Session management (Redis)
- End-to-end encryption for P2P

================================================================================
14. Architecture Overview
================================================================================

Hybrid P2P Design:

Centralized Tracker (HTTP Server):
- Peer registration and discovery
- Channel management
- Web UI serving
- Initial peer list distribution

Decentralized Messaging (P2P):
- Direct TCP connections between peers
- Message broadcasting without server relay
- Reduced server load
- Lower latency for peer communication

Benefits:
- Scalable: Server load doesn't increase with more messages
- Resilient: Peers can communicate even if tracker is slow
- Low Latency: Direct peer-to-peer connections
- Simple Discovery: Centralized tracker makes peer discovery easy

================================================================================
15. Course Requirements Checklist
================================================================================

CO3093/CO3094 Requirements:

[✓] HTTP/1.1 server implementation from scratch
[✓] TCP socket programming
[✓] Multi-threading for concurrent connections
[✓] Thread-safe data structures
[✓] RESTful API design
[✓] Cookie-based authentication
[✓] Request parsing (headers, body, query parameters)
[✓] Response building (JSON, HTML, CSS, JS)
[✓] Reverse proxy with load balancing
[✓] Round-robin distribution policy
[✓] P2P peer discovery
[✓] Direct peer-to-peer messaging
[✓] Heartbeat mechanism
[✓] Channel-based chat
[✓] Web UI integration
[✓] Static file serving

================================================================================
End of README.txt
================================================================================

For more details, see IMPLEMENTATION.md

Contact: bksysnet@hcmut.edu.vn
Course: CO3093/CO3094 - Computer Networks
Institution: HCMC University of Technology
