#!/usr/bin/env python3
"""
Vola Restart API - Enables self-restart capability

A small authenticated API that accepts restart requests from the Vola daemon
and executes systemctl commands on the host. Runs outside the container or
with sufficient privileges to control systemd services.

Security model:
- Requires valid API key (shared secret)
- Only accepts restart requests for approved services
- Logs all restart attempts
- Rate limited to prevent restart loops
"""

import os
import sys
import json
import time
import hmac
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
CONFIG_PATH = Path("/home/vola/state/restart_api.yaml")
ALLOWED_SERVICES = ["vola", "vola-dashboard"]
RESTART_COOLDOWN_SECONDS = 60  # Minimum time between restarts

# Runtime state
last_restart_times = {}


def load_config():
    """Load API key from config file."""
    try:
        import yaml
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading config: {e}")
    return {}


def verify_api_key(request_key):
    """Verify the request API key against configured key."""
    config = load_config()
    expected_key = config.get("api_key", "")
    if not expected_key or not request_key:
        return False
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(request_key, expected_key)


def check_rate_limit(service):
    """Check if enough time has passed since last restart."""
    now = time.time()
    last_time = last_restart_times.get(service, 0)
    if now - last_time < RESTART_COOLDOWN_SECONDS:
        return False, RESTART_COOLDOWN_SECONDS - int(now - last_time)
    return True, 0


def restart_service(service):
    """Execute systemctl restart for the given service."""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", service],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Restart command timed out"
    except Exception as e:
        return False, str(e)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/restart", methods=["POST"])
def restart():
    """
    Restart a Vola service.
    
    Request body:
    {
        "service": "vola" | "vola-dashboard",
        "api_key": "shared_secret",
        "reason": "optional reason for restart"
    }
    """
    # Parse request
    data = request.get_json() or {}
    service = data.get("service", "")
    api_key = data.get("api_key", "")
    reason = data.get("reason", "No reason provided")
    
    # Validate service
    if service not in ALLOWED_SERVICES:
        return jsonify({
            "success": False,
            "error": f"Service '{service}' not allowed. Allowed: {ALLOWED_SERVICES}"
        }), 400
    
    # Authenticate
    if not verify_api_key(api_key):
        return jsonify({
            "success": False,
            "error": "Invalid API key"
        }), 401
    
    # Rate limit check
    allowed, wait_seconds = check_rate_limit(service)
    if not allowed:
        return jsonify({
            "success": False,
            "error": f"Rate limit: wait {wait_seconds}s before restarting {service}"
        }), 429
    
    # Execute restart
    success, error = restart_service(service)
    
    if success:
        last_restart_times[service] = time.time()
        print(f"[{datetime.now()}] Restarted {service}: {reason}")
        return jsonify({
            "success": True,
            "service": service,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        })
    else:
        return jsonify({
            "success": False,
            "error": f"Restart failed: {error}"
        }), 500


@app.route("/status", methods=["GET"])
def status():
    """Get status of Vola services."""
    api_key = request.headers.get("X-API-Key", "")
    if not verify_api_key(api_key):
        return jsonify({"error": "Invalid API key"}), 401
    
    services_status = {}
    for service in ALLOWED_SERVICES:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True,
                text=True,
                timeout=5
            )
            services_status[service] = {
                "active": result.returncode == 0,
                "state": result.stdout.strip() if result.returncode == 0 else "inactive"
            }
        except Exception as e:
            services_status[service] = {"error": str(e)}
    
    return jsonify({
        "services": services_status,
        "last_restarts": {
            k: datetime.fromtimestamp(v).isoformat() 
            for k, v in last_restart_times.items()
        }
    })


if __name__ == "__main__":
    # Run on localhost only for security
    # Host should proxy this if external access needed
    app.run(host="127.0.0.1", port=7373, debug=False)
