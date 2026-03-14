#!/usr/bin/env python3
"""
Test runner for all NosVers agents.
Validates imports and initialization without executing real actions.
"""
import sys
import os
import importlib.util
from datetime import datetime

AGENTS_DIR = '/home/nosvers/agents'
LOG_FILE = '/home/nosvers/agents/test_agents.log'

results = {}

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def test_agent(filename):
    """Try to import and validate an agent file."""
    filepath = os.path.join(AGENTS_DIR, filename)
    modname = filename.replace('.py', '')

    try:
        spec = importlib.util.spec_from_file_location(modname, filepath)
        mod = importlib.util.module_from_spec(spec)
        # Don't actually run __main__ block
        spec.loader.exec_module(mod)

        has_run = hasattr(mod, 'run')
        return True, f"OK — has run()={has_run}", None
    except Exception as e:
        return False, f"FAIL — {type(e).__name__}: {e}", str(e)

def main():
    log("=" * 60)
    log("NosVers Agent Test Run")
    log("=" * 60)

    # Check .env
    env_path = '/home/nosvers/.env'
    if os.path.exists(env_path):
        log(f".env exists at {env_path}")
    else:
        log(f"WARNING: .env NOT FOUND at {env_path}")

    # Check dotenv loads
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        log("dotenv: OK")
    except ImportError:
        log("ERROR: python-dotenv not installed")

    # Check requests
    try:
        import requests
        log(f"requests: OK (v{requests.__version__})")
    except ImportError:
        log("ERROR: requests not installed")

    # Check env vars
    for var in ['TELEGRAM_TOKEN', 'ANGEL_CHAT_ID', 'ANTHROPIC_API_KEY', 'WP_URL', 'WP_USER', 'WP_PASS', 'APP_URL', 'APP_TOKEN']:
        val = os.getenv(var, '')
        status = 'SET' if val else 'MISSING'
        log(f"  {var}: {status}")

    # Check directories
    for d in ['/home/nosvers/uploads', '/home/nosvers/uploads/visuels',
              '/home/nosvers/uploads/africa', '/home/nosvers/uploads/pdfs']:
        exists = os.path.isdir(d)
        if not exists:
            os.makedirs(d, exist_ok=True)
            log(f"  DIR {d}: CREATED")
        else:
            log(f"  DIR {d}: OK")

    log("-" * 60)

    # Test each agent
    agents = sorted([f for f in os.listdir(AGENTS_DIR) if f.endswith('.py') and f != 'test_agents.py'])

    for agent_file in agents:
        ok, msg, error = test_agent(agent_file)
        status = "PASS" if ok else "FAIL"
        log(f"  {agent_file}: {status} — {msg}")
        results[agent_file] = (ok, msg)

    log("-" * 60)
    passed = sum(1 for ok, _ in results.values() if ok)
    total = len(results)
    log(f"Results: {passed}/{total} agents passed")
    log("=" * 60)

if __name__ == '__main__':
    main()
