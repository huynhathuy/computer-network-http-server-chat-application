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
apps.sampleApp
~~~~~~~~~~~~~~~~~

This module provides a simple example application demonstrating the WeApRous
framework usage. It shows how to create routes and handle different HTTP methods.

Usage:
    from apps.sampleApp import create_sampleapp
    
    app = create_sampleapp()
    app.prepare_address('0.0.0.0', 8000)
    app.run()
"""

import sys
import os
import json

# Add parent directory to path so daemon module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daemon import WeApRous


def create_sampleapp():
    """
    Creates and configures a sample WeApRous application with basic routes.
    
    This function demonstrates:
    - Creating a WeApRous instance
    - Defining GET and POST routes
    - Handling JSON payloads
    - Returning dictionary responses (auto-converted to JSON)
    
    :return: Configured WeApRous application instance
    :rtype: WeApRous
    """
    app = WeApRous()

    @app.route("/", methods=["GET"])
    def home(headers, body):
        """Home route returning a welcome message"""
        return {"message": "Welcome to the RESTful TCP WebApp"}

    @app.route("/user", methods=["GET"])
    def get_user(headers, body):
        """Get user information"""
        return {"id": 1, "name": "Alice", "email": "alice@example.com"}

    @app.route("/echo", methods=["POST"])
    def echo(headers, body):
        """Echo back the JSON payload sent in the request"""
        try:
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            data = json.loads(body)
            return {"received": data}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"error": "Invalid JSON"}
    
    return app


if __name__ == "__main__":
    """
    Example: Run the sample application directly
    
    Start with:
        python apps/sampleApp.py
    
    Then test with:
        curl http://localhost:8000/
        curl http://localhost:8000/user
        curl -X POST http://localhost:8000/echo -H "Content-Type: application/json" -d '{"test":"data"}'
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        prog='SampleApp',
        description='Run a simple WeApRous sample application',
        epilog='Example application for WeApRous framework'
    )
    parser.add_argument(
        '--server-ip',
        type=str,
        default='0.0.0.0',
        help='IP address to bind the server. Default is 0.0.0.0'
    )
    parser.add_argument(
        '--server-port',
        type=int,
        default=8000,
        help='Port number to bind the server. Default is 8000'
    )
    
    args = parser.parse_args()
    
    # Create and configure the application
    app = create_sampleapp()
    app.prepare_address(args.server_ip, args.server_port)
    
    print(f"[SampleApp] Starting server on {args.server_ip}:{args.server_port}")
    print("[SampleApp] Available routes:")
    print("  GET  /      - Welcome message")
    print("  GET  /user  - Get user information")
    print("  POST /echo  - Echo JSON payload")
    
    # Run the application
    app.run()
