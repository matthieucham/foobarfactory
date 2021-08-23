import pytest
from unittest.mock import MagicMock
import json
import copy

from . import robots, activities


# Fixtures


@pytest.fixture
def mock_activity():
    """Yield an activity mock"""
    yield MagicMock()


# Tests


class TestRobot:
    def test_init(self):
        rob = robots.Robot()
        assert rob.status == robots.READY
        assert rob.previous_activity is None
        assert rob.current_activity is None
        assert rob.current_activity_start_tick is None

    @pytest.mark.parametrize(
        ["activity"],
        [
            (activities.MineFoo(),),
            (activities.MineBar(),),
            (activities.AssembleFoobar(),),
            (activities.SellFoobar(),),
            (activities.BuyRobot(),),
        ],
    )
    def test_schedule_newrobot(self, activity):
        """
        Test activity scheduling on robots without previous activity
        """
        rob = robots.Robot()
        rob.schedule(activity=activity, tick=1)
        assert rob.status == robots.SCHEDULING
        assert rob.current_activity == activity
        assert rob.previous_activity is None
        assert rob.current_activity_start_tick == 1

    @pytest.mark.parametrize(
        ["activity"],
        [
            (activities.MineFoo(),),
            (activities.MineBar(),),
            (activities.AssembleFoobar(),),
            (activities.SellFoobar(),),
            (activities.BuyRobot(),),
        ],
    )
    def test_schedule_sameactivity(self, activity):
        """
        Test activity scheduling on robots with same previous activity type
        """
        rob = robots.Robot()
        rob.previous_activity = copy.deepcopy(activity)
        rob.schedule(activity=activity, tick=1)
        assert rob.status == robots.SCHEDULING
        assert rob.current_activity == activity
        assert rob.previous_activity is not None
        assert rob.current_activity_start_tick == 1

    @pytest.mark.parametrize(
        ["activity"],
        [
            (activities.MineFoo(),),
            (activities.MineBar(),),
            (activities.AssembleFoobar(),),
            (activities.SellFoobar(),),
            (activities.BuyRobot(),),
        ],
    )
    def test_schedule_changeactivity(self, activity):
        """
        Test activity scheduling on robots with same previous activity type
        """
        rob = robots.Robot()
        previous = copy.deepcopy(activity)
        # change type to force something different
        previous.type = next(
            filter(
                lambda x: not x == activity.type,
                [activities.MINEFOO, activities.MINEBAR],
            )
        )
        rob.previous_activity = previous
        rob.schedule(activity=activity, tick=1)
        assert rob.status == robots.SCHEDULING
        assert rob.current_activity == activity
        assert rob.previous_activity is not None
        assert rob.current_activity_start_tick == 6

    @pytest.mark.parametrize(
        ["status"],
        [
            (robots.SCHEDULING,),
            (robots.WORKING,),
        ],
    )
    def test_schedule_badstatus(self, status):
        rob = robots.Robot()
        rob.status = status
        with pytest.raises(robots.RobotException):
            rob.schedule(None, 0)

    def test_work_noactivity(self):
        rob = robots.Robot()
        assert rob.work(0) is None

    def test_work_scheduling_nostart(self, mock_activity):
        # given
        rob = robots.Robot()
        rob.status = robots.SCHEDULING
        rob.current_activity = mock_activity
        rob.current_activity_start_tick = 1
        # when
        result = rob.work(0)
        # then
        assert result is None
        mock_activity.start.assert_not_called()
        mock_activity.progress.assert_not_called()
        assert rob.status == robots.SCHEDULING

    @pytest.mark.parametrize(
        argnames=[
            "completed",
        ],
        argvalues=((False,), (True,)),
    )
    def test_work_scheduling_andstart(self, mock_activity, completed):
        # given
        mock_activity.has_completed.return_value = completed
        rob = robots.Robot()
        rob.status = robots.SCHEDULING
        rob.current_activity = mock_activity
        rob.current_activity_start_tick = 1
        # when
        result = rob.work(1)
        # then
        mock_activity.start.assert_called_with(tick=1)
        mock_activity.progress.assert_called_with(tick=1)
        mock_activity.has_completed.assert_called_with(tick=1)
        if completed:
            assert rob.status == robots.READY
            assert rob.current_activity is None
            assert rob.previous_activity == mock_activity
            assert result == mock_activity
        else:
            assert rob.status == robots.WORKING
            assert rob.current_activity == mock_activity
            assert result is None

    def test_to_dict(self):
        rob = robots.Robot()
        result = rob.to_dict()
        assert "status" in result
        assert "current" in result
        assert "previous" in result
