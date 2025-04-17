#!/usr/bin/env python3
import asyncio
import argparse
import json
from typing import Optional
from .client import AlmondBotClient

async def run_command(client: AlmondBotClient, args: argparse.Namespace) -> None:
    """Execute the requested command using the client."""
    try:
        if args.command == "connect":
            await client.connect()
            print("Connected successfully")
            
        elif args.command == "disconnect":
            await client.disconnect()
            print("Disconnected successfully")
            
        elif args.command == "set_drag_mode":
            await client.set_drag_mode(args.enabled)
            print(f"Drag mode {'enabled' if args.enabled else 'disabled'}")
            
        elif args.command == "set_speed":
            await client.set_speed(args.percent)
            print(f"Speed set to {args.percent}%")
            
        elif args.command == "get_joint_angles":
            angles = await client.get_joint_angles()
            print("Joint angles:", angles)
            
        elif args.command == "get_tool_transform":
            transform = await client.get_tool_transform()
            print("Tool transform:", json.dumps(transform, indent=2))
            
        elif args.command == "open_tool":
            await client.open_tool()
            print("Tool opened")
            
        elif args.command == "close_tool":
            await client.close_tool()
            print("Tool closed")
            
        elif args.command == "set_tool_stroke":
            await client.set_tool_stroke(args.stroke, args.force)
            print(f"Tool stroke set to {args.stroke} with force {args.force}")
            
        elif args.command == "detect_april_tags":
            tags = await client.detect_april_tags()
            print("Detected AprilTags:", json.dumps(tags, indent=2))
            
        elif args.command == "align_with_apriltag":
            await client.align_with_apriltag(args.x, args.y, args.z, args.id)
            print(f"Aligned with AprilTag {args.id} at position ({args.x}, {args.y}, {args.z})")
            
        elif args.command == "record_episode":
            await client.record_episode(args.timer, args.task_name, args.control_mode)
            print(f"Recording episode for task '{args.task_name}' for {args.timer} seconds")
            
        elif args.command == "replay_episode":
            await client.replay_episode(args.task_name, args.number)
            print(f"Replaying episode {args.number} of task '{args.task_name}'")
            
        elif args.command == "list_episodes":
            episodes = await client.list_episode_metadata(args.task_name)
            print(f"Episodes for task '{args.task_name}':", json.dumps(episodes, indent=2))
            
        elif args.command == "train":
            await client.train(args.task_name, args.model)
            print(f"Training model '{args.model}' on task '{args.task_name}'")
            
        elif args.command == "list_trainings":
            trainings = await client.list_trainings()
            print("Available trainings:", json.dumps(trainings, indent=2))
            
        elif args.command == "run_model":
            await client.run_model(args.model)
            print(f"Running model '{args.model}'")
            
        elif args.command == "verify_scene":
            result = await client.verify_scene(args.question)
            print(f"Scene verification result: {result}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="AlmondBot Command Line Interface")
    parser.add_argument("--host", default="localhost", help="Server host address")
    parser.add_argument("--port", type=int, default=8000, help="Server port number")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Connection commands
    subparsers.add_parser("connect", help="Connect to the server")
    subparsers.add_parser("disconnect", help="Disconnect from the server")
    
    # Robot control commands
    drag_parser = subparsers.add_parser("set_drag_mode", help="Enable/disable drag mode")
    drag_parser.add_argument("--enabled", type=bool, required=True, help="Enable drag mode")
    
    speed_parser = subparsers.add_parser("set_speed", help="Set robot speed")
    speed_parser.add_argument("--percent", type=int, required=True, help="Speed percentage (0-100)")
    
    subparsers.add_parser("get_joint_angles", help="Get current joint angles")
    subparsers.add_parser("get_tool_transform", help="Get current tool transform")
    
    subparsers.add_parser("open_tool", help="Open the gripper")
    subparsers.add_parser("close_tool", help="Close the gripper")
    
    stroke_parser = subparsers.add_parser("set_tool_stroke", help="Set tool stroke and force")
    stroke_parser.add_argument("--stroke", type=int, required=True, help="Stroke value (0-100)")
    stroke_parser.add_argument("--force", type=int, default=0, help="Force value (0-100)")
    
    # AprilTag commands
    subparsers.add_parser("detect_april_tags", help="Detect AprilTags")
    
    align_parser = subparsers.add_parser("align_with_apriltag", help="Align with AprilTag")
    align_parser.add_argument("--x", type=float, required=True, help="Target x position")
    align_parser.add_argument("--y", type=float, required=True, help="Target y position")
    align_parser.add_argument("--z", type=float, required=True, help="Target z position")
    align_parser.add_argument("--id", type=int, required=True, help="AprilTag ID")
    
    # Episode and training commands
    record_parser = subparsers.add_parser("record_episode", help="Record an episode")
    record_parser.add_argument("--timer", type=float, required=True, help="Duration in seconds")
    record_parser.add_argument("--task_name", required=True, help="Task name")
    record_parser.add_argument("--control_mode", required=True, help="Control mode")
    
    replay_parser = subparsers.add_parser("replay_episode", help="Replay an episode")
    replay_parser.add_argument("--task_name", required=True, help="Task name")
    replay_parser.add_argument("--number", type=int, required=True, help="Episode number")
    
    list_episodes_parser = subparsers.add_parser("list_episodes", help="List episodes")
    list_episodes_parser.add_argument("--task_name", required=True, help="Task name")
    
    train_parser = subparsers.add_parser("train", help="Train a model")
    train_parser.add_argument("--task_name", required=True, help="Task name")
    train_parser.add_argument("--model", default="", help="Model name")
    
    subparsers.add_parser("list_trainings", help="List available trainings")
    
    run_model_parser = subparsers.add_parser("run_model", help="Run a model")
    run_model_parser.add_argument("--model", required=True, help="Model name")
    
    verify_parser = subparsers.add_parser("verify_scene", help="Verify scene")
    verify_parser.add_argument("--question", required=True, help="Verification question")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = AlmondBotClient(host=args.host, port=args.port)
    asyncio.run(run_command(client, args))

if __name__ == "__main__":
    main() 