from typing import Any, Dict, List, Optional
from almond.types import Mode, Pose, Status, Joints, AprilTag, TrainingEpisode, AIModel, TaskTraining
import aiohttp
from aiohttp import WSMsgType, ClientConnectionError
import logging


logger = logging.getLogger(__name__)

class AlmondBotClient:
    """Client for interacting with the AlmondBot WebSocket server.
    
    This client provides methods to control and query the AlmondBot robot arm
    through a WebSocket connection using JSON-RPC 2.0 protocol.
    """
    
    def __init__(self, host: str = "almond-bot.local", port: int = 8000):
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

    async def set_mode(self, mode: Mode) -> None:
        """Set the mode of Almond Bot.
        
        Args:
            mode: The mode to set
        """
        await self._call("set_mode", mode=mode)
    

    async def set_collision_sensitivity(self, percent: int) -> None:
        """Set the collision sensitivity of Almond Bot.
        
        Args:
            percent: Sensitivity percentage (0-100)
        """
        await self._call("set_collision_sensitivity", percent=percent)

    async def set_speed(self, percent: int) -> None:
        """Set the movement speed of Almond Bot.
        
        Args:
            percent: Speed percentage (0-100)
        """
        await self._call("set_speed", percent=percent)

    # End of Robot Mode Configuration Methods

    # Read Robot State Methods

    async def get_status(self) -> Status:
        """Get the current status of Almond Bot.
        
        Returns:
            Status object containing the current status
        """
        return Status.from_dict(await self._call("get_status"))

    async def get_joint_angles(self) -> Joints:
        """Get the current joint angles of Almond Bot.
        
        Returns:
            Joints object containing the joint angles
        """
        return Joints.from_dict(await self._call("get_joint_angles"))

    async def get_tool_pose(self) -> Pose:
        """Get the current tool pose of Almond Bot.
        
        Returns:
            Pose object containing the tool pose
        """
        return Pose.from_dict(await self._call("get_tool_pose"))
    
    async def stream_joint_angles(self, frequency: int, joint_angles: Joints, tool_stroke: int = None, tool_force: int = None) -> None:
        """Stream joint angles to Almond Bot.

        Args:
            frequency: The frequency of the joint angles stream in Hz
            joint_angles: Joints object containing the joint angles
            tool_stroke: The tool stroke as a percentage of the maximum stroke (0-100)
            tool_force: The tool force as a percentage of the maximum force (0-100)
        """
        await self._call("stream_joint_angles", frequency=frequency, joint_angles=joint_angles.to_list(), tool_stroke=tool_stroke, tool_force=tool_force)
    # Tool Control Methods
    async def set_tool_pose(self, pose: Pose, is_offset: bool = False) -> None:
        """Set the tool pose of Almond Bot.
        
        Args:
            pose: Pose object containing the tool pose
            is_offset: If True, the pose is an offset from the current tool pose. If False, the pose is the absolute tool pose.
        """
        await self._call("set_tool_pose", pose=pose.to_list(), is_offset=is_offset)
    
    
    async def set_joint_angles(self, angles: Joints, is_offset: bool = False) -> None:
        """Set the joint angles of Almond Bot.
        
        Args:
            angles: Joints object containing the joint angles.
            is_offset: If True, the angles are an offset from the current joint angles. If False, the angles are the absolute joint angles.
        """
        await self._call("set_joint_angles", angles=angles.to_list(), is_offset=is_offset)

    async def move_arc(self, radius: float, pose: Pose, is_offset: bool = False) -> None:
        """Move Almond Bot in an arc.
        
        Args:
            radius: The radius of the arc in mm
            pose: Pose object containing the tool pose
            is_offset: If True, the pose is an offset from the current tool pose. If False, the pose is the absolute tool pose.
        """
        await self._call("move_arc", radius=radius, pose=pose.to_list(), is_offset=is_offset)

    # Gripper Control Methods
    async def open_tool(self) -> None:
        """Open Almond Bot's gripper."""
        await self._call("open_tool")

    async def close_tool(self) -> None:
        """Close Almond Bot's gripper."""
        await self._call("close_tool")

    async def set_tool_stroke(self, stroke: int, force: int = 0) -> None:
        """Set the gripper stroke and force.
        
        Args:
            stroke: Stroke value (0-100)
            force: Force value (0-100)
        """
        await self._call("set_tool_stroke", stroke=stroke, force=force)

    # AprilTags Methods
    async def detect_april_tags(self) -> List[AprilTag]:
        """Detect AprilTags in Almond Bot's field of view.
        
        Returns:
            List of AprilTag objects containing the detected AprilTags
        """
        return [AprilTag.from_dict(tag) for tag in await self._call("detect_april_tags")]

    async def align_with_apriltag(self, id: int, pose_offset: Pose = None) -> None:
        """Align Almond Bot with a specific AprilTag. If pose_offset is not provided, Almond Bot will center on the AprilTag.
        
        Args:
            id: AprilTag ID to align with
            pose_offset: Pose object containing the target pose offset
        """
        await self._call("align_with_apriltag", id=id, pose_offset=pose_offset.to_list() if pose_offset else None)

    # AI Methods
    async def record_episode(self, task_name: str, duration_seconds: float) -> TrainingEpisode:
        """Record a robot episode for training.
        
        Args:
            task_name: Name of the task being recorded
            duration_seconds: Duration of the episode in seconds

        Returns:
            TrainingEpisode object containing the recorded episode
        """
        return TrainingEpisode.from_dict(await self._call("record_episode", task_name=task_name, duration_seconds=duration_seconds))

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

    async def train_task(self, task_name: str, training_name: str, model: AIModel = AIModel.PI0) -> None:
        """Train a model on recorded episodes.
        
        Args:
            task_name: Name of the task to train on
            training_name: Name to give the training
            model: Optional model name to use for training
        """
        await self._call("train", task_name=task_name, training_name=training_name, model=model)

    async def list_trainings(self, task_name: str = None) -> List[TaskTraining]:
        """Get list of available trained models.

        Args:
            task_name: Name of the task to filter by. If not provided, all trained models will be returned.
        
        Returns:
            List of TaskTraining objects containing the trained models
        """
        return [TaskTraining.from_dict(training) for training in await self._call("list_trainings", task_name=task_name)]

    async def run_task(self, task_name: str, training_name: str = '') -> None:
        """Run a trained model on Almond Bot.
        
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

    async def detect_poses(self, object_name: str) -> List[Pose]:
        """Detect poses in Almond Bot's field of view.
        
        Args:
            object_name: Name of the object to detect
        """
        return [Pose.from_dict(pose) for pose in await self._call("detect_poses", object_name=object_name)]