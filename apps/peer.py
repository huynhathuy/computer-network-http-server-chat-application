#!/usr/bin/env python
#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#

"""
apps.peer
~~~~~~~~~~~~~~~~~

Standalone P2P chat client that connects directly to other peers.

Features:
- Register with tracker server
- Discover other peers
- Direct TCP connections to peers
- P2P message broadcasting
- Heartbeat mechanism
"""

import socket
import threading
import json
import time
import argparse
import sys

class Peer:
    """P2P Chat Peer Client"""
    
    def __init__(self, peer_id, listen_port, tracker_host, tracker_port, username):
        self.peer_id = peer_id
        self.listen_port = listen_port
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.username = username
        
        # Peer connections: {peer_id: socket}
        self.peers = {}
        self.peers_lock = threading.Lock()
        
        # Server socket for incoming connections
        self.server_socket = None
        self.running = True
        
        # Get local IP
        self.local_ip = self.get_local_ip()
        
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def register_with_tracker(self):
        """Register this peer with the tracker server"""
        try:
            # Build HTTP POST request
            data = json.dumps({
                "id": self.peer_id,
                "ip": self.local_ip,
                "port": self.listen_port,
                "username": self.username
            })
            
            request = (
                f"POST /submit-info HTTP/1.1\r\n"
                f"Host: {self.tracker_host}:{self.tracker_port}\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(data)}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
                f"{data}"
            )
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.tracker_host, self.tracker_port))
            sock.sendall(request.encode())
            
            response = sock.recv(4096).decode()
            sock.close()
            
            if "200 OK" in response:
                print(f"[Peer] Registered with tracker as {self.peer_id}")
                return True
            else:
                print(f"[Peer] Registration failed: {response[:100]}")
                return False
        except Exception as e:
            print(f"[Peer] Error registering with tracker: {e}")
            return False
    
    def discover_peers(self):
        """Get list of peers from tracker"""
        try:
            request = (
                f"GET /get-list HTTP/1.1\r\n"
                f"Host: {self.tracker_host}:{self.tracker_port}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            )
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.tracker_host, self.tracker_port))
            sock.sendall(request.encode())
            
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            sock.close()
            
            # Parse response
            response_str = response.decode()
            if "\r\n\r\n" in response_str:
                body = response_str.split("\r\n\r\n", 1)[1]
                data = json.loads(body)
                return data.get("peers", [])
            
            return []
        except Exception as e:
            print(f"[Peer] Error discovering peers: {e}")
            return []
    
    def connect_to_peer(self, peer_info):
        """Establish TCP connection to another peer"""
        peer_id = peer_info['id']
        
        # Don't connect to self
        if peer_id == self.peer_id:
            return False
        
        # Don't reconnect if already connected
        with self.peers_lock:
            if peer_id in self.peers:
                return True
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((peer_info['ip'], peer_info['port']))
            
            # Send handshake
            handshake = json.dumps({
                "type": "handshake",
                "from": self.peer_id,
                "username": self.username
            }) + "\n"
            sock.sendall(handshake.encode())
            
            with self.peers_lock:
                self.peers[peer_id] = sock
            
            # Start receiver thread for this peer
            receiver_thread = threading.Thread(
                target=self.receive_from_peer,
                args=(peer_id, sock),
                daemon=True
            )
            receiver_thread.start()
            
            print(f"[Peer] Connected to {peer_info['username']} ({peer_id})")
            return True
            
        except Exception as e:
            print(f"[Peer] Failed to connect to {peer_id}: {e}")
            return False
    
    def receive_from_peer(self, peer_id, sock):
        """Receive messages from a connected peer"""
        buffer = ""
        try:
            while self.running:
                data = sock.recv(4096).decode()
                if not data:
                    break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self.handle_peer_message(peer_id, line)
        except Exception as e:
            print(f"[Peer] Connection to {peer_id} lost: {e}")
        finally:
            with self.peers_lock:
                if peer_id in self.peers:
                    del self.peers[peer_id]
            try:
                sock.close()
            except:
                pass
    
    def handle_peer_message(self, peer_id, message):
        """Handle incoming message from peer"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "handshake":
                print(f"[Peer] Handshake from {data.get('username')} ({data.get('from')})")
            
            elif msg_type == "message":
                sender = data.get("from")
                text = data.get("message")
                print(f"\n[{sender}]: {text}")
                print("> ", end="", flush=True)
            
            elif msg_type == "heartbeat":
                # Respond to heartbeat
                response = json.dumps({"type": "heartbeat_ack", "from": self.peer_id}) + "\n"
                with self.peers_lock:
                    if peer_id in self.peers:
                        self.peers[peer_id].sendall(response.encode())
        
        except Exception as e:
            print(f"[Peer] Error handling message from {peer_id}: {e}")
    
    def broadcast_message(self, message):
        """Broadcast message to all connected peers"""
        payload = json.dumps({
            "type": "message",
            "from": self.peer_id,
            "message": message
        }) + "\n"
        
        with self.peers_lock:
            dead_peers = []
            for peer_id, sock in self.peers.items():
                try:
                    sock.sendall(payload.encode())
                except Exception as e:
                    print(f"[Peer] Failed to send to {peer_id}: {e}")
                    dead_peers.append(peer_id)
            
            # Remove dead connections
            for peer_id in dead_peers:
                del self.peers[peer_id]
    
    def send_heartbeat(self):
        """Send heartbeat to all connected peers"""
        payload = json.dumps({
            "type": "heartbeat",
            "from": self.peer_id
        }) + "\n"
        
        with self.peers_lock:
            for peer_id, sock in list(self.peers.items()):
                try:
                    sock.sendall(payload.encode())
                except:
                    pass
    
    def heartbeat_loop(self):
        """Periodic heartbeat sender"""
        while self.running:
            time.sleep(30)  # Send heartbeat every 30 seconds
            self.send_heartbeat()
            self.register_with_tracker()  # Re-register to update last_seen
    
    def accept_connections(self):
        """Accept incoming peer connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.listen_port))
        self.server_socket.listen(10)
        
        print(f"[Peer] Listening on port {self.listen_port}")
        
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                print(f"[Peer] Incoming connection from {addr}")
                
                # Start receiver thread
                receiver_thread = threading.Thread(
                    target=self.handle_incoming_connection,
                    args=(conn, addr),
                    daemon=True
                )
                receiver_thread.start()
            except Exception as e:
                if self.running:
                    print(f"[Peer] Error accepting connection: {e}")
    
    def handle_incoming_connection(self, conn, addr):
        """Handle incoming peer connection"""
        try:
            # Wait for handshake
            conn.settimeout(10)
            data = conn.recv(4096).decode()
            
            if "\n" in data:
                line = data.split("\n")[0]
                handshake = json.loads(line)
                
                if handshake.get("type") == "handshake":
                    peer_id = handshake.get("from")
                    username = handshake.get("username")
                    
                    with self.peers_lock:
                        self.peers[peer_id] = conn
                    
                    print(f"[Peer] Accepted connection from {username} ({peer_id})")
                    
                    # Handle remaining data and continue receiving
                    remaining = data.split("\n", 1)[1] if "\n" in data else ""
                    self.receive_from_peer_with_buffer(peer_id, conn, remaining)
        except Exception as e:
            print(f"[Peer] Error handling incoming connection: {e}")
            try:
                conn.close()
            except:
                pass
    
    def receive_from_peer_with_buffer(self, peer_id, sock, initial_buffer):
        """Receive messages with initial buffer"""
        buffer = initial_buffer
        try:
            while self.running:
                data = sock.recv(4096).decode()
                if not data:
                    break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self.handle_peer_message(peer_id, line)
        except Exception as e:
            print(f"[Peer] Connection to {peer_id} lost: {e}")
        finally:
            with self.peers_lock:
                if peer_id in self.peers:
                    del self.peers[peer_id]
    
    def interactive_mode(self):
        """Interactive command line interface"""
        print("\n=== P2P Chat Client ===")
        print("Commands:")
        print("  /refresh - Refresh peer list and reconnect")
        print("  /peers - Show connected peers")
        print("  /exit - Quit")
        print("  <message> - Broadcast message to all peers")
        print()
        
        while self.running:
            try:
                message = input("> ")
                
                if message == "/exit":
                    self.running = False
                    break
                
                elif message == "/refresh":
                    peers = self.discover_peers()
                    print(f"[Peer] Found {len(peers)} peers")
                    for peer in peers:
                        self.connect_to_peer(peer)
                
                elif message == "/peers":
                    with self.peers_lock:
                        print(f"[Peer] Connected to {len(self.peers)} peers:")
                        for peer_id in self.peers.keys():
                            print(f"  - {peer_id}")
                
                elif message.strip():
                    self.broadcast_message(message)
            
            except KeyboardInterrupt:
                print("\n[Peer] Shutting down...")
                self.running = False
                break
            except Exception as e:
                print(f"[Peer] Error: {e}")
    
    def run(self):
        """Start the peer client"""
        # Register with tracker
        if not self.register_with_tracker():
            print("[Peer] Failed to register with tracker")
            return
        
        # Start listener thread
        listener_thread = threading.Thread(target=self.accept_connections, daemon=True)
        listener_thread.start()
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Discover and connect to peers
        time.sleep(1)
        peers = self.discover_peers()
        print(f"[Peer] Found {len(peers)} peers in network")
        
        for peer in peers:
            self.connect_to_peer(peer)
        
        # Start interactive mode
        self.interactive_mode()
        
        # Cleanup
        print("[Peer] Shutting down...")
        if self.server_socket:
            self.server_socket.close()
        
        with self.peers_lock:
            for sock in self.peers.values():
                try:
                    sock.close()
                except:
                    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='P2P Chat Peer Client')
    parser.add_argument('--id', default=f'peer_{int(time.time())}', help='Peer ID')
    parser.add_argument('--port', type=int, default=5000, help='Listen port')
    parser.add_argument('--tracker-host', default='127.0.0.1', help='Tracker host')
    parser.add_argument('--tracker-port', type=int, default=9000, help='Tracker port')
    parser.add_argument('--username', default='Anonymous', help='Username')
    
    args = parser.parse_args()
    
    peer = Peer(
        peer_id=args.id,
        listen_port=args.port,
        tracker_host=args.tracker_host,
        tracker_port=args.tracker_port,
        username=args.username
    )
    
    peer.run()
