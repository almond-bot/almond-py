import asyncio
from typing import Any, Dict, List, Optional
import aiohttp

class AlmondBotClient:
    """Client for interacting with the AlmondBot WebSocket server.
    
    This client provides methods to control and query the AlmondBot robot arm
    through a WebSocket connection using JSON-RPC 2.0 protocol.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize the AlmondBot client.
        
        Args:
            host: The host address of the AlmondBot server
            port: The port number of the AlmondBot server
        """
        self.uri = f"ws://{host}:{port}/ws"
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.request_id = 0

    async def connect(self) -> None:
        """Establish a WebSocket connection to the AlmondBot server."""
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(self.uri)

    async def disconnect(self) -> None:
        """Close the WebSocket connection to the AlmondBot server."""
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self.session:
            await self.session.close()
            self.session = None

    async def _call(self, method: str, **params) -> Any:
        """Make a JSON-RPC call to the server.
        
        Args:
            method: The name of the RPC method to call
            **params: The parameters to pass to the method
            
        Returns:
            The result of the RPC call
            
        Raises:
            ConnectionError: If not connected to the server
            Exception: If the server returns an error response
        """
        if not self.ws:
            raise ConnectionError("Not connected to server")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }

        await self.ws.send_json(request)
        response = await self.ws.receive_json()

        if "error" in response:
            raise Exception(f"RPC Error: {response['error']['message']}")
        return response.get("result")

    # Robot Mode Configuration Methods
    async def set_drag_mode(self, is_enabled: bool) -> None:
        """Enable or disable drag mode on the robot arm.
        
        Args:
            is_enabled: True to enable drag mode, False to disable
        """
        await self._call("set_drag_mode", is_enabled=is_enabled)

    async def set_collision_sensitivity(self, percent: int) -> None:
        """Set the collision sensitivity of the robot arm.
        
        Args:
            percent: Sensitivity percentage (0-100)
        """
        await self._call("set_collision_sensitivity", percent=percent)

    async def set_speed(self, percent: int) -> None:
        """Set the movement speed of the robot arm.
        
        Args:
            percent: Speed percentage (0-100)
        """
        await self._call("set_speed", percent=percent)

    # Read Robot State Methods
    async def get_joint_angles(self) -> List[float]:
        """Get the current joint angles of the robot arm.
        
        Returns:
            List of joint angles in radians
        """
        return await self._call("get_joint_angles")

    async def get_tool_transform(self) -> Dict[str, Any]:
        """Get the current tool transform of the robot arm.
        
        Returns:
            Dictionary containing the tool transform matrix
        """
        return await self._call("get_tool_transform")

    # Tool Transform Control Methods
    async def set_tool_transform(self, transform: Dict[str, Any]) -> None:
        """Set the tool transform of the robot arm.
        
        Args:
            transform: Dictionary containing the tool transform matrix
        """
        await self._call("set_tool_transform", transform=transform)

    async def set_tool_transform_offset(self, transform_offset: Dict[str, Any]) -> None:
        """Set the tool transform offset of the robot arm.
        
        Args:
            transform_offset: Dictionary containing the tool transform offset matrix
        """
        await self._call("set_tool_transform_offset", transform_offset=transform_offset)

    # Gripper Control Methods
    async def open_tool(self) -> None:
        """Open the robot's gripper."""
        await self._call("open_tool")

    async def close_tool(self) -> None:
        """Close the robot's gripper."""
        await self._call("close_tool")

    async def set_tool_stroke(self, stroke: int, force: int = 0) -> None:
        """Set the gripper stroke and force.
        
        Args:
            stroke: Stroke value (0-100)
            force: Force value (0-100)
        """
        await self._call("set_tool_stroke", stroke=stroke, force=force)

    # AprilTags Methods
    async def detect_april_tags(self) -> List[Dict[str, Any]]:
        """Detect AprilTags in the robot's field of view.
        
        Returns:
            List of dictionaries containing AprilTag detections
        """
        return await self._call("detect_april_tags")

    async def align_with_apriltag(self, x: float, y: float, z: float, id: int) -> None:
        """Align the robot with a specific AprilTag.
        
        Args:
            x: Target x position
            y: Target y position
            z: Target z position
            id: AprilTag ID to align with
        """
        await self._call("align_with_apriltag", x=x, y=y, z=z, id=id)

    async def move_relative_to_april_tag(self, tag_id: int, offset: Dict[str, float]) -> None:
        """Move the robot relative to a detected AprilTag.
        
        Args:
            tag_id: ID of the AprilTag to move relative to
            offset: Dictionary containing x, y, z offsets
        """
        await self._call("move_relative_to_april_tag", tag_id=tag_id, offset=offset)

    # AI Episode Methods
    async def record_episode(self, timer: float, task_name: str, control_mode: str) -> None:
        """Record a robot episode for training.
        
        Args:
            timer: Duration of the episode in seconds
            task_name: Name of the task being recorded
            control_mode: Control mode used during recording
        """
        await self._call("record_episode", timer=timer, task_name=task_name, control_mode=control_mode)

    async def replay_episode(self, task_name: str, number: int) -> None:
        """Replay a recorded episode.
        
        Args:
            task_name: Name of the task to replay
            number: Episode number to replay
        """
        await self._call("replay_episode", task_name=task_name, number=number)

    async def list_episode_metadata(self, task_name: str) -> List[Dict[str, Any]]:
        """Get metadata for recorded episodes of a task.
        
        Args:
            task_name: Name of the task
            
        Returns:
            List of episode metadata dictionaries
        """
        return await self._call("list_episode_metadata", task_name=task_name)

    async def train(self, task_name: str, model: str = '') -> None:
        """Train a model on recorded episodes.
        
        Args:
            task_name: Name of the task to train on
            model: Optional model name to use for training
        """
        await self._call("train", task_name=task_name, model=model)

    async def list_trainings(self) -> List[Dict[str, Any]]:
        """Get list of available trained models.
        
        Returns:
            List of training metadata dictionaries
        """
        return await self._call("list_trainings")

    async def run_model(self, model: str) -> None:
        """Run a trained model on the robot.
        
        Args:
            model: Name of the model to run
        """
        await self._call("run_model", model=model)

    async def verify_scene(self, question: str) -> bool:
        """Verify the current scene matches expectations.
        
        Args:
            question: Question to ask about the scene
            
        Returns:
            True if the scene matches expectations, False otherwise
        """
        return await self._call("verify_scene", question=question)

async def main():
    """Example usage of the AlmondBot client."""
    client = AlmondBotClient()
    try:
        await client.connect()
        
        # Example: Get joint angles
        angles = await client.get_joint_angles()
        print(f"Current joint angles: {angles}")
        
        # Example: Move to a position
        await client.set_tool_transform({
            "position": [0.1, 0.2, 0.3],
            "rotation": [0, 0, 0]
        })
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 