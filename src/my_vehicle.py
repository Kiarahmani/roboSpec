from highway_env.vehicle.behavior import IDMVehicle
from highway_env.road.road import Road, Route
from highway_env.utils import Vector
import random
import numpy as np



OTHER_SPEED_RANGE_LOW = 25  # [m/s]
OTHER_SPEED_RANGE_HIGH = 25  # [m/s]
OTHER_SPEED_INTERVAL = 1  # [m/s]



# Aux Functions
_other_speed_num_points = (
    int(OTHER_SPEED_RANGE_HIGH - OTHER_SPEED_RANGE_LOW) // OTHER_SPEED_INTERVAL + 1
)

_other_speeds = np.linspace(
    OTHER_SPEED_RANGE_LOW, OTHER_SPEED_RANGE_HIGH, _other_speed_num_points
)

# New Vehicle Class Definition
class MyVehicle(IDMVehicle):
    def __init__(
        self,
        road: Road,
        position: Vector,
        heading: float = 0,
        speed: float = 0,
        target_lane_index: int = None,
        target_speed: float = None,
        route: Route = None,
        enable_lane_change: bool = True,
        timer: float = None,
    ):
        speed = random.choice(
            _other_speeds
        )  # Change velocity of car in front using this variable
        target_speed = speed  # TODO: Not working yet for above 30
        super().__init__(
            road, position, heading, speed, target_lane_index, target_speed, route
        )