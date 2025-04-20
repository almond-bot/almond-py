#!/usr/bin/env python3
import asyncio
import sys
import termios
import tty
from pynput import keyboard as pkb
from almond.client import AlmondBotClient

# Configuration
TRANSLATION_DELTA = 1.0  # mm per frame
ROTATION_DELTA = 0.5    # degrees per frame
UPDATE_HZ = 100
UPDATE_INTERVAL = 1.0 / UPDATE_HZ

TRANSLATION_KEYS = {
    'w': (1, -1),  # up
    's': (1, 1), # down
    'a': (0, -1), # left
    'd': (0, 1),  # right
    'e': (2, -1),  # backward
    'q': (2, 1)  # forward
}

ROTATION_KEYS = {
    'j': (1, -1),  # rotate left
    'l': (1, 1), # rotate right
    'i': (0, 1),  # tilt up
    'k': (0, -1), # tilt down
    'u': (2, -1),  # turn clockwise
    'o': (2, 1)  # turn counterclockwise
}

TOOL_STROKE_KEYS = {
    'v': 10,  # open tool
    'b': -10  # close tool
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
        if key == pkb.Key.space:
            pressed_keys.add(key)
        else:
            pressed_keys.add(key.char)
    except AttributeError:
        pass


def on_release(key):
    try:
        if key == pkb.Key.space:
            pressed_keys.discard(key)
        else:
            pressed_keys.discard(key.char)
    except AttributeError:
        pass
    if key == pkb.Key.esc:
        return False

async def keyboard_control_loop(client: AlmondBotClient):
    print("\n[Keyboard control ENABLED — press ESC to stop]")
    print("\nTranslation (mm/frame):")
    print("  w/s : up / down")
    print("  a/d : left / right")
    print("  q/e :  forward / backward")
    print("\nRotation (deg/frame):")
    print("  j/l : rotate left / rotate right")
    print("  i/k : tilt up / tilt down")
    print("  u/o : turn clockwise / turn counterclockwise\n")
    print("\bTool Stroke:")
    print("  v/b : open / close")
    print("  space : toggle tool stroke")
    tool_stroke = 0
    previous_tool_stroke = 0

    last_toggle_time = 0
    debounce_interval = 1.0  # 1 second debounce interval

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

            # Check for "v" and "b" keys to adjust tool stroke with debounce
            for key, direction in TOOL_STROKE_KEYS.items():
                if key in pressed_keys:
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_toggle_time > debounce_interval:
                        tool_stroke += direction
                        last_toggle_time = current_time

            # Check for "space" key to toggle tool stroke + debounce to prevent rapid toggling
            current_time = asyncio.get_event_loop().time()
            if pkb.Key.space in pressed_keys and current_time - last_toggle_time > debounce_interval:
                tool_stroke = 100 if tool_stroke == 0 else 0
                last_toggle_time = current_time

            # Ensure tool stroke is within the range [0, 100]
            tool_stroke = max(0, min(tool_stroke, 100))

            # Determine if tool stroke should be sent
            tool_stroke_to_send = tool_stroke if tool_stroke != previous_tool_stroke else None

            if any(pose_delta) or tool_stroke_to_send is not None:
                try:
                    await client.teleop(pose_offset=pose_delta, tool_stroke=tool_stroke_to_send)
                    previous_tool_stroke = tool_stroke
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
