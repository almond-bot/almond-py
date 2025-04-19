#!/usr/bin/env python3
import asyncio
import sys
import termios
import tty
from pynput import keyboard as pkb
from almond.client import AlmondBotClient

# Configuration
TRANSLATION_DELTA = 1.0  # mm per frame
ROTATION_DELTA = 1.0     # degrees per frame
UPDATE_HZ = 50
UPDATE_INTERVAL = 1.0 / UPDATE_HZ

TRANSLATION_KEYS = {
    'w': (1, 1),  # forward
    's': (1, -1), # backward
    'a': (0, -1), # left
    'd': (0, 1),  # right
    'e': (2, 1),  # up
    'q': (2, -1)  # down
}

ROTATION_KEYS = {
    'j': (0, 1),  # rotate left
    'l': (0, -1), # rotate right
    'i': (1, 1),  # tilt up
    'k': (1, -1), # tilt down
    'u': (2, 1),  # turn clockwise
    'o': (2, -1)  # turn counterclockwise
}

pressed_keys = set()
original_term_settings = None


def suppress_terminal_input():
    global original_term_settings
    fd = sys.stdin.fileno()
    original_term_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)


def restore_terminal_input():
    if original_term_settings:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, original_term_settings)


def on_press(key):
    try:
        pressed_keys.add(key.char)
    except AttributeError:
        pass


def on_release(key):
    try:
        pressed_keys.discard(key.char)
    except AttributeError:
        pass
    if key == pkb.Key.esc:
        return False


async def keyboard_control_loop(client: AlmondBotClient):
    print("\n[Keyboard control ENABLED — press ESC to stop]")
    print("\nTranslation (mm/frame):")
    print("  w/s : forward / backward")
    print("  a/d : left / right")
    print("  q/e : down / up")
    print("\nRotation (deg/frame):")
    print("  j/l : rotate left / rotate right")
    print("  i/k : tilt up / tilt down")
    print("  u/o : turn clockwise / turn counterclockwise\n")

    suppress_terminal_input()

    with pkb.Listener(on_press=on_press, on_release=on_release) as listener:
        while listener.running:
            pose_delta = [0, 0, 0, 0, 0, 0]

            for key, (idx, direction) in TRANSLATION_KEYS.items():
                if key in pressed_keys:
                    pose_delta[idx] += direction * TRANSLATION_DELTA

            for key, (idx, direction) in ROTATION_KEYS.items():
                if key in pressed_keys:
                    pose_delta[idx + 3] += direction * ROTATION_DELTA

            if any(pose_delta):
                try:
                    if not client.ws or client.ws.closed:
                        print("WebSocket connection is closed. Attempting to reconnect...")
                        await client.connect()
                    await client.set_tool_pose_offset(pose_delta)
                except Exception as e:
                    print(f"[Keyboard Control Error] {e}")

            await asyncio.sleep(UPDATE_INTERVAL)

    restore_terminal_input()
    print("\n[Keyboard control DISABLED]")


async def main():
    client = AlmondBotClient()
    await client.connect()
    try:
        await keyboard_control_loop(client)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
