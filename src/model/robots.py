"""Definition of Robots capabilities"""

import json
from typing import Dict
from . import activities

# statuses
READY = "ready"
SCHEDULING = "scheduling"
WORKING = "working"


class RobotException(Exception):
    """Exceptions raised by robots"""
    pass


class Robot:
    """Manage Robot state"""

    def __init__(self) -> None:
        self.status = READY
        self.previous_activity = None
        self.current_activity = None
        self.current_activity_start_tick = None
    
    def schedule(self, activity:activities.BaseActivity, tick: int) -> None:
        if not self.status == READY:
            raise RobotException("Cannot schedule activity on busy robot")
        self.status = SCHEDULING
        self.current_activity = activity
        if self.previous_activity and not self.previous_activity.get_type() == activity.get_type():
            self.current_activity_start_tick = tick + 5  # changing activity takes 5 ticks
        else:
            self.current_activity_start_tick = tick
    
    def work(self, tick:int) -> activities.BaseActivity:
        """Make """
        if not self.current_activity:
            # raise RobotException("Robot has no scheduled activity")
            return None
        if self.status == SCHEDULING:
            if tick >= self.current_activity_start_tick:
                self.current_activity.start(tick=tick)
                self.status = WORKING
        if self.status == WORKING:
            self.current_activity.progress(tick=tick)
            if self.current_activity.has_completed(tick=tick):
                self.previous_activity = self.current_activity
                self.current_activity = None
                self.status = READY
                return self.previous_activity
        # Mean work is not complete:
        return None
    
    def to_dict(self) -> Dict:
        output = {"status": self.status}
        if self.current_activity:
            output["current"] = self.current_activity.to_dict()
        if self.previous_activity:
            output["previous"] = self.previous_activity.to_dict()
        return output

    def __str__(self) -> str:
        return json.dumps(self.to_dict())