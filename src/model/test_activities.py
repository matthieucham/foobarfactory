import pytest
import json

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
            "possible_result",
        ],
        argvalues=[
            (
                activities.MineFoo(),
                1,
                1,
                2,
                {
                    1,
                },
            ),
            (
                activities.MineBar(),
                1,
                1,
                3,
                {
                    1,
                },
            ),
            (
                activities.AssembleFoobar(),
                1,
                2,
                3,
                {
                    0,
                    1,
                },
            ),
            (
                activities.SellFoobar(nbtosell=3),
                1,
                5,
                11,
                {
                    3,
                },
            ),
        ],
    )
    def test_progress_result(
        self, activity, start_tick, notfinished_tick, done_tick, possible_result
    ):
        # set the start tick of the activity
        activity.start(start_tick)
        # check that the activity is still running
        activity.progress(notfinished_tick)
        assert activity.status == activities.RUNNING
        assert not activity.has_completed(notfinished_tick)
        # in this case it is not allowed to retrieve the result
        with pytest.raises(activities.ActivityException):
            activity.result()
        # do the activity progress past upon its duration
        activity.progress(done_tick)
        assert activity.status == activities.COMPLETED
        assert activity.has_completed(done_tick)
        # the result is now available
        assert activity.result() in possible_result


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
        beforedict["foos"] = 10
        assert remaining["foos"] == afterdict["foos"]


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
        beforedict["foos"] = 10
        assert remaining["foos"] == afterdict["foos"]


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
        with pytest.raises(activities.ActivityException):
            act.take_resources(resources=beforedict)


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
        with pytest.raises(activities.ActivityException):
            act.take_resources(resources=beforedict)


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
        with pytest.raises(activities.ActivityException):
            act.take_resources(resources=beforedict)
