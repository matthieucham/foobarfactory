import copy
import json
import logging
from collections import defaultdict
from typing import Dict
from model import robots
from model.activities import (
    ActivityException,
    BaseActivity,
    MINEBAR,
    MINEFOO,
    ASSEMBLEFOOBAR,
    SELLFOOBAR,
    BUYROBOT,
)

# TODO move logger config to main script
from logging.config import fileConfig

fileConfig("logging.ini")

# App logger as configured by logger.py
logger = logging.getLogger()


class FactoryException(Exception):
    """Exceptions raised by the factory"""

    pass


class Factory:
    def __init__(self, initial_robots_nb: int = 2) -> None:
        self.robots = [robots.Robot() for _ in range(0, initial_robots_nb)]
        self.resources = {
                "foos": 0,
                "bars": 0,
                "foobars": 0,
                "money": 0,
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
        """Run the factory at the specified tick and returns a view of the situation after the tick"""
        logger.debug("running factory at tick %s", tick)
        for rob in self.robots:
            logger.debug("advancing work of robot %s", rob)
            self._update_after_activity(rob.work(tick=tick))


    def set_activities(self, tick, *activities) -> None:
        """Set activities on available robots.

        If any activity is wrong (not enough resources) then an exception is raised
        and no activity is assigned to any robot"""
        future_resources = self.resources.copy()  # shallow copy is enough here
        future_assignments = list()
        avrobots = self._get_available_robots()
        if len(avrobots) < len(activities):
            raise FactoryException("Not enough available robots")
        try:
            # reorder activities to have previous first
            # in order to minimize changing assignment time
            previousacts = {bot.previous_activity.get_type() if bot.previous_activity else None for bot in avrobots}
            sortedacts = sorted(activities, key=lambda act: 0 if act in previousacts else 1)
            bots_by_act = defaultdict(list)
            for bot in avrobots:
                if bot.previous_activity:
                    bots_by_act[bot.previous_activity.get_type()].append(bot)
                else:
                    bots_by_act["idle"].append(bot)
            for act in sortedacts:
                future_resources = act.take_ressources(future_resources)
                # Try to assign the act to a robot which previously did the same activity
                # to minimize the time lost between activities
                assigned = self._find_good_robot(bots_by_act, act.get_type())
                future_assignments.append((assigned, act))
        except ActivityException as actexcept:
            raise FactoryException("Not enough resources", actexcept)
        # All checks have passed, assignments are valid so:
        for robot, activity in future_assignments:
            self.resources = activity.take_resources(self.resources)
            robot.schedule(activity=activity, tick=tick)

    ### PRIVATE METHODS ###

    def _get_available_robots(self):
        """Return the list of available robots"""
        return [r for r in self.robots if r.status == robots.READY]

    def _update_after_activity(self, activity: BaseActivity) -> None:
        """Update the factory situation after the processing of the provided activity"""
        if activity is None:
            logger.debug("no completed activity")
            return
        if activity.get_type() == MINEFOO:
            logger.debug(
                "activity %s completed, result=%s", activity, activity.result()
            )
            self.resources["foos"] += activity.result()
        elif activity.get_type() == MINEBAR:
            logger.debug(
                "activity %s completed, result=%s", activity, activity.result()
            )
            self.resources["bars"] += activity.result()
        elif activity.get_type() == ASSEMBLEFOOBAR:
            logger.debug(
                "activity %s completed, result=%s", activity, activity.result()
            )
            self.situation["foobars"] += activity.result()
            # the bar is reusable if no new foobar assembled
            if activity.result() == 0:
                self.resources["bars"] += 1
        elif activity.get_type() == SELLFOOBAR:
            logger.debug(
                "activity %s completed, result=%s", activity, activity.result()
            )
            self.resources["money"] += activity.result()
        elif activity.get_type() == BUYROBOT:
            nb_new_robots = activity.result()
            logger.debug("activity %s completed, result=%s", activity, nb_new_robots)
            # add robots
            self.robots.extend([robots.Robot() for _ in range(0, nb_new_robots)])
        else:
            raise FactoryException("Unknown activity type %s", activity.get_type())
        
    def _find_good_robot(self, avrobots, activity_type:str) -> robots.Robot:
        # preference order:
        # 1- robot with the same previous activity type
        # 2- robot without previous activity
        # 3- robot with a different activity
        sameact = avrobots.get(activity_type,[])
        if len(sameact) > 0:
            return sameact.pop()
        idle = avrobots.get("idle", [])
        if len(idle) > 0:
            return idle.pop()
        # now, any bot will do...
        for _, bots in avrobots.items():
            if len(bots) > 0:
                return bots.pop()
        # should not happen
        raise FactoryException("Not enough robots")