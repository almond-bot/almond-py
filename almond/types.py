from enum import Enum
from collections import namedtuple

# Enum Mode
class Mode(Enum):
    DRAG = "drag"
    TELEOPERATION = "teleoperation"
    AUTONOMOUS = "autonomous"

# Pose Class
class Pose:
    def __init__(self, x: float, y: float, z: float, roll: float, pitch: float, yaw: float):
        self.x = x
        self.y = y
        self.z = z
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z, self.roll, self.pitch, self.yaw]

    @staticmethod
    def from_dict(data: dict) -> 'Pose':
        return Pose(data['x'], data['y'], data['z'], data['roll'], data['pitch'], data['yaw'])

class Status:
    def __init__(self, mode: Mode, status: str, error_message: str = None):
        self.mode = mode
        self.status = status
        self.error_message = error_message
    
    @staticmethod
    def from_dict(data: dict) -> 'Status':
        return Status(Mode(data['mode']), data['status'], data['error_message'])

class Joints:
    def __init__(self, j1: float, j2: float, j3: float, j4: float, j5: float, j6: float):
        self.j1 = j1
        self.j2 = j2
        self.j3 = j3
        self.j4 = j4
        self.j5 = j5
        self.j6 = j6

    def to_list(self) -> list[float]:
        return [self.j1, self.j2, self.j3, self.j4, self.j5, self.j6]
    
    @staticmethod
    def from_dict(data: dict) -> 'Joints':
        return Joints(data['j1'], data['j2'], data['j3'], data['j4'], data['j5'], data['j6'])

Point = namedtuple('Point', ['x', 'y'])

class AprilTag:
    def __init__(self, id: int, center: Point, corners: list[Point], offset: Pose):
        self.id = id
        self.center = center
        self.corners = corners
        self.offset = offset
    
    @staticmethod
    def from_dict(data: dict) -> 'AprilTag':
        return AprilTag(data['id'], Point(data['center']['x'], data['center']['y']), [Point(corner['x'], corner['y']) for corner in data['corners']], Pose(data['offset']['x'], data['offset']['y'], data['offset']['z'], data['offset']['roll'], data['offset']['pitch'], data['offset']['yaw']))

class TrainingEpisode:
    def __init__(self, id: str, task_name: str, duration_seconds: float, created_at: str):
        self.id = id
        self.task_name = task_name
        self.duration_seconds = duration_seconds
        self.created_at = created_at
    
    @staticmethod
    def from_dict(data: dict) -> 'TrainingEpisode':
        return TrainingEpisode(data['id'], data['task_name'], data['duration_seconds'], data['created_at'])


class AIModel(Enum):
    PI0 = "PI0"
    PI0_FAST = "PI0_FAST"
    ACT = "ACT"
    DIFFUSION = "DIFFUSION"
    TDMPC = "TDMPC"
    VQBET = "VQBET"


class TaskTraining:
    def __init__(self, id: str, task_name: str, training_name: str, model: AIModel, training_episode_count: int, status: str, created_at: str):
        self.id = id
        self.task_name = task_name
        self.training_name = training_name
        self.model = model
        self.training_episode_count = training_episode_count
        self.status = status
        self.created_at = created_at

    @staticmethod
    def from_dict(data: dict) -> 'TaskTraining':
        return TaskTraining(data['id'], data['task_name'], data['training_name'], AIModel(data['model']), data['training_episode_count'], data['created_at'])
