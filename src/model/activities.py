""" Definition of different activities robots can do """

# activity statuses

import random
import json
from typing import Dict

# statuses
READY = "ready"
RUNNING = "running"
COMPLETED = "completed"

# types
MINEFOO = "minefoo"
MINEBAR = "minebar"
ASSEMBLEFOOBAR = "assemblefoobar"
SELLFOOBAR = "sellfoobar"
BUYROBOT = "buyrobot"


class ActivityException(Exception):
    """Exceptions raised by activities"""

    pass


class BaseActivity:
    """Base class, handles status logic in an uniform way"""

    def __init__(self, type: str, duration: float, future_result: int) -> None:
        self.status = READY
        self.type = type
        self.duration = duration
        self.future_result = future_result

    def start(self, tick: int) -> None:
        if self.status == READY:
            self.start_tick = tick
        self.status = RUNNING

    def progress(self, tick: int) -> None:
        if tick < self.start_tick:
            raise ActivityException(
                f"Current tick value {tick} is less than start_tick {self.start_tick}"
            )
        if self.has_completed(tick):
            self.status = COMPLETED

    def result(self) -> int:
        if self.status == COMPLETED:
            return self.future_result
        raise ActivityException("Activity has not completed, cannot get result")

    def get_status(self) -> str:
        return self.status

    def has_completed(self, tick) -> bool:
        return tick - self.start_tick >= self.duration

    def get_type(self) -> str:
        return self.type
    
    def take_resources(self, resources:Dict) -> Dict:
        """
        Consume the needed resources to do the activity.

        Returns the remaining resources after consumption.
        Raise ActivityException if resources are not sufficient.
        """
        # base implementation : need nothing.
        return resources.copy()

    def __str__(self) -> str:
        return json.dumps(self.to_dict())
    
    def to_dict(self) -> Dict:
        return self.__dict__
    

class MineFooActivity(BaseActivity):
    """Take 1 tick, produce 1 Foo"""

    def __init__(self) -> None:
        super().__init__(type=MINEFOO, duration=1, future_result=1)
    
    def take_resources(self, resources:Dict) -> Dict:
        # no resource needed.
        return resources.copy()


class MineBarActivity(BaseActivity):
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
    
    def take_resources(self, resources:Dict) -> Dict:
        # no resource needed.
        return resources.copy()


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
    
    def take_resources(self, resources:Dict) -> Dict:
        try:
            if resources["foos"] < 1 or resources["bars"] < 1:
                raise ActivityException("Not enough resource for activity %s", self)
        except KeyError:
            raise ActivityException("Not enough resource for activity %s", self)
        resources["foos"] -= 1
        resources["bars"] -= 1
        return resources.copy()


class SellFoobar(BaseActivity):
    """Take 10 ticks, produce the requested number of money units"""

    def __init__(self, nbtosell: int) -> None:
        if nbtosell < 1 or nbtosell > 5:
            raise ValueError("nbtosell must be between 1 and 5")
        super().__init__(type=SELLFOOBAR, duration=10, future_result=nbtosell)
        self.nbtosell = nbtosell
    
    def take_resources(self, resources:Dict) -> Dict:
        try:
            if resources["foobars"] <  self.nbtosell:
                raise ActivityException("Not enough resource for activity %s", self)
        except KeyError:
            raise ActivityException("Not enough resource for activity %s", self)
        resources["foobars"] -= self.nbtosell
        return resources.copy()


class BuyRobot(BaseActivity):
    """Take 0 tick, produce one robot"""

    def __init__(self) -> None:
        super().__init__(type=BUYROBOT, duration=0, future_result=1)
    
    def take_resources(self, resources:Dict) -> Dict:
        try:
            if resources["money"] <  3 or resources["foos"] < 6:
                raise ActivityException("Not enough resource for activity %s", self)
        except KeyError:
            raise ActivityException("Not enough resource for activity %s", self)
        resources["money"] -= 3
        resources["foos"] -= 6
        return resources.copy()
