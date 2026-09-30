from youtube_live_bot.stack import StackManager


def test_stack_set_and_format(tmp_path):
    manager = StackManager(tmp_path / "stack.json")
    manager.update("금연", 10, "set")
    assert "금연" in manager.format_text()
    assert "10" in manager.format_text()


def test_stack_delete(tmp_path):
    manager = StackManager(tmp_path / "stack.json")
    manager.update("금연", 10, "set")
    manager.update("금연", 3, "delete")
    assert "7" in manager.format_text()
