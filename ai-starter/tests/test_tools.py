from ai_starter.tools import add, current_time


def test_add():
    assert add.invoke({"a": 2, "b": 3}) == 5


def test_time_is_iso():
    assert "T" in current_time.invoke({})
