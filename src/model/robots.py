"""Definition of Robots capabilities"""

import json
from typing import Dict
from . import activities
from .constants import READY, SCHEDULING, WORKING


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

    def schedule(self, activity: activities.BaseActivity, tick: int) -> None:
        if not self.status == READY:
            raise RobotException("Cannot schedule activity on busy robot")
        self.status = SCHEDULING
        self.current_activity = activity
        if self.previous_activity and not self.previous_activity.type == activity.type:
            self.current_activity_start_tick = (
                tick + 5
            )  # changing activity takes 5 ticks
        else:
            self.current_activity_start_tick = tick

    def work(self, tick: int) -> activities.BaseActivity:
        """
        Make the current activity progress

        If the activity is completed, it is returned.
        Otherwise, return nothing.
        """
        if not self.current_activity:
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

    def to_dict(self) -> Dict:  # pragma: no cover
        output = {"status": self.status}
        if self.current_activity:
            output["current"] = self.current_activity.to_dict()
        else:
            output["current"] = None
        if self.previous_activity:
            output["previous"] = self.previous_activity.to_dict()
        else:
            output["previous"] = None
        return output

    def __str__(self) -> str:  # pragma: no cover
        return json.dumps(self.to_dict())
