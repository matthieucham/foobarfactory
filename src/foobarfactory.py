import click
import copy
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

FOOBARFACTORY = Runtime()


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


def prompt_for_actions(datadict):
    nb_possible_actions = len(
        [bot for bot in datadict["situation"]["robots"] if bot["status"] == READY]
    )

    def _get_possible_actions(resources):
        actions = ["Mine (F)oo", "Mine (B)ar"]
        if resources[RES_KEY_FOOS] > 0 and resources[RES_KEY_BARS] > 0:
            actions.append("(A)ssemble foobar")
        if resources[RES_KEY_FOOBARS] > 0:
            actions.append("(S)ell foobars")
        if resources[RES_KEY_MONEY] >= 3 and resources[RES_KEY_FOOS] >= 6:
            actions.append("Buy (R)obot")
        actions.append("Do (N)othing")
        return actions

    res = copy.deepcopy(datadict["situation"]["resources"])
    activities = []
    for _ in range(0, nb_possible_actions):
        possible_actions = _get_possible_actions(res)
        incorrect = True
        while incorrect:
            act = click.prompt(", ".join(possible_actions), type=str)
            if act.upper() == "F":
                activities.append(MINEFOO)
                incorrect = False
            elif act.upper() == "B":
                activities.append(MINEBAR)
                incorrect = False
            elif act.upper() == "A":
                activities.append(ASSEMBLEFOOBAR)
                res[RES_KEY_FOOS] -= 1
                res[RES_KEY_BARS] -= 1
                incorrect = False
            elif act.upper() == "S":
                activities.append(
                    (SELLFOOBAR, {"nbtosell": min(res[RES_KEY_FOOBARS], 5)})
                )
                res[RES_KEY_FOOBARS] -= min(res[RES_KEY_FOOBARS], 5)
                incorrect = False
            elif act.upper() == "R":
                activities.append(BUYROBOT)
                res[RES_KEY_MONEY] -= 3
                res[RES_KEY_FOOS] -= 6
                incorrect = False
            elif act.upper() == "N":
                incorrect = False
                continue
            else:
                click.secho("Unknown action, try again", fg="red", bg="white")

    return activities


@click.command()
def foobarfactory():
    while len(FOOBARFACTORY.display().get("situation").get("robots")) < 5:
        display(FOOBARFACTORY.display())
        activities = prompt_for_actions(FOOBARFACTORY.display())
        if activities:
            FOOBARFACTORY.program(*activities)
            FOOBARFACTORY.run()
        else:
            FOOBARFACTORY.run(force_one_next=True)


if __name__ == "__main__":
    foobarfactory()
