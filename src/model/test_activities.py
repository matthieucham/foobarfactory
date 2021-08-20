import pytest

from . import activities


class TestActivityCommon:
    @pytest.mark.parametrize(
        argnames=["activity", "type", "duration_min", "duration_max"],
        argvalues=[
            (activities.MineFooActivity(), activities.MINEFOO, 1, 1),
            (activities.MineBarActivity(), activities.MINEBAR, 0.5, 2.0),
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
            (activities.MineFooActivity(), 2),
            (activities.MineBarActivity(), 2),
            (activities.AssembleFoobar(), 2),
            (activities.SellFoobar(), 2),
            (activities.BuyRobot(), 2),
        ],
    )
    def test_start(self, activity, tickval):
        activity.start(tick=tickval)
        assert activity.status == activities.RUNNING
        assert activity.start_tick == tickval

    @pytest.mark.parametrize(
        argnames=["activity", "status"],
        argvalues=[
            (activities.MineFooActivity(), activities.RUNNING),
            (activities.MineFooActivity(), activities.COMPLETED),
            (activities.MineBarActivity(), activities.RUNNING),
            (activities.MineBarActivity(), activities.COMPLETED),
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
