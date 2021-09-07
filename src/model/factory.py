import copy
import json
from collections import defaultdict
from typing import Dict, List, Tuple
from . import robots
from .constants import (
    RES_KEY_NEWROBOTS,
    RES_KEY_BARS,
    RES_KEY_FOOBARS,
    RES_KEY_FOOS,
    RES_KEY_MONEY,
)
from .activities import (
    BaseActivity,
    ActivityResourcesException,
)


def group_by_previous_activity(
    robots: List[robots.Robot], no_act_key: str = "idle"
) -> Dict[str, robots.Robot]:
    """Organize robots by type of their previous activity"""
    bots_by_act = defaultdict(list)
    for bot in robots:
        if bot.previous_activity:
            bots_by_act[bot.previous_activity.type].append(bot)
        else:
            bots_by_act[no_act_key].append(bot)
    return bots_by_act


class FactoryException(Exception):
    """Exceptions raised by the factory"""

    pass


class Factory:
    def __init__(self, initial_robots_nb: int = 2) -> None:
        self.robots = [robots.Robot() for _ in range(0, initial_robots_nb)]
        self.resources = {
            RES_KEY_FOOS: 6,
            RES_KEY_BARS: 0,
            RES_KEY_FOOBARS: 0,
            RES_KEY_MONEY: 3,
        }

    def to_dict(self) -> Dict:
        return {
            "resources": copy.deepcopy(self.resources),
            "robots": [copy.deepcopy(r.to_dict()) for r in self.robots],
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict())

    ### PUBLIC METHODS ###

    def run(self, tick: int) -> None:
        """Run the factory at the specified tick and update the situation"""
        for rob in self.robots:
            self._update_after_activity(rob.work(tick=tick))

    def set_activities(self, tick, *activities) -> None:
        """Set activities on available robots.

        If any activity is wrong (not enough resources) then an exception is raised
        and no activity is assigned to any robot"""
        future_resources = self.resources.copy()  # shallow copy is enough here
        avrobots = [r for r in self.robots if r.status == robots.READY]
        assignments = self._validate_activities(avrobots, future_resources, *activities)
        # All checks have passed, assignments are valid so:
        for robot, activity in assignments:
            self.resources = activity.take_resources(self.resources)
            robot.schedule(activity=activity, tick=tick)

    ### PRIVATE METHODS ###

    def _validate_activities(
        self, available_robots, available_resources, *activities
    ) -> List[Tuple[robots.Robot, BaseActivity]]:
        """
        Validate activities and return assignments (robot, activity)

        Raise FactoryException if any activity is invalid (not enough resource)
        """
        future_assignments = list()
        if len(available_robots) < len(activities):
            raise FactoryException("Not enough available robots")
        try:
            # reorder activities to have previous first
            # in order to minimize changing assignment time
            previousacts = {
                bot.previous_activity.type if bot.previous_activity else None
                for bot in available_robots
            }
            sortedacts = sorted(
                activities, key=lambda act: 0 if act.type in previousacts else 1
            )
            for act in sortedacts:
                available_resources = act.take_resources(available_resources)
                # Try to assign the act to a robot which previously did the same activity
                # to minimize the time lost between activities
                assigned = self._find_good_robot(available_robots, act.type)
                # the assigned robot is no longer available:
                available_robots.remove(assigned)
                future_assignments.append((assigned, act))
            return future_assignments
        except ActivityResourcesException as actexcept:
            raise FactoryException("Not enough resources", actexcept)

    def _update_after_activity(self, activity: BaseActivity) -> None:
        """Update the factory situation after the processing of the provided activity"""
        if activity is None:
            return
        newresources = activity.deliver_result(self.resources)
        if RES_KEY_NEWROBOTS in newresources:
            # add robots
            self.robots.extend(
                [robots.Robot() for _ in range(0, newresources.get(RES_KEY_NEWROBOTS))]
            )
            del newresources[RES_KEY_NEWROBOTS]
        self.resources = newresources

    def _find_good_robot(self, avrobots, activity_type: str) -> robots.Robot:
        # preference order:
        # 1- robot with the same previous activity type
        # 2- robot without previous activity
        # 3- robot with a different activity
        robots = group_by_previous_activity(avrobots)
        sameact = robots.get(activity_type, [])
        if len(sameact) > 0:
            return sameact.pop()
        idle = robots.get("idle", [])
        if len(idle) > 0:
            return idle.pop()
        # now, any bot will do...
        for _, bots in robots.items():
            if len(bots) > 0:
                return bots.pop()
        # should not happen
        raise FactoryException("Not enough robots")
