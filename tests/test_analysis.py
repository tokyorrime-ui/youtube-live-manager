from pathlib import Path

from youtube_live_bot.analysis import Segment, build_highlight_comment, merge_consecutive_segments


def test_merge_consecutive_segments():
    items = [
        Segment(1, 1, 10, 50, 0, {"a"}),
        Segment(2, 2, 20, 20, 0, {"b"}),
        Segment(4, 4, 40, 80, 0, {"c"}),
    ]
    merged = merge_consecutive_segments(items)
    assert len(merged) == 2
    assert merged[0].bucket_start == 1
    assert merged[0].bucket_end == 2
    assert merged[0].laugh == 70
    assert merged[0].users == {"a", "b"}


def test_build_highlight_comment():
    segment = Segment(1, 1, 10, 50, 0, {"a", "b"})
    comment = build_highlight_comment([segment], [])
    assert "오늘 방송 하이라이트" in comment
    assert "웃음 TOP 5" in comment
