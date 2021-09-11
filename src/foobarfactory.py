from typing import Dict, Iterable, List, Tuple
import click
import copy
from model.factory import FactoryException
from runtime import Runtime
from model.constants import (
    READY,
    RES_KEY_BARS,
    RES_KEY_FOOS,
    RES_KEY_FOOBARS,
    RES_KEY_MONEY,
    MINEFOO,
    MINEBAR,
    ASSEMBLEFOOBAR,
    SELLFOOBAR,
    BUYROBOT,
)

FOOBARFACTORY = Runtime(tick_delay=0)


def display(datadict, cleanscreen=True):
    if cleanscreen:
        click.clear()
    click.secho(f"Tick ", fg="blue", nl=False)
    click.secho(datadict["tick"], fg="blue", bg="white", bold=True)
    click.secho(f"Foos: {datadict['situation']['resources']['foos']}", fg="green")
    click.secho(f"Bars: {datadict['situation']['resources']['bars']}", fg="green")
    click.secho(f"Foobars: {datadict['situation']['resources']['foobars']}", fg="green")
    click.secho(f"Money: {datadict['situation']['resources']['money']}", fg="green")
    click.secho(f"Robots: {len(datadict['situation']['robots'])}", fg="green")
    for bot in datadict["situation"]["robots"]:
        click.secho(f"Robot: {bot}", fg="red", bg="white")


class FactoryPilot:
    """Base class for pilot: choose activities to do depending on the situation."""

    @staticmethod
    def _get_nb_possible_actions(robots: Iterable[Dict]):
        if not robots:
            return 0
        return len([bot for bot in robots if bot["status"] == READY])

    @staticmethod
    def _get_type_possible_actions(resources):
        actions = [MINEFOO, MINEBAR]
        if resources[RES_KEY_FOOS] > 0 and resources[RES_KEY_BARS] > 0:
            actions.append(ASSEMBLEFOOBAR)
        if resources[RES_KEY_FOOBARS] > 0:
            actions.append(SELLFOOBAR)
        if resources[RES_KEY_MONEY] >= 3 and resources[RES_KEY_FOOS] >= 6:
            actions.append(BUYROBOT)
        return actions

    def get_activities(self, situation: Dict) -> List:
        raise NotImplementedError()


class InteractiveFactoryPilot(FactoryPilot):

    display_labels = {
        MINEFOO: "Mine (F)oo",
        MINEBAR: "Mine (B)ar",
        ASSEMBLEFOOBAR: "(A)ssemble foobar",
        SELLFOOBAR: "(S)ell foobars",
        BUYROBOT: "Buy (R)obot",
    }

    def get_activities(self, situation: Dict) -> List:
        res = copy.deepcopy(situation.get("situation").get("resources"))
        activities = []
        for _ in range(
            0, self._get_nb_possible_actions(situation.get("situation").get("robots"))
        ):
            possible_actions = [
                self.display_labels.get(act)
                for act in self._get_type_possible_actions(res)
            ]
            possible_actions.extend(["Do (N)othing"])
            valid_key_entered = False
            while not valid_key_entered:
                act = click.prompt(", ".join(possible_actions), type=str)
                if act.upper() == "F":
                    activities.append(MINEFOO)
                    valid_key_entered = True
                elif act.upper() == "B":
                    activities.append(MINEBAR)
                    valid_key_entered = True
                elif act.upper() == "A":
                    activities.append(ASSEMBLEFOOBAR)
                    res[RES_KEY_FOOS] -= 1
                    res[RES_KEY_BARS] -= 1
                    valid_key_entered = True
                elif act.upper() == "S":
                    activities.append(
                        (SELLFOOBAR, {"nbtosell": min(res[RES_KEY_FOOBARS], 5)})
                    )
                    res[RES_KEY_FOOBARS] -= min(res[RES_KEY_FOOBARS], 5)
                    valid_key_entered = True
                elif act.upper() == "R":
                    activities.append(BUYROBOT)
                    res[RES_KEY_MONEY] -= 3
                    res[RES_KEY_FOOS] -= 6
                    valid_key_entered = True
                elif act.upper() == "N":
                    # voluntary no action
                    valid_key_entered = True
                    continue
                else:
                    click.secho("Invalid key pressed, try again", fg="white", bg="red")
        return activities


class DumbAutopilot(FactoryPilot):
    """
    This autopilot follows a straightforward strategy:

    - 28 new robots to buy
    - means 6*28 = 168 foos to provide
    - and 3*28 = 84 money units to provide
    - means 84 foobars to sell
    - means 84 foobars to assemble but that will require more attempts
    - means 84 more foos and 84 bars to provide

    The strategy will be:
    - assemble 84 foobars
    - mine 168 foos
    - buy robots

    Obviously this is not optimized at all because only two robots are doing all the work.
    """

    def get_activities(self, situation: Dict) -> List:
        # nbpa will always be 2 at the beginning because this strategy is dumb:
        nbpa = self._get_nb_possible_actions(situation.get("situation").get("robots"))
        nbrobots = len(situation.get("situation").get("robots"))
        # when nbrobots is greater than 2, it means we are buying robots with all
        # our resources, and do nothing else than that.
        # get a snapshot of the current resources
        res = copy.deepcopy(situation.get("situation").get("resources"))
        # hold chosen activities
        activities = []
        for _ in range(0, nbpa):
            nbfoobars = res.get(RES_KEY_FOOBARS)
            nbfoos = res.get(RES_KEY_FOOS)
            nbmoney = res.get(RES_KEY_MONEY)
            if nbrobots == 2:
                # Do foobars as long as we haven't reach 84
                if nbfoobars + nbmoney < 84:
                    nbmissing = 84 - nbmoney - nbfoobars
                    if res.get(RES_KEY_FOOS) < nbmissing:
                        activities.append(MINEFOO)
                        res[RES_KEY_FOOS] += 1
                    elif res.get(RES_KEY_BARS) < nbmissing:
                        activities.append(MINEBAR)
                        res[RES_KEY_BARS] += 1
                    else:
                        # enough resources
                        activities.append(ASSEMBLEFOOBAR)
                        # adjust resources for next activity choice of the same round
                        # assuming foobar will succeed
                        res[RES_KEY_FOOS] -= 1
                        res[RES_KEY_BARS] -= 1
                        res[RES_KEY_FOOBARS] += 1
                # Do foos as long as we haven't reach 168
                elif nbfoos < 168:
                    activities.append(MINEFOO)
                    res[RES_KEY_FOOS] += 1
                # Sell foobars
                elif nbmoney < 84:
                    nbfoobars = res.get(RES_KEY_FOOBARS)
                    activities.append((SELLFOOBAR, {"nbtosell": min(nbfoobars, 5)}))
                    # adjust resources for next activity choice of the same round
                    res[RES_KEY_FOOBARS] -= nbfoobars
                    res[RES_KEY_MONEY] += min(nbfoobars, 5)
                # Buy robot
                elif nbmoney >= 3 and nbfoos >= 6:
                    activities.append(BUYROBOT)
                    res[RES_KEY_MONEY] -= 3
                    res[RES_KEY_FOOS] -= 6
            elif nbmoney >= 3 and nbfoos >= 6:
                activities.append(BUYROBOT)
                res[RES_KEY_MONEY] -= 3
                res[RES_KEY_FOOS] -= 6
        return activities


@click.command()
def foobarfactory():
    pilot = InteractiveFactoryPilot()
    dumbpilot = DumbAutopilot()
    while len(FOOBARFACTORY.display().get("situation").get("robots")) < 30:
        display(FOOBARFACTORY.display())
        activities = dumbpilot.get_activities(FOOBARFACTORY.display())
        try:
            if activities:
                FOOBARFACTORY.program(*activities)
                FOOBARFACTORY.run()
            else:
                FOOBARFACTORY.run(force_one_next=True)
        except FactoryException as err:
            click.secho(f"Factory error: {str(err)}", fg="white", bg="red")
    display(FOOBARFACTORY.display())


if __name__ == "__main__":
    foobarfactory()
