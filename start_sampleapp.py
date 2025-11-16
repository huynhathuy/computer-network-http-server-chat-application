#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a complete chat application with the WeApRous framework.

Features:
- User authentication
- Chat channels and messaging
- Peer-to-peer tracker
- Static file serving
"""

import json
import socket
import argparse
import time
import threading
from urllib.parse import parse_qs

from daemon.weaprous import WeApRous

PORT = 9000  # Default port
PEER_TTL = 300.0  # Peer time-to-live in seconds

# Global data structures
PEERS = {}       # {peer_id: {ip, port, username, last_seen}}
MESSAGES = {     # {channel: [{sender, text, timestamp}, ...]}
    'general': [],
    'random': [],
    'tech': []
}
CHANNELS = ['general', 'random', 'tech']
lock = threading.Lock()

app = WeApRous()

def check_cookie(headers):
    """Check if the auth cookie is present and valid"""
    if not isinstance(headers, dict):
        return False
    cookie = headers.get('cookie', '') or headers.get('Cookie', '')
    return 'auth=true' in cookie

def parse_form_data(body):
    """Parse URL-encoded form data"""
    try:
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        params = {}
        for pair in body.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                params[key] = value
        return params
    except:
        return {}

# Authentication Routes
@app.route('/login', methods=['POST'])
def login(headers, body):
    """Handle user login"""
    print("[SampleApp] Login request")
    data = parse_form_data(body)
    username = data.get('username', '')
    password = data.get('password', '')
    
    # Simple authentication (educational purposes only)
    if username == 'admin' and password == 'password':
        return {
            "_status": 200,
            "_content": b'{"status":"ok"}',
            "_mime": "application/json",
            "Set-Cookie": "auth=true; Path=/"
        }
    else:
        return {
            "_status": 401,
            "_content": b'{"error":"Invalid credentials"}',
            "_mime": "application/json"
        }

@app.route('/login.html', methods=['GET'])
def login_page(headers, body):
    """Serve login page"""
    return "www/login.html"

@app.route('/', methods=['GET'])
@app.route('/index.html', methods=['GET'])
def index(headers, body):
    """Serve main chat interface"""
    if not check_cookie(headers):
        return {
            "_status": 401,
            "_content": b'Unauthorized',
            "_mime": "text/plain"
        }
    return "www/index.html"

# Chat API Routes
@app.route('/channels', methods=['GET'])
def get_channels(headers, body):
    """Return list of channels"""
    if not check_cookie(headers):
        return {"error": "Unauthorized"}
    
    with lock:
        return {"channels": CHANNELS}

@app.route('/messages', methods=['GET'])
def get_messages(headers, body):
    """Get messages for a channel"""
    if not check_cookie(headers):
        return {"error": "Unauthorized"}
    
    # Extract channel from query params
    path = headers.get('path', '')
    channel = 'general'
    if '?' in path:
        query = path.split('?', 1)[1]
        params = parse_qs(query)
        if 'channel' in params:
            channel = params['channel'][0]
    
    with lock:
        msgs = MESSAGES.get(channel, [])
        return {"messages": msgs}

@app.route('/send', methods=['POST'])
def send_message(headers, body):
    """Send a message to a channel"""
    if not check_cookie(headers):
        return {"error": "Unauthorized"}
    
    try:
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        data = json.loads(body)
        
        channel = data.get('channel', 'general')
        sender = data.get('sender', 'anonymous')
        text = data.get('text', '')
        timestamp = data.get('timestamp', time.time())
        
        with lock:
            if channel not in MESSAGES:
                MESSAGES[channel] = []
            MESSAGES[channel].append({
                'sender': sender,
                'text': text,
                'timestamp': timestamp
            })
        
        return {"status": "sent"}
    except Exception as e:
        print("[SampleApp] Error in send_message: {}".format(e))
        return {"error": str(e)}

@app.route('/create-channel', methods=['POST'])
def create_channel(headers, body):
    """Create a new channel"""
    if not check_cookie(headers):
        return {"error": "Unauthorized"}
    
    try:
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        data = json.loads(body)
        channel = data.get('channel', '')
        
        with lock:
            if channel and channel not in CHANNELS:
                CHANNELS.append(channel)
                MESSAGES[channel] = []
                return {"status": "created", "channel": channel}
            else:
                return {"error": "Channel already exists or invalid name"}
    except Exception as e:
        return {"error": str(e)}

# Peer Tracker Routes
@app.route('/submit-info', methods=['POST'])
def submit_info(headers, body):
    """Register peer information"""
    try:
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        data = json.loads(body)
        
        peer_id = data.get('id', '')
        ip = data.get('ip', '')
        port = data.get('port', 0)
        username = data.get('username', '')
        
        with lock:
            PEERS[peer_id] = {
                'id': peer_id,
                'ip': ip,
                'port': port,
                'username': username,
                'last_seen': time.time()
            }
        
        print("[SampleApp] Peer registered: {}".format(peer_id))
        return {"status": "ok", "id": peer_id, "peers": len(PEERS)}
    except Exception as e:
        print("[SampleApp] Error in submit_info: {}".format(e))
        return {"error": str(e)}

@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    """Get list of active peers"""
    with lock:
        # Prune stale peers
        current_time = time.time()
        stale_peers = [pid for pid, pdata in PEERS.items() 
                      if current_time - pdata['last_seen'] > PEER_TTL]
        for pid in stale_peers:
            del PEERS[pid]
        
        # Return active peers
        peer_list = list(PEERS.values())
        return {"peers": peer_list}

@app.route('/connect-peer', methods=['POST'])
def connect_peer(headers, body):
    """Test peer connectivity"""
    try:
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        data = json.loads(body)
        
        peer_id = data.get('id', '')
        with lock:
            peer = PEERS.get(peer_id)
        
        if not peer:
            return {"error": "Peer not found"}
        
        # Test TCP connection
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.settimeout(2)
            test_sock.connect((peer['ip'], peer['port']))
            test_sock.close()
            return {"status": "reachable", "peer": peer}
        except:
            return {"error": "Peer unreachable"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers, body):
    """Broadcast message to all peers via direct TCP"""
    try:
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        data = json.loads(body)
        message = data.get('message', '')
        sender = data.get('sender', 'unknown')
        
        with lock:
            peer_list = list(PEERS.values())
        
        # Broadcast to all peers via direct TCP connection
        success_count = 0
        failed_peers = []
        
        for peer in peer_list:
            try:
                # Create JSON payload for P2P message
                payload = json.dumps({
                    "type": "message",
                    "from": sender,
                    "message": message
                }) + "\n"
                
                # Attempt direct TCP connection to peer
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((peer['ip'], peer['port']))
                sock.sendall(payload.encode())
                sock.close()
                success_count += 1
            except Exception as e:
                print(f"[Broadcast] Failed to reach peer {peer['id']}: {e}")
                failed_peers.append(peer['id'])
        
        return {
            "status": "broadcast",
            "total_peers": len(peer_list),
            "successful": success_count,
            "failed": len(failed_peers)
        }
    except Exception as e:
        return {"error": str(e)}

# Static file routes
@app.route('/static/css/login.css', methods=['GET'])
def login_css(headers, body):
    """Serve login CSS"""
    return "static/css/login.css"

@app.route('/static/css/chat.css', methods=['GET'])
def chat_css(headers, body):
    """Serve chat CSS"""
    return "static/css/chat.css"

@app.route('/static/css/styles.css', methods=['GET'])
def styles_css(headers, body):
    """Serve styles CSS"""
    return "static/css/styles.css"

@app.route('/static/js/login.js', methods=['GET'])
def login_js(headers, body):
    """Serve login JavaScript"""
    return "static/js/login.js"

@app.route('/static/js/chat.js', methods=['GET'])
def chat_js(headers, body):
    """Serve chat JavaScript"""
    return "static/js/chat.js"

@app.route('/favicon.ico', methods=['GET'])
def favicon(headers, body):
    """Return empty favicon"""
    return {
        "_status": 200,
        "_content": b'',
        "_mime": "image/x-icon"
    }

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()