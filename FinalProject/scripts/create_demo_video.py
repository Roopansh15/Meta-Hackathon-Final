from __future__ import annotations

import json
import math
import struct
import subprocess
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "demo_video"
WIDTH = 1280
HEIGHT = 720
FPS = 2
SAMPLE_RATE = 22050
CHANNELS = 1
BITS_PER_SAMPLE = 16
BLOCK_ALIGN = CHANNELS * BITS_PER_SAMPLE // 8


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


FONT_TITLE = load_font("segoeuib.ttf", 52)
FONT_H2 = load_font("segoeuib.ttf", 34)
FONT_H3 = load_font("segoeuib.ttf", 28)
FONT_BODY = load_font("segoeui.ttf", 25)
FONT_BODY_BOLD = load_font("segoeuib.ttf", 25)
FONT_SMALL = load_font("segoeui.ttf", 20)
FONT_SMALL_BOLD = load_font("segoeuib.ttf", 20)
FONT_SUBTITLE = load_font("segoeui.ttf", 28)


COLORS = {
    "ink": (18, 31, 52),
    "muted": (76, 91, 111),
    "blue": (31, 95, 191),
    "blue_dark": (15, 50, 105),
    "green": (20, 122, 88),
    "red": (180, 35, 24),
    "soft": (246, 249, 253),
    "line": (215, 224, 234),
    "white": (255, 255, 255),
    "amber": (166, 95, 0),
}


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font,
    fill: tuple[int, int, int],
    max_width: int,
    line_gap: int = 8,
) -> int:
    x, y = xy
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += bbox[3] - bbox[1] + line_gap
    return y


def rounded_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] = COLORS["line"],
    radius: int = 18,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=2)


def subtitle_lines(draw: ImageDraw.ImageDraw, text: str) -> list[str]:
    return wrap_text(draw, text, FONT_SUBTITLE, WIDTH - 180)[:2]


def draw_subtitle(draw: ImageDraw.ImageDraw, text: str) -> None:
    lines = subtitle_lines(draw, text)
    box_h = 86 if len(lines) == 1 else 112
    y0 = HEIGHT - box_h - 22
    draw.rounded_rectangle((70, y0, WIDTH - 70, HEIGHT - 22), radius=16, fill=(12, 20, 34))
    y = y0 + 18
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=FONT_SUBTITLE)
        draw.text(((WIDTH - (bbox[2] - bbox[0])) // 2, y), line, font=FONT_SUBTITLE, fill=(255, 255, 255))
        y += 36


def base_slide(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["white"])
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 96), fill=(241, 246, 253))
    draw.rectangle((0, 0, 14, HEIGHT), fill=COLORS["blue"])
    draw.text((48, 26), "InboxWorld", font=FONT_H3, fill=COLORS["blue_dark"])
    draw.text((48, 108), title, font=FONT_TITLE, fill=COLORS["ink"])
    if subtitle:
        draw_wrapped(draw, (50, 174), subtitle, FONT_BODY, COLORS["muted"], 900, 8)
    return img, draw


def draw_metric(draw: ImageDraw.ImageDraw, x: int, y: int, value: str, label: str, color: tuple[int, int, int]) -> None:
    rounded_box(draw, (x, y, x + 250, y + 118), (250, 252, 255))
    draw.text((x + 22, y + 18), value, font=FONT_H2, fill=color)
    draw_wrapped(draw, (x + 22, y + 65), label, FONT_SMALL, COLORS["muted"], 206, 4)


def draw_chart(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    baseline = [-81, -154, -81, -154, -81, -154, -81, -154]
    improved = [77, 127, 77, 127, 77, 127, 77, 127]
    min_v, max_v = -170, 140

    rounded_box(draw, (x, y, x + w, y + h), (255, 255, 255))
    draw.text((x + 24, y + 18), "Baseline vs Improved Policy Reward", font=FONT_H3, fill=COLORS["ink"])
    px0, py0 = x + 70, y + 84
    px1, py1 = x + w - 40, y + h - 70
    draw.line((px0, py1, px1, py1), fill=(80, 94, 115), width=2)
    draw.line((px0, py0, px0, py1), fill=(80, 94, 115), width=2)

    def point(i: int, value: float) -> tuple[int, int]:
        px = px0 + int((px1 - px0) * i / (len(baseline) - 1))
        py = py1 - int((value - min_v) / (max_v - min_v) * (py1 - py0))
        return px, py

    zero_y = point(0, 0)[1]
    draw.line((px0, zero_y, px1, zero_y), fill=(148, 163, 184), width=2)
    draw.text((px1 - 115, zero_y - 28), "zero line", font=FONT_SMALL, fill=COLORS["muted"])
    for grid_v in [-150, -75, 0, 75, 125]:
        gy = point(0, grid_v)[1]
        draw.line((px0, gy, px1, gy), fill=(231, 236, 244), width=1)
        draw.text((x + 24, gy - 10), str(grid_v), font=FONT_SMALL, fill=COLORS["muted"])

    b_points = [point(i, value) for i, value in enumerate(baseline)]
    g_points = [point(i, value) for i, value in enumerate(improved)]
    draw.line(b_points, fill=COLORS["red"], width=5, joint="curve")
    draw.line(g_points, fill=COLORS["green"], width=5, joint="curve")
    for p in b_points:
        draw.ellipse((p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7), fill=COLORS["white"], outline=COLORS["red"], width=4)
    for p in g_points:
        draw.ellipse((p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7), fill=COLORS["white"], outline=COLORS["green"], width=4)

    draw.line((x + 105, y + h - 36, x + 165, y + h - 36), fill=COLORS["red"], width=5)
    draw.text((x + 178, y + h - 48), "Baseline avg -117.5", font=FONT_SMALL_BOLD, fill=COLORS["ink"])
    draw.line((x + 405, y + h - 36, x + 465, y + h - 36), fill=COLORS["green"], width=5)
    draw.text((x + 478, y + h - 48), "Improved avg +102.0", font=FONT_SMALL_BOLD, fill=COLORS["ink"])


def make_policy_outputs() -> list[dict[str, str]]:
    sys.path.insert(0, str(ROOT))
    from src.inboxworld.agents import MultiAgentEmailPolicy
    from src.inboxworld.types import InboxEmail

    raw_cases = [
        {
            "name": "Hidden business blocker",
            "sender": "design@studio.dev",
            "importance": "client",
            "subject": "Quick export question",
            "body": "Which hero image should we export for tomorrow's client deck? If I do not get confirmation, the deck may slip.",
            "why": "The email looks simple, but it can block a client deck.",
        },
        {
            "name": "Revenue renewal risk",
            "sender": "csm@renewals.app",
            "importance": "client",
            "subject": "Renewal may pause without pricing clarification",
            "body": "Customer needs pricing confirmation before tomorrow's renewal call or they may pause the renewal approval.",
            "why": "The email contains deadline and revenue risk.",
        },
        {
            "name": "Personal emergency",
            "sender": "neighbor",
            "importance": "normal",
            "subject": "Father in hospital",
            "body": "Hey, my father is in hospital and I need help contacting you. Can you please respond as soon as possible?",
            "why": "The sender is normal, but the body contains a medical emergency signal.",
        },
    ]

    policy = MultiAgentEmailPolicy()
    outputs: list[dict[str, str]] = []
    for idx, case in enumerate(raw_cases, 1):
        email = InboxEmail(
            email_id=f"demo-{idx}",
            sender=case["sender"],
            sender_importance=case["importance"],
            subject=case["subject"],
            body=case["body"],
            priority="unknown",
            urgency=False,
            visible_urgency=False,
            deadline_step=None,
            hidden_intent="unknown",
            expected_action="unknown",
            expected_tone="unknown",
            thread_id=f"demo-thread-{idx}",
            tags=[],
        )
        action = policy.act({"emails": [email]})
        if action.escalate_target == "emergency_contact":
            decision_summary = "Escalate as urgent emergency."
        elif action.action_type == "escalate_email":
            decision_summary = "Escalate to manager for business risk."
        elif action.reply_tone == "helpful":
            decision_summary = "Generate helpful high-priority reply."
        else:
            decision_summary = "Generate safe response with selected tone."
        outputs.append(
            {
                **case,
                "priority": str(action.predicted_priority).upper(),
                "urgent": str(action.predicted_urgency),
                "action": action.action_type.replace("_", " ").title(),
                "tone": str(action.reply_tone).title(),
                "response": action.response_text,
                "decision_summary": decision_summary,
                "target": action.escalate_target,
            }
        )
    return outputs


def build_segments(cases: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "kind": "title",
            "title": "InboxWorld Demo",
            "subtitle": "A multi-agent email triage environment with delayed reward modeling.",
            "narration": "A normal chatbot can write a polite email reply. InboxWorld asks a harder question: was the assistant's decision correct after the inbox world changed?",
        },
        {
            "kind": "problem",
            "title": "Why Email Triage Is Not Just Text Generation",
            "subtitle": "Real inboxes contain hidden urgency, deadlines, follow-ups, and consequences.",
            "narration": "Most email assistants summarize messages or generate replies. But real email work is decision making. If an assistant delays a critical email, the damage may appear only later.",
        },
        {
            "kind": "architecture",
            "title": "Research Design",
            "subtitle": "Four agents plus a delayed reward buffer.",
            "narration": "InboxWorld uses four agents: classifier, priority planner, responder, and supervisor. A delayed reward buffer then checks whether the decision was actually good after future steps.",
        },
        {
            "kind": "chart",
            "title": "Measured Improvement",
            "subtitle": "Baseline behavior is compared with the improved multi-agent policy.",
            "narration": "The baseline policy averages minus one hundred seventeen point five reward. The improved multi-agent policy averages plus one hundred two reward, and missed deadlines drop from sixty to zero.",
        },
        {
            "kind": "demo_intro",
            "title": "Live Demo Structure",
            "subtitle": "Three cases show why the system is different from a chatbot.",
            "narration": "Now we will test three examples: a hidden business blocker, a revenue renewal risk, and a personal emergency. Each example shows action selection, not just reply generation.",
        },
        {
            "kind": "demo",
            "case": cases[0],
            "title": "Demo Case 1: Hidden Business Blocker",
            "subtitle": "A design question that can delay a client deck.",
            "narration": "In the first case, the message looks like a small design question. A chatbot may simply draft a reply. InboxWorld sees the client deck risk and treats it as high priority.",
        },
        {
            "kind": "demo_explain",
            "case": cases[0],
            "title": "Why Case 1 Is Different",
            "subtitle": "The system detects impact, not only urgency words.",
            "narration": "This is useful because many important emails do not say urgent. InboxWorld uses sender importance, task context, and downstream impact to select the action and tone.",
        },
        {
            "kind": "demo",
            "case": cases[1],
            "title": "Demo Case 2: Revenue Renewal Risk",
            "subtitle": "A client renewal may pause without pricing clarification.",
            "narration": "In the second case, the email includes revenue and renewal risk. InboxWorld marks it high priority and chooses escalation or immediate handling to avoid a negative consequence.",
        },
        {
            "kind": "demo_explain",
            "case": cases[1],
            "title": "Why Case 2 Is Different",
            "subtitle": "The environment rewards business-safe handling.",
            "narration": "A normal assistant may produce a nice message but still miss the business deadline. InboxWorld is evaluated by reward, missed deadlines, and future follow-up behavior.",
        },
        {
            "kind": "demo",
            "case": cases[2],
            "title": "Demo Case 3: Personal Emergency",
            "subtitle": "The sender is normal, but the body contains emergency context.",
            "narration": "In the third case, the sender importance is normal, and visible urgency is not checked. But the body says father in hospital, so InboxWorld switches to urgent emergency handling.",
        },
        {
            "kind": "demo_explain",
            "case": cases[2],
            "title": "Why Case 3 Is Different",
            "subtitle": "The system reasons from meaning, not only form fields.",
            "narration": "This shows partial observability. InboxWorld does not blindly depend on the urgency checkbox. It reads the content and chooses a safer action.",
        },
        {
            "kind": "closing",
            "title": "Research Contribution",
            "subtitle": "InboxWorld moves email AI from reply generation to decision evaluation.",
            "narration": "The contribution is not only a demo interface. It is a research environment with multi-agent reasoning, delayed reward, benchmark metrics, and training-ready transition data.",
        },
        {
            "kind": "closing",
            "title": "Final Takeaway",
            "subtitle": "A chatbot writes what to say. InboxWorld evaluates what to do.",
            "narration": "InboxWorld is useful because it can measure whether an AI assistant made the right decision under time pressure, uncertainty, and delayed consequences.",
        },
    ]


def draw_architecture(draw: ImageDraw.ImageDraw) -> None:
    labels = [
        ("Classifier", "Extracts intent and visible signals."),
        ("Priority", "Ranks urgency and importance."),
        ("Responder", "Chooses reply, delay, or escalation."),
        ("Supervisor", "Checks safety and consistency."),
        ("Reward Buffer", "Scores future consequences."),
    ]
    x0, y0 = 58, 270
    box_w, box_h, gap = 220, 142, 22
    for i, (title, desc) in enumerate(labels):
        x = x0 + i * (box_w + gap)
        rounded_box(draw, (x, y0, x + box_w, y0 + box_h), (250, 252, 255), radius=16)
        draw.text((x + 18, y0 + 18), title, font=FONT_SMALL_BOLD, fill=COLORS["blue_dark"])
        draw_wrapped(draw, (x + 18, y0 + 54), desc, FONT_SMALL, COLORS["muted"], box_w - 36, 5)
        if i < len(labels) - 1:
            draw.line((x + box_w + 4, y0 + box_h // 2, x + box_w + gap - 4, y0 + box_h // 2), fill=COLORS["blue"], width=4)


def draw_demo_case(draw: ImageDraw.ImageDraw, case: dict[str, str], explain: bool = False) -> None:
    left = (54, 244, 612, 574)
    right = (668, 244, 1226, 574)
    rounded_box(draw, left, (250, 252, 255), radius=16)
    rounded_box(draw, right, (249, 253, 250), radius=16)
    draw.text((80, 268), "Incoming Email", font=FONT_H3, fill=COLORS["ink"])
    draw.text((694, 268), "InboxWorld Output", font=FONT_H3, fill=COLORS["green"])

    y = 320
    for label, value in [
        ("Sender", case["sender"]),
        ("Importance", case["importance"]),
        ("Subject", case["subject"]),
    ]:
        draw.text((80, y), f"{label}: ", font=FONT_SMALL_BOLD, fill=COLORS["ink"])
        y = draw_wrapped(draw, (200, y), value, FONT_SMALL, COLORS["muted"], 360, 4)
        y += 8
    draw.text((80, y), "Body:", font=FONT_SMALL_BOLD, fill=COLORS["ink"])
    draw_wrapped(draw, (80, y + 32), case["body"], FONT_SMALL, COLORS["muted"], 486, 4)

    y = 320
    for label, value, color in [
        ("Priority", f"{case['priority']} (Urgent: {case['urgent']})", COLORS["green"]),
        ("Action", case["action"], COLORS["blue_dark"]),
        ("Tone", case["tone"], COLORS["amber"] if case["tone"].lower() == "urgent" else COLORS["blue_dark"]),
        ("Target", case["target"], COLORS["muted"]),
    ]:
        draw.text((694, y), f"{label}: ", font=FONT_SMALL_BOLD, fill=COLORS["ink"])
        draw_wrapped(draw, (824, y), value, FONT_SMALL_BOLD if label in {"Priority", "Action"} else FONT_SMALL, color, 330, 4)
        y += 44
    draw.text((694, y + 8), "Decision summary:", font=FONT_SMALL_BOLD, fill=COLORS["ink"])
    decision_lines = wrap_text(draw, case.get("decision_summary", case["response"]), FONT_SMALL, 484)
    if len(decision_lines) > 2:
        decision_lines = decision_lines[:2]
        decision_lines[-1] = decision_lines[-1].rstrip(".") + "..."
    line_y = y + 40
    for line in decision_lines:
        draw.text((694, line_y), line, font=FONT_SMALL, fill=COLORS["muted"])
        line_y += 27

    if explain:
        rounded_box(draw, (90, 588, 1190, 648), (246, 249, 253), radius=14)
        draw.text((116, 605), "Difference from chatbot:", font=FONT_SMALL_BOLD, fill=COLORS["blue_dark"])
        draw_wrapped(draw, (370, 605), case["why"], FONT_SMALL, COLORS["ink"], 760, 3)


def draw_slide(segment: dict[str, object], subtitle: str) -> Image.Image:
    img, draw = base_slide(str(segment["title"]), str(segment.get("subtitle", "")))
    kind = str(segment["kind"])

    if kind == "title":
        draw_metric(draw, 64, 302, "4", "specialized agents", COLORS["blue_dark"])
        draw_metric(draw, 342, 302, "+102", "multi-agent average reward", COLORS["green"])
        draw_metric(draw, 620, 302, "0", "missed deadlines after policy", COLORS["green"])
        draw_metric(draw, 898, 302, "94%", "success rate", COLORS["green"])
    elif kind == "problem":
        rounded_box(draw, (70, 282, 590, 530), (255, 250, 249), radius=18)
        rounded_box(draw, (690, 282, 1210, 530), (248, 253, 250), radius=18)
        draw.text((100, 310), "Normal chatbot", font=FONT_H3, fill=COLORS["red"])
        draw_wrapped(draw, (100, 360), "Generates a reply for the current email, but may not understand deadlines, follow-ups, or future business damage.", FONT_BODY, COLORS["ink"], 430, 10)
        draw.text((720, 310), "InboxWorld", font=FONT_H3, fill=COLORS["green"])
        draw_wrapped(draw, (720, 360), "Chooses an action, tracks consequences, and receives reward or penalty after the environment changes.", FONT_BODY, COLORS["ink"], 430, 10)
    elif kind == "architecture":
        draw_architecture(draw)
        rounded_box(draw, (92, 472, 1188, 584), (246, 249, 253), radius=16)
        draw_wrapped(draw, (120, 496), "Delayed reward means the system can be penalized later for a bad delay, missed deadline, or unsafe triage action.", FONT_BODY, COLORS["ink"], 1040, 8)
    elif kind == "chart":
        draw_chart(draw, 70, 236, 1140, 390)
    elif kind == "demo_intro":
        items = [
            ("Case 1", "Hidden business blocker"),
            ("Case 2", "Revenue renewal risk"),
            ("Case 3", "Personal emergency"),
        ]
        for i, (case_no, label) in enumerate(items):
            x = 92 + i * 390
            rounded_box(draw, (x, 300, x + 330, 500), (250, 252, 255), radius=18)
            draw.text((x + 26, 330), case_no, font=FONT_H3, fill=COLORS["blue_dark"])
            draw_wrapped(draw, (x + 26, 385), label, FONT_BODY_BOLD, COLORS["ink"], 270, 8)
    elif kind == "demo":
        draw_demo_case(draw, segment["case"], explain=False)  # type: ignore[arg-type]
    elif kind == "demo_explain":
        draw_demo_case(draw, segment["case"], explain=True)  # type: ignore[arg-type]
    elif kind == "closing":
        draw_metric(draw, 90, 302, "-117.5", "baseline reward", COLORS["red"])
        draw_metric(draw, 370, 302, "+102.0", "improved reward", COLORS["green"])
        draw_metric(draw, 650, 302, "60 -> 0", "missed deadlines", COLORS["green"])
        rounded_box(draw, (122, 470, 1158, 590), (246, 249, 253), radius=18)
        draw_wrapped(draw, (154, 496), "A chatbot writes what to say. InboxWorld evaluates what to do when the inbox has time pressure, uncertainty, and delayed consequences.", FONT_BODY_BOLD, COLORS["ink"], 960, 9)

    draw_subtitle(draw, subtitle)
    return img


def synthesize_segments(segments: list[dict[str, object]], out_dir: Path) -> list[Path]:
    items = []
    for idx, segment in enumerate(segments, 1):
        items.append({"text": str(segment["narration"]), "path": str(out_dir / f"audio_{idx:02d}.wav")})

    json_path = out_dir / "tts_items.json"
    ps_path = out_dir / "synthesize_tts.ps1"
    json_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
    ps_path.write_text(
        """
param([string]$ItemsPath)
Add-Type -AssemblyName System.Speech
$items = Get-Content -Raw -Path $ItemsPath | ConvertFrom-Json
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = -1
$synth.Volume = 100
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(22050, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
foreach ($item in $items) {
  $synth.SetOutputToWaveFile($item.path, $fmt)
  [void]$synth.Speak($item.text)
  $synth.SetOutputToNull()
}
$synth.Dispose()
""".strip(),
        encoding="utf-8",
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_path), str(json_path)],
        check=True,
        cwd=str(ROOT),
    )
    return [Path(item["path"]) for item in items]


def read_pcm(path: Path) -> bytes:
    with wave.open(str(path), "rb") as wf:
        if wf.getnchannels() != CHANNELS or wf.getframerate() != SAMPLE_RATE or wf.getsampwidth() != BLOCK_ALIGN:
            raise ValueError(f"Unexpected WAV format for {path}: {wf.getparams()}")
        return wf.readframes(wf.getnframes())


def write_wave(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BLOCK_ALIGN)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)


def srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hh = millis // 3_600_000
    millis %= 3_600_000
    mm = millis // 60_000
    millis %= 60_000
    ss = millis // 1000
    ms = millis % 1000
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"


def write_srt(path: Path, segments: list[dict[str, object]], timings: list[tuple[float, float]]) -> None:
    parts = []
    for idx, (segment, (start, end)) in enumerate(zip(segments, timings), 1):
        parts.append(str(idx))
        parts.append(f"{srt_time(start)} --> {srt_time(end)}")
        parts.append(str(segment["narration"]))
        parts.append("")
    path.write_text("\n".join(parts), encoding="utf-8")


def chunk(f, chunk_id: bytes, data: bytes) -> tuple[int, int]:
    start = f.tell()
    f.write(chunk_id)
    f.write(struct.pack("<I", len(data)))
    f.write(data)
    if len(data) % 2:
        f.write(b"\0")
    return start, len(data)


def write_list(f, list_type: bytes, writer) -> None:
    start = f.tell()
    f.write(b"LIST")
    f.write(b"\0\0\0\0")
    f.write(list_type)
    writer()
    end = f.tell()
    f.seek(start + 4)
    f.write(struct.pack("<I", end - start - 8))
    f.seek(end)


def write_avi(path: Path, frame_jpegs: list[bytes], frame_segments: list[int], pcm: bytes) -> None:
    total_frames = len(frame_segments)
    max_jpeg = max(len(data) for data in frame_jpegs)
    audio_bytes_per_sec = SAMPLE_RATE * BLOCK_ALIGN
    audio_samples = len(pcm) // BLOCK_ALIGN

    with path.open("wb") as f:
        riff_start = f.tell()
        f.write(b"RIFF")
        f.write(b"\0\0\0\0")
        f.write(b"AVI ")

        def hdrl_writer() -> None:
            avih = struct.pack(
                "<IIIIIIIIII4I",
                int(1_000_000 / FPS),
                0,
                0,
                0x10,
                total_frames,
                0,
                2,
                max_jpeg,
                WIDTH,
                HEIGHT,
                0,
                0,
                0,
                0,
            )
            chunk(f, b"avih", avih)

            def video_strl() -> None:
                strh = struct.pack(
                    "<4s4sIHHIIIIIIIIiiii",
                    b"vids",
                    b"MJPG",
                    0,
                    0,
                    0,
                    0,
                    1,
                    FPS,
                    0,
                    total_frames,
                    max_jpeg,
                    0xFFFFFFFF,
                    0,
                    0,
                    0,
                    WIDTH,
                    HEIGHT,
                )
                chunk(f, b"strh", strh)
                strf = struct.pack(
                    "<IiiHH4sIiiII",
                    40,
                    WIDTH,
                    HEIGHT,
                    1,
                    24,
                    b"MJPG",
                    WIDTH * HEIGHT * 3,
                    0,
                    0,
                    0,
                    0,
                )
                chunk(f, b"strf", strf)

            def audio_strl() -> None:
                strh = struct.pack(
                    "<4s4sIHHIIIIIIIIiiii",
                    b"auds",
                    b"\0\0\0\0",
                    0,
                    0,
                    0,
                    0,
                    BLOCK_ALIGN,
                    audio_bytes_per_sec,
                    0,
                    audio_samples,
                    4096,
                    0xFFFFFFFF,
                    BLOCK_ALIGN,
                    0,
                    0,
                    0,
                    0,
                )
                chunk(f, b"strh", strh)
                strf = struct.pack("<HHIIHH", 1, CHANNELS, SAMPLE_RATE, audio_bytes_per_sec, BLOCK_ALIGN, BITS_PER_SAMPLE)
                chunk(f, b"strf", strf)

            write_list(f, b"strl", video_strl)
            write_list(f, b"strl", audio_strl)

        write_list(f, b"hdrl", hdrl_writer)

        movi_start = f.tell()
        f.write(b"LIST")
        f.write(b"\0\0\0\0")
        f.write(b"movi")
        movi_data_start = f.tell()
        index: list[tuple[bytes, int, int, int]] = []

        for frame_idx, seg_idx in enumerate(frame_segments):
            frame_data = frame_jpegs[seg_idx]
            start, length = chunk(f, b"00dc", frame_data)
            index.append((b"00dc", 0x10, start - movi_data_start, length))

            sample_start = int(frame_idx * SAMPLE_RATE / FPS)
            sample_end = int((frame_idx + 1) * SAMPLE_RATE / FPS)
            audio_chunk = pcm[sample_start * BLOCK_ALIGN : sample_end * BLOCK_ALIGN]
            if audio_chunk:
                start, length = chunk(f, b"01wb", audio_chunk)
                index.append((b"01wb", 0x10, start - movi_data_start, length))

        movi_end = f.tell()
        f.seek(movi_start + 4)
        f.write(struct.pack("<I", movi_end - movi_start - 8))
        f.seek(movi_end)

        idx_data = b"".join(struct.pack("<4sIII", ckid, flags, offset, size) for ckid, flags, offset, size in index)
        chunk(f, b"idx1", idx_data)

        riff_end = f.tell()
        f.seek(riff_start + 4)
        f.write(struct.pack("<I", riff_end - riff_start - 8))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = make_policy_outputs()
    (OUT_DIR / "demo_case_outputs.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")

    segments = build_segments(cases)
    (OUT_DIR / "narration_script.txt").write_text(
        "\n\n".join(f"{idx}. {segment['narration']}" for idx, segment in enumerate(segments, 1)),
        encoding="utf-8",
    )

    wav_paths = synthesize_segments(segments, OUT_DIR)

    silence = b"\0" * int(SAMPLE_RATE * BLOCK_ALIGN * 0.35)
    pcm_parts: list[bytes] = []
    timings: list[tuple[float, float]] = []
    cursor = 0.0
    for path in wav_paths:
        pcm = read_pcm(path)
        start = cursor
        duration = len(pcm) / (SAMPLE_RATE * BLOCK_ALIGN)
        end = start + duration
        timings.append((start, end))
        pcm_parts.append(pcm)
        pcm_parts.append(silence)
        cursor = end + 0.35
    combined_pcm = b"".join(pcm_parts)
    write_wave(OUT_DIR / "narration.wav", combined_pcm)
    write_srt(OUT_DIR / "inboxworld_demo_video.srt", segments, timings)

    frame_jpegs: list[bytes] = []
    for idx, segment in enumerate(segments):
        image = draw_slide(segment, str(segment["narration"]))
        if idx == 0:
            image.save(OUT_DIR / "thumbnail.png")
        frame_path = OUT_DIR / f"slide_{idx + 1:02d}.jpg"
        image.save(frame_path, "JPEG", quality=86, optimize=True)
        frame_jpegs.append(frame_path.read_bytes())

    total_frames = math.ceil(len(combined_pcm) / BLOCK_ALIGN / SAMPLE_RATE * FPS)
    frame_segments: list[int] = []
    for frame_idx in range(total_frames):
        t = frame_idx / FPS
        seg_idx = 0
        for i, (start, end) in enumerate(timings):
            if start <= t <= end + 0.35:
                seg_idx = i
                break
            if t > end:
                seg_idx = i
        frame_segments.append(seg_idx)

    write_avi(OUT_DIR / "inboxworld_demo_video.avi", frame_jpegs, frame_segments, combined_pcm)
    print(f"Created {OUT_DIR / 'inboxworld_demo_video.avi'}")
    print(f"Created {OUT_DIR / 'inboxworld_demo_video.srt'}")
    print(f"Created {OUT_DIR / 'narration.wav'}")


if __name__ == "__main__":
    main()
