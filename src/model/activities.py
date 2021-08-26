""" Definition of different activities robots can do """

# activity statuses

import random
import json
from typing import Dict

from .constants import (
    RES_KEY_MONEY,
    RES_KEY_BARS,
    RES_KEY_FOOBARS,
    RES_KEY_FOOS,
    RES_KEY_NEWROBOTS,
    READY,
    RUNNING,
    COMPLETED,
    CONSUMED,
    MINEFOO,
    MINEBAR,
    ASSEMBLEFOOBAR,
    SELLFOOBAR,
    BUYROBOT,
)


class ActivityResourcesException(Exception):
    """Raised by activities when resources are not sufficient"""

    pass


class ActivityStatusException(Exception):
    """Raised by activities when bad status for the requested operation"""

    pass


class BaseActivity:
    """
    Base class, handles status logic in an uniform way.

    CAUTION : NOT THREAD-SAFE
    """

    def __init__(self, type: str, duration: float, future_result: int) -> None:
        self.status = READY
        self.type = type
        self.duration = duration
        self.future_result = future_result
        self.start_tick = None

    def start(self, tick: int) -> None:
        """
        Launch the activity and register the start tick.

        Do nothing if the activity is not in READY state.
        """
        if self.status == READY:
            self.start_tick = tick
            self.status = RUNNING
            # A startup is a special kind of progress !
            self.progress(tick=tick)

    def progress(self, tick: int) -> None:
        """Advance the activity change its status to COMPLETED if it is done."""
        if tick < self.start_tick:
            raise ValueError(
                f"Current tick value {tick} is less than start_tick {self.start_tick}"
            )
        if self.has_completed(tick):
            self.status = COMPLETED

    # def result(self) -> int:
    #     """
    #     Give back the activity result as an int : number of entities produced.

    #     The context (type of activity) provide info about what has been produced.
    #     """
    #     if self.status == COMPLETED:
    #         return self.future_result
    #     raise ActivityStatusException("Activity has not completed, cannot get result")

    def has_completed(self, tick) -> bool:
        return tick - self.start_tick >= self.duration

    def take_resources(self, resources: Dict) -> Dict:
        """
        Consume the needed resources to do the activity.

        Arguments:
          - resources: Dict of resources available before the activity
        Return the remaining resources after consumption.
        Raise ActivityResourcesException if resources are not sufficient.
        Raise ActivityStatusException if activity not ready.
        """
        if not self.status == READY:
            raise ActivityStatusException(
                f"Activity not READY, current status={self.status}"
            )
        return self._take_resources(resources)  # impl by subclasses

    def deliver_result(self, resources: Dict) -> Dict:
        """
        Add the result of the completed activity to the resources dict

        Arguments:
          - resources: Dict of resources before adding the new ones
        Return the new resources after addition.
        Raise ActivityStatusException if activity not completed.
        """
        if not self.status == COMPLETED:
            raise ActivityStatusException(
                f"Activity not COMPLETED, current status={self.status}"
            )
        result = self._deliver_result(resources)  # impl by subclasses
        self.status = CONSUMED
        return result

    def __str__(self) -> str:
        return json.dumps(self.to_dict())

    def to_dict(self) -> Dict:
        """Return a dictionary-based representation of the activity"""
        return self.__dict__


class MineFoo(BaseActivity):
    """Take 1 tick, produce 1 Foo"""

    def __init__(self) -> None:
        super().__init__(type=MINEFOO, duration=1, future_result=1)

    def _take_resources(self, resources: Dict) -> Dict:
        # no resource needed.
        return resources.copy()

    def _deliver_result(self, resources: Dict) -> Dict:
        newres = resources.copy()
        newres[RES_KEY_FOOS] += self.future_result
        return newres


class MineBar(BaseActivity):
    """Take between 0.5 and 2 ticks, produce one Bar"""

    def __init__(self) -> None:
        # duration is a random value between 0.5 and 2.0 ticks.
        # To have more interesting results, possible values are
        # voluntarily limited to 0.5, 1.0, 1.5 and 2.0
        # So, instead of this: (any tenth of a tick)
        # duration = float(random.randint(5, 20)/10.0)
        # set duration like this:
        super().__init__(
            type=MINEBAR,
            duration=[0.5, 1.0, 1.5, 2.0][random.randint(0, 3)],
            future_result=1,
        )

    def _take_resources(self, resources: Dict) -> Dict:
        # no resource needed.
        return resources.copy()

    def _deliver_result(self, resources: Dict) -> Dict:
        newres = resources.copy()
        newres[RES_KEY_BARS] += self.future_result
        return newres


class AssembleFoobar(BaseActivity):
    """Take 2 ticks, produce 1 Foobar with 60% chance or 0"""

    def __init__(self) -> None:
        # There is a 60% chance (or 3/5) that 1 Foobar was assembled
        # Otherwise it's a failure : 0 Foobar assembled
        super().__init__(
            type=ASSEMBLEFOOBAR,
            duration=2,
            future_result=[1, 1, 1, 0, 0][random.randint(0, 4)],
        )

    def _take_resources(self, resources: Dict) -> Dict:
        try:
            if resources[RES_KEY_FOOS] < 1 or resources[RES_KEY_BARS] < 1:
                raise ActivityResourcesException(
                    "Not enough resource for activity %s", self
                )
        except KeyError:
            raise ActivityResourcesException(
                "Not enough resource for activity %s", self
            )
        newres = resources.copy()
        newres[RES_KEY_FOOS] -= 1
        newres[RES_KEY_BARS] -= 1
        return newres

    def _deliver_result(self, resources: Dict) -> Dict:
        newres = resources.copy()
        newres[RES_KEY_FOOBARS] += self.future_result
        # the bar is reusable if no new foobar assembled
        if self.future_result == 0:
            newres[RES_KEY_BARS] += 1
        return newres


class SellFoobar(BaseActivity):
    """Take 10 ticks, produce the requested number of money units"""

    def __init__(self, nbtosell: int = 1) -> None:
        if nbtosell < 1 or nbtosell > 5:
            raise ValueError("nbtosell must be between 1 and 5")
        super().__init__(type=SELLFOOBAR, duration=10, future_result=nbtosell)
        self.nbtosell = nbtosell

    def _take_resources(self, resources: Dict) -> Dict:
        try:
            if resources[RES_KEY_FOOBARS] < self.nbtosell:
                raise ActivityResourcesException(
                    "Not enough resource for activity %s", self
                )
        except KeyError:
            raise ActivityResourcesException(
                "Not enough resource for activity %s", self
            )
        newres = resources.copy()
        newres[RES_KEY_FOOBARS] -= self.nbtosell
        return newres

    def _deliver_result(self, resources: Dict) -> Dict:
        newres = resources.copy()
        newres[RES_KEY_MONEY] += self.future_result
        return newres


class BuyRobot(BaseActivity):
    """Take 0 tick, produce one robot"""

    def __init__(self) -> None:
        super().__init__(type=BUYROBOT, duration=0, future_result=1)

    def _take_resources(self, resources: Dict) -> Dict:
        try:
            if resources[RES_KEY_MONEY] < 3 or resources[RES_KEY_FOOS] < 6:
                raise ActivityResourcesException(
                    "Not enough resource for activity %s", self
                )
        except KeyError:
            raise ActivityResourcesException(
                "Not enough resource for activity %s", self
            )
        newres = resources.copy()
        newres[RES_KEY_MONEY] -= 3
        newres[RES_KEY_FOOS] -= 6
        return newres

    def _deliver_result(self, resources: Dict) -> Dict:
        newres = resources.copy()
        newres[RES_KEY_NEWROBOTS] = self.future_result
        return newres
