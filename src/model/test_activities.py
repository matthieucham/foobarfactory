from unittest.mock import MagicMock
import pytest
import json

from model.constants import COMPLETED, CONSUMED, RES_KEY_FOOS

from . import activities


class TestActivityCommon:
    @pytest.mark.parametrize(
        argnames=["activity", "type", "duration_min", "duration_max"],
        argvalues=[
            (activities.MineFoo(), activities.MINEFOO, 1, 1),
            (activities.MineBar(), activities.MINEBAR, 0.5, 2.0),
            (activities.AssembleFoobar(), activities.ASSEMBLEFOOBAR, 2, 2),
            (activities.SellFoobar(), activities.SELLFOOBAR, 10, 10),
            (activities.BuyRobot(), activities.BUYROBOT, 0, 0),
        ],
    )
    def test_init(self, activity, type, duration_min, duration_max):
        assert activity.status == activities.READY
        assert activity.type == type
        assert duration_min <= activity.duration <= duration_max
        assert activity.start_tick is None

    @pytest.mark.parametrize(
        argnames=["activity", "tickval"],
        argvalues=[
            (activities.MineFoo(), 2),
            (activities.MineBar(), 2),
            (activities.AssembleFoobar(), 2),
            (activities.SellFoobar(), 2),
        ],
    )
    def test_start(self, activity, tickval):
        activity.start(tick=tickval)
        assert activity.status == activities.RUNNING
        assert activity.start_tick == tickval

    @pytest.mark.parametrize(
        argnames=["activity", "status"],
        argvalues=[
            (activities.MineFoo(), activities.RUNNING),
            (activities.MineFoo(), activities.COMPLETED),
            (activities.MineBar(), activities.RUNNING),
            (activities.MineBar(), activities.COMPLETED),
            (activities.AssembleFoobar(), activities.RUNNING),
            (activities.AssembleFoobar(), activities.COMPLETED),
            (activities.SellFoobar(), activities.RUNNING),
            (activities.SellFoobar(), activities.COMPLETED),
            (activities.BuyRobot(), activities.RUNNING),
            (activities.BuyRobot(), activities.COMPLETED),
        ],
    )
    def test_start_notready(self, activity, status):
        # Given
        activity.status = status
        activity.start_tick = 1
        # When
        activity.start(tick=2)
        # Then
        assert activity.start_tick == 1
        assert activity.status == status

    @pytest.mark.parametrize(
        argnames=[
            "activity",
            "start_tick",
            "notfinished_tick",
            "done_tick",
        ],
        argvalues=[
            (
                activities.MineFoo(),
                1,
                1,
                2,
            ),
            (
                activities.MineBar(),
                1,
                1,
                3,
            ),
            (
                activities.AssembleFoobar(),
                1,
                2,
                3,
            ),
            (
                activities.SellFoobar(nbtosell=3),
                1,
                5,
                11,
            ),
        ],
    )
    def test_progress(self, activity, start_tick, notfinished_tick, done_tick):
        # set the start tick of the activity
        activity.start(start_tick)
        # check that the activity is still running
        activity.progress(notfinished_tick)
        assert activity.status == activities.RUNNING
        assert not activity.has_completed(notfinished_tick)
        # do the activity progress past upon its duration
        activity.progress(done_tick)
        assert activity.status == activities.COMPLETED
        assert activity.has_completed(done_tick)

    @pytest.mark.parametrize(
        argnames=[
            "activity",
            "start_tick",
            "toosoon_tick",
        ],
        argvalues=[
            (
                activities.MineFoo(),
                2,
                1,
            ),
            (
                activities.MineBar(),
                2,
                1,
            ),
            (
                activities.AssembleFoobar(),
                5,
                2,
            ),
            (
                activities.SellFoobar(nbtosell=3),
                8,
                5,
            ),
        ],
    )
    def test_progress_fail(self, activity, start_tick, toosoon_tick):
        # set the start tick of the activity
        activity.start(start_tick)
        with pytest.raises(ValueError):
            activity.progress(toosoon_tick)

    @pytest.mark.parametrize(
        argnames=["activity", "status"],
        argvalues=[
            (activities.MineFoo(), activities.RUNNING),
            (activities.MineFoo(), activities.COMPLETED),
            (activities.MineFoo(), activities.CONSUMED),
            (activities.MineBar(), activities.RUNNING),
            (activities.MineBar(), activities.COMPLETED),
            (activities.MineBar(), activities.CONSUMED),
            (activities.AssembleFoobar(), activities.RUNNING),
            (activities.AssembleFoobar(), activities.COMPLETED),
            (activities.AssembleFoobar(), activities.CONSUMED),
            (activities.SellFoobar(), activities.RUNNING),
            (activities.SellFoobar(), activities.COMPLETED),
            (activities.SellFoobar(), activities.CONSUMED),
            (activities.BuyRobot(), activities.RUNNING),
            (activities.BuyRobot(), activities.COMPLETED),
            (activities.BuyRobot(), activities.CONSUMED),
        ],
    )
    def test_take_resources_badstatus(self, activity, status):
        activity.status = status
        with pytest.raises(activities.ActivityStatusException):
            activity.take_resources({})

    @pytest.mark.parametrize(
        argnames=["activity", "status"],
        argvalues=[
            (activities.MineFoo(), activities.RUNNING),
            (activities.MineFoo(), activities.READY),
            (activities.MineFoo(), activities.CONSUMED),
            (activities.MineBar(), activities.RUNNING),
            (activities.MineBar(), activities.READY),
            (activities.MineBar(), activities.CONSUMED),
            (activities.AssembleFoobar(), activities.RUNNING),
            (activities.AssembleFoobar(), activities.READY),
            (activities.AssembleFoobar(), activities.CONSUMED),
            (activities.SellFoobar(), activities.RUNNING),
            (activities.SellFoobar(), activities.READY),
            (activities.SellFoobar(), activities.CONSUMED),
            (activities.BuyRobot(), activities.RUNNING),
            (activities.BuyRobot(), activities.READY),
            (activities.BuyRobot(), activities.CONSUMED),
        ],
    )
    def test_deliver_result_badstatus(self, activity, status):
        activity.status = status
        with pytest.raises(activities.ActivityStatusException):
            activity.deliver_result({})

    @pytest.mark.parametrize(
        argnames=[
            "activitycode",
        ],
        argvalues=[
            (activities.MINEFOO,),
            (activities.MINEBAR,),
            (activities.ASSEMBLEFOOBAR,),
            (activities.SELLFOOBAR,),
            (activities.BUYROBOT,),
        ],
    )
    def test_get_activity(self, activitycode):
        act = activities.get_activty(activitycode)
        assert act.type == activitycode

    def test_get_activity_fail(self):
        with pytest.raises(ValueError):
            act = activities.get_activty("Z")


# Tests for specific activity


class TestMineFoo:
    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
            ),
        ),
    )
    def test_take_resources_ok(self, before, after):
        act = activities.MineFoo()
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.take_resources(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict[RES_KEY_FOOS] = 10
        assert remaining[RES_KEY_FOOS] == afterdict[RES_KEY_FOOS]

    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 1,"bars": 0,"foobars": 0,"money": 0}',
            ),
        ),
    )
    def test_deliver_result_ok(self, before, after):
        act = activities.MineFoo()
        act.status = COMPLETED
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.deliver_result(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict[RES_KEY_FOOS] = 10
        assert remaining[RES_KEY_FOOS] == afterdict[RES_KEY_FOOS]
        assert act.status == CONSUMED


class TestMineBar:
    def test_init_duration(self):
        """
        Check that this activity duration is one of the 4 allowed values
        """
        act = activities.MineBar()
        assert act.duration in {0.5, 1.0, 1.5, 2.0}

    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
            ),
        ),
    )
    def test_take_resources_ok(self, before, after):
        act = activities.MineBar()
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.take_resources(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict[RES_KEY_FOOS] = 10
        assert remaining[RES_KEY_FOOS] == afterdict[RES_KEY_FOOS]

    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 0,"bars": 1,"foobars": 0,"money": 0}',
            ),
        ),
    )
    def test_deliver_result_ok(self, before, after):
        act = activities.MineBar()
        act.status = COMPLETED
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.deliver_result(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict[RES_KEY_FOOS] = 10
        assert remaining[RES_KEY_FOOS] == afterdict[RES_KEY_FOOS]
        assert act.status == CONSUMED


class TestAssembleFoobar:
    def test_init_futureresult(self):
        """
        Check that the result is 0 or 1
        """
        act = activities.AssembleFoobar()
        assert act.future_result in {0, 1}

    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 1,"bars": 1,"foobars": 0,"money": 0}',
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
            ),
            (
                '{"foos": 3,"bars": 3,"foobars": 0,"money": 0}',
                '{"foos": 2,"bars": 2,"foobars": 0,"money": 0}',
            ),
            (
                '{"foos": 3,"bars": 2,"foobars": 0,"money": 0}',
                '{"foos": 2,"bars": 1,"foobars": 0,"money": 0}',
            ),
        ),
    )
    def test_take_resources_ok(self, before, after):
        act = activities.AssembleFoobar()
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.take_resources(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict["foos"] = 10
        assert remaining["foos"] == afterdict["foos"]

    @pytest.mark.parametrize(
        argnames=[
            "before",
        ],
        argvalues=(
            ('{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',),
            ('{"foos": 3,"bars": 0,"foobars": 0,"money": 0}',),
            ('{"foos": 0,"bars": 2,"foobars": 0,"money": 0}',),
        ),
    )
    def test_take_resources_failure(self, before):
        act = activities.AssembleFoobar()
        beforedict = json.loads(before)
        with pytest.raises(activities.ActivityResourcesException):
            act.take_resources(resources=beforedict)

    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 0,"bars": 1,"foobars": 0,"money": 0}',
            ),
        ),
    )
    def test_deliver_result_not_assembled(self, before, after):
        act = activities.AssembleFoobar()
        act.status = COMPLETED
        act.future_result = 0
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.deliver_result(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict[RES_KEY_FOOS] = 10
        assert remaining[RES_KEY_FOOS] == afterdict[RES_KEY_FOOS]
        assert act.status == CONSUMED

    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 0,"bars": 0,"foobars": 1,"money": 0}',
            ),
        ),
    )
    def test_deliver_result_assembled(self, before, after):
        act = activities.AssembleFoobar()
        act.status = COMPLETED
        act.future_result = 1
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.deliver_result(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict[RES_KEY_FOOS] = 10
        assert remaining[RES_KEY_FOOS] == afterdict[RES_KEY_FOOS]
        assert act.status == CONSUMED


class TestSellFoobar:
    @pytest.mark.parametrize("nbtosell", range(1, 6))
    def test_init_ok(self, nbtosell):
        """
        Check that the futureresult will be the requested number of items to sell
        """
        act = activities.SellFoobar(nbtosell=nbtosell)
        assert act.future_result == nbtosell

    @pytest.mark.parametrize("nbtosell", (0, 6, 10))
    def test_init_ko(self, nbtosell):
        """
        Check that nbtosell must be in a range
        """
        with pytest.raises(ValueError):
            act = activities.SellFoobar(nbtosell=nbtosell)

    @pytest.mark.parametrize(
        argnames=["nbtosell", "before", "after"],
        argvalues=(
            (
                1,
                '{"foos": 0,"bars": 0,"foobars": 1,"money": 0}',
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
            ),
            (
                1,
                '{"foos": 2,"bars": 2,"foobars": 2,"money": 0}',
                '{"foos": 2,"bars": 2,"foobars": 1,"money": 0}',
            ),
            (
                2,
                '{"foos": 2,"bars": 2,"foobars": 2,"money": 0}',
                '{"foos": 2,"bars": 2,"foobars": 0,"money": 0}',
            ),
        ),
    )
    def test_take_resources_ok(self, nbtosell, before, after):
        act = activities.SellFoobar(nbtosell=nbtosell)
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.take_resources(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict["foos"] = 10
        assert remaining["foos"] == afterdict["foos"]

    @pytest.mark.parametrize(
        argnames=["nbtosell", "before"],
        argvalues=(
            (
                1,
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
            ),
            (
                2,
                '{"foos": 2,"bars": 2,"foobars": 1,"money": 0}',
            ),
            (
                5,
                '{"foos": 2,"bars": 2,"foobars": 4,"money": 0}',
            ),
        ),
    )
    def test_take_resources_failure(self, nbtosell, before):
        act = activities.SellFoobar(nbtosell)
        beforedict = json.loads(before)
        with pytest.raises(activities.ActivityResourcesException):
            act.take_resources(resources=beforedict)

    @pytest.mark.parametrize(
        argnames=["nbtosell", "before", "after"],
        argvalues=(
            (
                1,
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 1}',
            ),
            (
                3,
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 3}',
            ),
        ),
    )
    def test_deliver_result_ok(self, nbtosell, before, after):
        act = activities.SellFoobar(nbtosell=nbtosell)
        act.status = COMPLETED
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.deliver_result(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict[RES_KEY_FOOS] = 10
        assert remaining[RES_KEY_FOOS] == afterdict[RES_KEY_FOOS]
        assert act.status == CONSUMED


class TestBuyRobot:
    def test_start(self):
        """The Buy activity is immediate"""
        act = activities.BuyRobot()
        assert act.status == activities.READY
        act.start(tick=0)
        assert act.status == activities.COMPLETED

    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 6,"bars": 0,"foobars": 0,"money": 3}',
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
            ),
            (
                '{"foos": 7,"bars": 2,"foobars": 2,"money": 4}',
                '{"foos": 1,"bars": 2,"foobars": 2,"money": 1}',
            ),
        ),
    )
    def test_take_resources_ok(self, before, after):
        act = activities.BuyRobot()
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.take_resources(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict["foos"] = 10
        assert remaining["foos"] == afterdict["foos"]

    @pytest.mark.parametrize(
        argnames=["before"],
        argvalues=(
            ('{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',),
            ('{"foos": 2,"bars": 2,"foobars": 6,"money": 2}',),
            ('{"foos": 2,"bars": 2,"foobars": 5,"money": 3}',),
        ),
    )
    def test_take_resources_failure(self, before):
        act = activities.BuyRobot()
        beforedict = json.loads(before)
        with pytest.raises(activities.ActivityResourcesException):
            act.take_resources(resources=beforedict)

    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 0,"bars": 0,"foobars": 0,"money": 0, "newrobots": 1}',
            ),
        ),
    )
    def test_deliver_result_ok(self, before, after):
        act = activities.BuyRobot()
        act.status = COMPLETED
        beforedict = json.loads(before)
        afterdict = json.loads(after)
        remaining = act.deliver_result(resources=beforedict)
        assert remaining == afterdict
        # make sure the output is decoupled from the input
        beforedict[RES_KEY_FOOS] = 10
        assert remaining[RES_KEY_FOOS] == afterdict[RES_KEY_FOOS]
        assert act.status == CONSUMED
