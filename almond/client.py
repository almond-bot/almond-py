from typing import Any, Dict, List, Optional
import aiohttp
from aiohttp import WSMsgType, ClientConnectionError
import logging


logger = logging.getLogger(__name__)

class AlmondBotClient:
    """Client for interacting with the AlmondBot WebSocket server.
    
    This client provides methods to control and query the AlmondBot robot arm
    through a WebSocket connection using JSON-RPC 2.0 protocol.
    """
    
    def __init__(self, host: str = "almond-jetson.local", port: int = 8000):
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
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None)) # keep connection alive
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
            Exception: If the server returns an error response
        """
        if not self.ws or self.ws.closed:
            logger.warning("WebSocket connection is closed. Attempting to connect...")
            await self.connect()

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }

        try:
            await self.ws.send_json(request)
            msg = await self.ws.receive()
            if msg.type == WSMsgType.TEXT:
                response = msg.json()
            elif msg.type == WSMsgType.CLOSE or msg.type == WSMsgType.CLOSING:
                logger.warning("WebSocket connection closed on send. Trying again.")
                await self.connect()
                return await self._call(method, **params)
            else:
                raise ClientConnectionError(f"Unexpected WebSocket message type: {msg.type}")

        except Exception as e:
            print(f"Error sending request: {e}")
            raise e

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

    # End of Robot Mode Configuration Methods

    # Read Robot State Methods
    async def get_joint_angles(self) -> List[float]:
        """Get the current joint angles of the robot arm.
        
        Returns:
            List of joint angles in radians
        """
        return await self._call("get_joint_angles")

    async def get_tool_pose(self) -> Dict[str, Any]:
        """Get the current tool pose of the robot arm.
        
        Returns:
            Dictionary containing the tool pose
        """
        return await self._call("get_tool_pose")

    # Tool Control Methods
    async def set_tool_pose(self, pose: List[float]) -> None:
        """Set the tool pose of the robot arm.
        
        Args:
            pose: List of floats containing the tool pose. x, y, z, roll, pitch, yaw
        """
        await self._call("set_tool_pose", pose=pose)

    async def set_tool_pose_offset(self, pose_offset: List[float]) -> None:
        """Set the tool pose offset of the robot arm.
        
        Args:
            pose_offset: List of floats containing the tool pose offset. x, y, z, roll, pitch, yaw
        """
        await self._call("set_tool_pose_offset", pose_offset=pose_offset)
    
    
    async def set_joint_angles(self, angles: List[float]) -> None:
        """Set the joint angles of the robot arm.
        
        Args:
            angles: List of floats containing the joint angles.
        """
        await self._call("set_joint_angles", angles=angles)

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

    async def align_with_apriltag(self, id: int, x_offset: float = 0, y_offset: float = 0, z_offset: float = 0) -> None:
        """Align the robot with a specific AprilTag. If x, y, z are not provided, the robot will center on the AprilTag.
        
        Args:
            id: AprilTag ID to align with
            x_offset: Target x position offset, mm
            y_offset: Target y position offset, mm
            z_offset: Target z position offset, mm
        """
        await self._call("align_with_apriltag", x_offset=x_offset, y_offset=y_offset, z_offset=z_offset, id=id)

    async def move_relative_to_april_tag(self, tag_id: int, offset: Dict[str, float]) -> None:
        """Move the robot relative to a detected AprilTag.
        
        Args:
            tag_id: ID of the AprilTag to move relative to
            offset: Dictionary containing x, y, z, roll, pitch, yaw offsets
        """
        await self._call("move_relative_to_april_tag", tag_id=tag_id, offset=offset)

    # AI Methods
    async def record_episode(self, task_name: str, duration_seconds: float, control_mode: str) -> None:
        """Record a robot episode for training.
        
        Args:
            task_name: Name of the task being recorded
            duration_seconds: Duration of the episode in seconds
            control_mode: Control mode used during recording
        """
        await self._call("record_episode", task_name=task_name, duration_seconds=duration_seconds, control_mode=control_mode)

    async def replay_episode(self, task_name: str, id: str) -> None:
        """Replay a recorded episode.
        
        Args:
            task_name: Name of the task to replay
            id: Episode id to replay
        """
        await self._call("replay_episode", task_name=task_name, id=id)
    
    async def delete_episode(self, task_name: str, id: str) -> None:
        """Delete a recorded episode.
        
        Args:
            task_name: Name of the task
            id: Episode id to delete
        """
        await self._call("delete_episode", task_name=task_name, id=id)

    async def list_episodes(self, task_name: str) -> List[Dict[str, Any]]:
        """Get metadata for recorded episodes of a task.
        
        Args:
            task_name: Name of the task
            
        Returns:
            List recorded training episodes for a task
        """
        return await self._call("list_episodes", task_name=task_name)

    async def train_task(self, task_name: str, training_name: str, model: str = '') -> None:
        """Train a model on recorded episodes.
        
        Args:
            task_name: Name of the task to train on
            training_name: Name to give the training
            model: Optional model name to use for training
        """
        await self._call("train", task_name=task_name, training_name=training_name, model=model)

    async def list_trainings(self) -> List[Dict[str, Any]]:
        """Get list of available trained models.
        
        Returns:
            List of training metadata dictionaries
        """
        return await self._call("list_trainings")

    async def run_task(self, task_name: str, training_name: str = '') -> None:
        """Run a trained model on the robot.
        
        Args:
            task_name: Name of the task to run
            training_name: Name of the training to use. If not provided, the latest training will be used.
        """
        await self._call("run_task", task_name=task_name, training_name=training_name)

    async def verify_scene(self, question: str) -> bool:
        """Verify the current scene matches expectations.
        
        Args:
            question: Question to ask about the scene
            
        Returns:
            True if the scene matches expectations, False otherwise
        """
        return await self._call("verify_scene", question=question)
