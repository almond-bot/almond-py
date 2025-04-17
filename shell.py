#!/usr/bin/env python3
import asyncio
import threading
import argparse
from almond.client import AlmondBotClient
from IPython.terminal.embed import InteractiveShellEmbed

def start_background_loop(loop: asyncio.AbstractEventLoop):
    """Run an asyncio loop in a background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

def main():
    # parser = argparse.ArgumentParser(description='AlmondBot Python Shell')
    # args = parser.parse_args()

    try:
        from IPython import embed
    except ImportError:
        print("IPython not found. Please run `uv pip install \".[dev]\"`")
        return

    # ✅ Create a shared event loop and run it in the background
    loop = asyncio.new_event_loop()
    threading.Thread(target=start_background_loop, args=(loop,), daemon=True).start()

    # Set the event loop as current for coroutines in this thread
    asyncio.set_event_loop(loop)

    client = AlmondBotClient()

    banner = """
AlmondBot Python Shell
=====================
Available variables:
- client

Example usage:
>>> await client.connect()
>>> await client.get_joint_angles()
"""

    shell = InteractiveShellEmbed(banner1=banner)
    shell(local_ns={
        'AlmondBotClient': AlmondBotClient,
        'asyncio': asyncio,
        'client': client,
    })

if __name__ == "__main__":
    main()
