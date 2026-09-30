from youtube_live_bot.members import MemberManager


def test_member_add_and_subtract(tmp_path):
    manager = MemberManager(tmp_path / "members.json", max_count=10)
    assert manager.add("멤버A", 375)[0]
    assert manager.subtract("멤버A", 75)
    assert manager.format_text() == "👤 멤버A 300"
