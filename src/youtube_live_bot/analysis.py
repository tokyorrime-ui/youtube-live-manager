"""Post-stream live chat analysis and highlight formatting."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

WINDOW_SECONDS = 10


@dataclass
class Bucket:
    bucket: int
    laugh: int = 0
    count: int = 0
    users: set[str] = field(default_factory=set)


@dataclass
class Segment:
    bucket_start: int
    bucket_end: int
    time: int
    laugh: int
    count: int
    users: set[str]


def sec_to_time(sec: int | float) -> str:
    hours, remainder = divmod(int(sec), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"


def get_segment_duration_seconds(segment: Segment) -> int:
    return (segment.bucket_end - segment.bucket_start + 1) * WINDOW_SECONDS


def format_duration_text(duration_sec: int | float) -> str:
    duration_sec = int(duration_sec)
    if duration_sec >= 60:
        minutes, seconds = divmod(duration_sec, 60)
        return f"{minutes}분동안" if seconds == 0 else f"{minutes}분 {seconds}초동안"
    return f"{duration_sec}초동안"


def get_start_time(segment: Segment) -> str:
    start_sec = segment.bucket_start * WINDOW_SECONDS
    return sec_to_time(max(0, start_sec - 8))


def merge_consecutive_segments(items: list[Segment]) -> list[Segment]:
    if not items:
        return []

    items = sorted(items, key=lambda item: item.bucket_start)
    merged: list[Segment] = []
    current = items[0]

    for item in items[1:]:
        if item.bucket_start == current.bucket_end + 1:
            current = Segment(
                bucket_start=current.bucket_start,
                bucket_end=item.bucket_end,
                time=current.time,
                laugh=current.laugh + item.laugh,
                count=current.count + item.count,
                users=current.users | item.users,
            )
        else:
            merged.append(current)
            current = item

    merged.append(current)
    return merged


def analyze_live_chat_json(json_file: Path) -> tuple[list[Segment], list[Segment]]:
    funny: dict[int, Bucket] = defaultdict(lambda: Bucket(bucket=-1))
    shock: dict[int, Bucket] = defaultdict(lambda: Bucket(bucket=-1))

    if not json_file.exists():
        return [], []

    print(f"🔍 하이라이트 분석 시작: {json_file}")

    with json_file.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                data = json.loads(line)
                replay = data.get("replayChatItemAction", {})
                video_offset = data.get("videoOffsetTimeMsec") or replay.get("videoOffsetTimeMsec")
                if not video_offset:
                    continue

                offset_seconds = int(video_offset) / 1000.0
                if offset_seconds < 0:
                    continue

                key = int(offset_seconds // WINDOW_SECONDS)
                actions = replay.get("actions", [])

                for action in actions:
                    item = action.get("addChatItemAction", {}).get("item", {})
                    renderer = (
                        item.get("liveChatTextMessageRenderer")
                        or item.get("liveChatPaidMessageRenderer")
                        or item.get("liveChatMembershipItemRenderer")
                    )
                    if not renderer:
                        continue

                    author = renderer.get("authorName", {}).get("simpleText", "Unknown")
                    runs = renderer.get("message", {}).get("runs", [])
                    text = "".join(run.get("text", "") for run in runs)
                    if not text:
                        text = renderer.get("headerSubtext", {}).get("simpleText", "")
                    if not text:
                        continue

                    if "ㅋ" in text or "w" in text:
                        bucket = funny[key]
                        bucket.bucket = key
                        bucket.users.add(author)
                        bucket.laugh += text.count("ㅋ") + text.count("w")

                    text_clean = re.sub(r"\s+", "", text)
                    if text_clean == "?" or re.match(r"^(헐|와)(ㅋ+)?$", text_clean):
                        bucket = shock[key]
                        bucket.bucket = key
                        bucket.users.add(author)
                        bucket.count += 1
            except Exception as exc:
                print(f"분석 중 오류: {exc}")
                continue

    fun_segments = [
        Segment(bucket_start=k, bucket_end=k, time=k * WINDOW_SECONDS, laugh=v.laugh, count=0, users=v.users)
        for k, v in funny.items()
        if v.laugh >= 50 and len(v.users) >= 12
    ]
    shock_segments = [
        Segment(bucket_start=k, bucket_end=k, time=k * WINDOW_SECONDS, laugh=0, count=v.count, users=v.users)
        for k, v in shock.items()
        if len(v.users) >= 8
    ]

    print("🏁 분석이 완료되었습니다.")
    return merge_consecutive_segments(fun_segments), merge_consecutive_segments(shock_segments)


def pick_spaced_top(items: list[Segment], top_n: int = 5, min_gap: int = 60) -> list[Segment]:
    picked: list[Segment] = []
    for item in sorted(items, key=lambda x: x.laugh, reverse=True):
        if all(abs(item.time - picked_item.time) >= min_gap for picked_item in picked):
            picked.append(item)
        if len(picked) >= top_n:
            break
    return sorted(picked, key=lambda x: x.time)


def build_highlight_comment(fun_results: list[Segment], shock_results: list[Segment]) -> str:
    def get_emoji(count: int) -> str:
        if count >= 500:
            return "💀"
        if count >= 300:
            return "🔥"
        if count >= 150:
            return "😂"
        return "😆"

    if not fun_results and not shock_results:
        return ""

    lines = ["👑 오늘 방송 하이라이트"]

    if fun_results:
        lines.append("😂 웃음 TOP 5")
        for item in pick_spaced_top(fun_results, top_n=5, min_gap=60):
            lines.append(
                f"{get_start_time(item)} {get_emoji(item.laugh)} "
                f"(ㅋㅋ {item.laugh}개 / 인원 {len(item.users)}명) "
                f"{format_duration_text(get_segment_duration_seconds(item))}"
            )

    if shock_results:
        lines.append("")
        lines.append("😲 당황 TOP 5")
        top_shock = sorted(shock_results, key=lambda item: len(item.users), reverse=True)[:5]
        for item in sorted(top_shock, key=lambda item: item.time):
            lines.append(
                f"{get_start_time(item)} ❗ "
                f"(반응 {item.count}개 / 인원 {len(item.users)}명) "
                f"{format_duration_text(get_segment_duration_seconds(item))}"
            )

    if fun_results:
        lines.append("")
        lines.append("🔥 전체 타임라인:")
        timeline = pick_spaced_top(fun_results, top_n=len(fun_results), min_gap=60)
        for item in timeline:
            lines.append(
                f"{get_start_time(item)} {get_emoji(item.laugh)} "
                f"(ㅋㅋ {item.laugh}개 / 인원 {len(item.users)}명) "
                f"{format_duration_text(get_segment_duration_seconds(item))}"
            )

    return "\n".join(lines)
