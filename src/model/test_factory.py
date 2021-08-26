import pytest
from unittest.mock import call, patch, MagicMock

import json
from . import activities, robots, factory


# Fixtures


@pytest.fixture
def mock_robot_builder():
    def _make_robot(prevtype):
        robot = MagicMock()
        robot.status = robots.READY
        if prevtype is not None:
            robot.previous_activity = MagicMock()
            robot.previous_activity.type = prevtype
        else:
            robot.previous_activity = None
        return robot

    yield _make_robot


@pytest.fixture
def mock_activity_builder():
    def _make_act(type):
        act = MagicMock()
        act.status = activities.READY
        act.type = type
        # make sure resources available are not an issue:
        act.take_resources.return_value = dict()
        return act

    yield _make_act


class TestFactory:
    def test_init_noparam(self):
        fact = factory.Factory()
        assert len(fact.robots) == 2
        assert fact.resources == {
            "foos": 0,
            "bars": 0,
            "foobars": 0,
            "money": 0,
        }

    @pytest.mark.parametrize("nb", range(1, 11))
    def test_init(self, nb):
        fact = factory.Factory(initial_robots_nb=nb)
        assert len(fact.robots) == nb
        assert fact.resources == {
            "foos": 0,
            "bars": 0,
            "foobars": 0,
            "money": 0,
        }

    def test_to_dict(self):
        fact = factory.Factory()
        result = fact.to_dict()
        assert "resources" in result
        assert "robots" in result

    @pytest.mark.parametrize("nbrobots", range(1, 11))
    @patch.object(factory.Factory, "_update_after_activity")
    @patch.object(factory.robots.Robot, "work")
    def test_run(self, mockwork, mockupdateafteract, nbrobots):
        """Check that all robots work are called correctly"""
        # given
        fact = factory.Factory(initial_robots_nb=nbrobots)
        # when
        fact.run(42)
        # then
        mockwork.assert_called_with(tick=42)
        assert len(mockupdateafteract.mock_calls) == nbrobots

    @pytest.mark.parametrize(
        argnames=["before", "after"],
        argvalues=(
            (
                '{"foos": 1,"bars": 0,"foobars": 0,"money": 0}',
                '{"foos": 1,"bars": 0,"foobars": 0,"money": 0}',
            ),
        ),
    )
    def test_update_after_activity_noact(self, before, after):
        fact = factory.Factory()
        fact.resources = json.loads(before)
        # when
        fact._update_after_activity(None)
        # then
        assert fact.resources == json.loads(after)

    def test_update_after_buyrobot(self):
        fact = factory.Factory(initial_robots_nb=2)
        buy = activities.BuyRobot()
        buy.status = activities.COMPLETED
        # when
        fact._update_after_activity(buy)
        # then
        assert len(fact.robots) == 3

    def test_group_by_previous_activity(self):
        bot1 = robots.Robot()
        bot2 = robots.Robot()
        bot3 = robots.Robot()
        bot4 = robots.Robot()
        bot1.previous_activity = activities.MineFoo()
        bot2.previous_activity = activities.MineBar()
        bot3.previous_activity = activities.MineFoo()
        bot4.previous_activity = None
        # when
        grouped = factory.group_by_previous_activity([bot1, bot2, bot3, bot4])
        grouped2 = factory.group_by_previous_activity(
            [bot1, bot2, bot3, bot4], no_act_key="toto"
        )
        # then
        assert grouped == {
            "idle": [bot4],
            activities.MINEFOO: [bot1, bot3],
            activities.MINEBAR: [bot2],
        }
        assert grouped2 == {
            "toto": [bot4],
            activities.MINEFOO: [bot1, bot3],
            activities.MINEBAR: [bot2],
        }

    @pytest.mark.parametrize(
        argnames=["nbrobots", "nbbusy"],
        argvalues=(
            (
                2,
                0,
            ),
            (
                2,
                1,
            ),
        ),
    )
    @patch.object(factory.Factory, "_validate_activities")
    def test_set_activities(self, mockvalidate, nbrobots, nbbusy):
        fact = factory.Factory(nbrobots)
        for tobusy in range(0, nbbusy):
            fact.robots[tobusy].status = robots.SCHEDULING
        assignments = [(MagicMock(), MagicMock()) for _ in range(0, nbrobots - nbbusy)]
        mockvalidate.return_value = assignments
        # when
        fact.set_activities(42, MagicMock())
        # then
        for robot, act in assignments:
            act.take_resources.assert_called_once()
            robot.schedule.assert_called_once_with(activity=act, tick=42)

    @pytest.mark.parametrize(["nbrobots", "nbactivities"], ((0, 1), (1, 3), (4, 5)))
    def test_validate_activities_nerobots(self, nbrobots, nbactivities):
        """Check exception raised when not enough robots"""
        fact = factory.Factory(initial_robots_nb=nbrobots)
        with pytest.raises(factory.FactoryException):
            fact._validate_activities(
                fact.robots, {}, *[MagicMock() for _ in range(0, nbactivities)]
            )

    @pytest.mark.parametrize(
        argnames=[
            "previousacts",
            "nextacts",
            "expectsame",
            "expectnone",
            "expectchange",
        ],
        argvalues=(
            (
                [None, None],
                [activities.MINEFOO, activities.MINEFOO],
                0,
                2,
                0,
            ),
            (
                [None, None],
                [activities.MINEFOO],
                0,
                1,
                0,
            ),
            (
                [activities.MINEFOO, activities.MINEFOO],
                [activities.MINEFOO, activities.MINEFOO],
                2,
                0,
                0,
            ),
            (
                [activities.MINEFOO, activities.MINEFOO],
                [activities.MINEFOO],
                1,
                0,
                0,
            ),
            (
                [activities.MINEBAR, activities.MINEBAR],
                [activities.MINEFOO, activities.MINEFOO],
                0,
                0,
                2,
            ),
            (
                [activities.MINEBAR, activities.MINEBAR],
                [activities.MINEFOO],
                0,
                0,
                1,
            ),
            (
                [activities.MINEBAR, activities.MINEBAR],
                [activities.MINEFOO, activities.MINEBAR],
                1,
                0,
                1,
            ),
            (
                [activities.MINEBAR, None],
                [activities.MINEFOO, activities.MINEBAR],
                1,
                1,
                0,
            ),
            (
                [activities.MINEBAR, None],
                [activities.MINEFOO, activities.ASSEMBLEFOOBAR],
                0,
                1,
                1,
            ),
            (
                [activities.MINEFOO, None, None],
                [activities.MINEFOO, activities.MINEFOO, activities.MINEFOO],
                1,
                2,
                0,
            ),
            (
                [activities.MINEFOO, None, None],
                [activities.MINEFOO, activities.MINEBAR, activities.ASSEMBLEFOOBAR],
                1,
                2,
                0,
            ),
            (
                [activities.MINEFOO, activities.MINEBAR, None],
                [activities.MINEFOO, activities.MINEBAR, activities.ASSEMBLEFOOBAR],
                2,
                1,
                0,
            ),
            (
                [activities.MINEFOO, activities.MINEBAR, None],
                [activities.MINEFOO, activities.MINEBAR, activities.ASSEMBLEFOOBAR],
                2,
                1,
                0,
            ),
            (
                [activities.MINEFOO, activities.MINEBAR, activities.MINEBAR],
                [activities.MINEFOO, activities.MINEBAR, activities.ASSEMBLEFOOBAR],
                2,
                0,
                1,
            ),
            (
                [activities.MINEFOO, activities.MINEBAR, None, activities.MINEFOO],
                [activities.MINEBAR, activities.MINEFOO, activities.MINEBAR],
                2,
                1,
                0,
            ),
        ),
    )
    def test_assignments(
        self,
        mock_robot_builder,
        mock_activity_builder,
        previousacts,
        nextacts,
        expectsame,
        expectnone,
        expectchange,
    ):
        """Check that assignments are optimized"""
        fact = factory.Factory()
        robots = [mock_robot_builder(preva) for preva in previousacts]
        acts = [mock_activity_builder(nexta) for nexta in nextacts]
        # when
        assresult = fact._validate_activities(robots, dict(), *acts)
        # then
        assert len(assresult) == len(acts)
        assert (
            len(
                [
                    (bot, act)
                    for bot, act in assresult
                    if bot.previous_activity and bot.previous_activity.type == act.type
                ]
            )
            == expectsame
        )
        assert (
            len([(bot, act) for bot, act in assresult if bot.previous_activity is None])
            == expectnone
        )
        assert (
            len(
                [
                    (bot, act)
                    for bot, act in assresult
                    if bot.previous_activity
                    and not bot.previous_activity.type == act.type
                ]
            )
            == expectchange
        )
