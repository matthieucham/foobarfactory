from time import sleep
from typing import Dict

from model import factory
from model.activities import get_activty
from model.constants import READY


class FactoryRunner:
    def __init__(self) -> None:
        self.factory = factory.Factory()
        self.tick = 0

    def expose(self):
        self.factory.run(self.tick)
        return self.factory.to_dict()

    def load(self, *acts):
        activities = self._build_activities(*acts)
        self.factory.set_activities(self.tick, *activities)

    def run(self):
        self.factory.run(self.tick)

    def next(self):
        self.tick += 1

    @staticmethod
    def _build_activities(*activitydescriptors):
        activities = list()
        for act in activitydescriptors:
            if type(act) is tuple:
                acttype, actparams = act
                activities.append(get_activty(acttype, **actparams))
            else:
                activities.append(get_activty(act))
        return activities


class Runtime:
    def __init__(self, tick_delay=1) -> None:
        """
        Runtime constructor

        Args:
        - tick_delay: duration of a tick, default to 1 second.
        """
        self.runner = FactoryRunner()
        self.tick_delay = tick_delay

    def set_tick_delay(self, delay: int) -> None:
        self.tick_delay = delay

    def _count_available_robots(self):
        current = self.runner.expose()
        # there always are robots (at least 2)
        return len([r for r in current.get("robots") if r.get("status") == READY])

    def run(self, force_one_next=False) -> Dict:
        """
        Run the loaded activities until at least one robot is available
        Args:
        - force_one_next : When True, at least one tick will advance, even if some robots are available. Default False.
        """
        do_next_anyway = force_one_next
        while True:  # run until robots are available
            self.runner.run()
            if self._count_available_robots() > 0 and not do_next_anyway:
                break
            if self.tick_delay > 0:  # else : no sleep, speed-of-light factory
                sleep(self.tick_delay)
            self.runner.next()
            do_next_anyway = False
        return self.runner.expose()

    def program(self, *activycodes) -> None:
        """Program robots with these activities to do next"""
        self.runner.load(*activycodes)

    def display(self) -> Dict:
        return {"tick": self.runner.tick, "situation": self.runner.expose()}
