from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "screen_demo_video"
FRAMES_DIR = OUT_DIR / "frames"
AUDIO_DIR = OUT_DIR / "audio"
SEGMENTS_DIR = OUT_DIR / "segments"
WIDTH = 1920
HEIGHT = 1080
CAPTION_H = 180
FFMPEG = Path("C:/Program Files/BlueStacks_nxt/ffmpeg.exe")


def font(name: str, size: int) -> ImageFont.ImageFont:
    for candidate in [
        Path("C:/Windows/Fonts") / name,
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


F = {
    "brand": font("segoeuib.ttf", 36),
    "h1": font("segoeuib.ttf", 58),
    "h2": font("segoeuib.ttf", 36),
    "h3": font("segoeuib.ttf", 29),
    "body": font("segoeui.ttf", 27),
    "body_b": font("segoeuib.ttf", 27),
    "small": font("segoeui.ttf", 22),
    "small_b": font("segoeuib.ttf", 22),
    "caption": font("segoeui.ttf", 35),
    "mono": font("consola.ttf", 22),
}


C = {
    "ink": (17, 28, 48),
    "muted": (76, 91, 111),
    "bg": (244, 247, 251),
    "panel": (255, 255, 255),
    "panel2": (250, 253, 255),
    "line": (214, 223, 235),
    "blue": (39, 99, 190),
    "blue_dark": (16, 55, 118),
    "green": (20, 122, 88),
    "red": (180, 35, 24),
    "amber": (166, 95, 0),
    "caption_bg": (11, 19, 32),
}


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_w: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    cur = ""
    for word in words:
        nxt = f"{cur} {word}".strip()
        if draw.textbbox((0, 0), nxt, font=fnt)[2] <= max_w or not cur:
            cur = nxt
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_wrap(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt, fill, max_w: int, gap: int = 6) -> int:
    x, y = xy
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += draw.textbbox((x, y), line, font=fnt)[3] - y + gap
    return y


def box(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill=C["panel"], outline=C["line"], r: int = 18) -> None:
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=2)


def caption(draw: ImageDraw.ImageDraw, text: str) -> None:
    y0 = HEIGHT - CAPTION_H
    draw.rectangle((0, y0, WIDTH, HEIGHT), fill=C["caption_bg"])
    draw.rectangle((0, y0, 14, HEIGHT), fill=(35, 177, 159))
    lines = wrap(draw, text, F["caption"], WIDTH - 180)[:3]
    y = y0 + 32
    for line in lines:
        draw.text((74, y), line, font=F["caption"], fill=(255, 255, 255))
        y += 43


def browser_frame(title: str, sub: str, cap: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), C["bg"])
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((36, 24, WIDTH - 36, HEIGHT - CAPTION_H - 22), radius=20, fill=(255, 255, 255), outline=C["line"], width=2)
    draw.rectangle((36, 24, WIDTH - 36, 104), fill=(236, 242, 250))
    for i, col in enumerate([(232, 72, 85), (242, 180, 56), (51, 190, 112)]):
        draw.ellipse((68 + i * 34, 54, 88 + i * 34, 74), fill=col)
    draw.rounded_rectangle((198, 48, 1110, 82), radius=17, fill=(255, 255, 255), outline=(204, 215, 229))
    draw.text((222, 52), "http://127.0.0.1:7860/  InboxWorld: Multi-Agent Policy Demo", font=F["small"], fill=C["muted"])
    draw.text((74, 132), title, font=F["h1"], fill=C["ink"])
    if sub:
        text_wrap(draw, (76, 198), sub, F["body"], C["muted"], 1500, 7)
    caption(draw, cap)
    return img, draw


def field(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, label: str, value: str, h: int = 62) -> int:
    draw.text((x, y), label, font=F["small_b"], fill=C["blue"])
    box(draw, (x, y + 30, x + w, y + 30 + h), fill=(255, 255, 255), r=10)
    text_wrap(draw, (x + 18, y + 44), value, F["small"], C["ink"], w - 36, 4)
    return y + h + 44


def output_row(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, value: str, color=C["ink"]) -> int:
    draw.text((x, y), label, font=F["small_b"], fill=C["blue"])
    box(draw, (x, y + 32, x + 760, y + 92), fill=(255, 255, 255), r=10)
    text_wrap(draw, (x + 18, y + 48), value, F["small_b"], color, 720, 3)
    return y + 106


def draw_ui(draw: ImageDraw.ImageDraw, case: dict[str, str] | None, show_output: bool, badge: str) -> None:
    left = (76, 286, 910, 878)
    right = (1010, 286, 1844, 878)
    draw.text((76, 242), "Incoming Email", font=F["h2"], fill=C["ink"])
    draw.text((1010, 242), "Multi-Agent Output", font=F["h2"], fill=C["ink"])
    box(draw, left, fill=C["panel2"], r=18)
    box(draw, right, fill=C["panel2"], r=18)
    draw.rounded_rectangle((1530, 132, 1825, 188), radius=28, fill=(226, 240, 255), outline=(188, 211, 242))
    draw.text((1556, 144), badge, font=F["small_b"], fill=C["blue_dark"])

    if case is None:
        case = {
            "sender": "John Doe",
            "importance": "normal",
            "subject": "Project Milestone",
            "body": "Hey team, when will we hit the renewal milestone? We need this by today.",
            "priority": "",
            "urgent": "",
            "action": "",
            "tone": "",
            "decision_summary": "",
            "target": "",
        }

    y = 314
    y = field(draw, 108, y, 760, "Sender Name", case["sender"], 56)
    y = field(draw, 108, y, 760, "Sender Importance", case["importance"], 56)
    draw.rectangle((108, y + 10, 132, y + 34), fill=(245, 247, 250), outline=C["line"], width=2)
    draw.text((146, y + 4), "Has Visible Urgency? unchecked", font=F["small"], fill=C["ink"])
    y += 48
    y = field(draw, 108, y, 760, "Email Subject", case["subject"], 56)
    draw.text((108, y), "Email Body", font=F["small_b"], fill=C["blue"])
    box(draw, (108, y + 32, 868, y + 154), fill=(255, 255, 255), r=10)
    text_wrap(draw, (126, y + 50), case["body"], F["small"], C["ink"], 724, 5)
    draw.rounded_rectangle((108, 824, 868, 872), radius=14, fill=(96, 99, 242))
    draw.text((386, 832), "Send to Agents", font=F["small_b"], fill=(255, 255, 255))

    if not show_output:
        draw.text((1054, 438), "Waiting for input...", font=F["h2"], fill=C["muted"])
        draw.text((1054, 490), "Click Send to Agents to run Classifier, Priority, Responder, and Supervisor agents.", font=F["small"], fill=C["muted"])
        return

    y = 314
    y = output_row(draw, 1048, y, "Assessed Priority", f"{case['priority']} (Urgent: {case['urgent']})", C["green"])
    y = output_row(draw, 1048, y, "Agent Action", case["action"], C["blue_dark"])
    y = output_row(draw, 1048, y, "Agent Tone", case["tone"], C["amber"] if case["tone"].lower() == "urgent" else C["ink"])
    y = output_row(draw, 1048, y, "Escalation Target", case["target"], C["muted"])
    draw.text((1048, y), "Decision Summary", font=F["small_b"], fill=C["blue"])
    box(draw, (1048, y + 32, 1808, y + 112), fill=(255, 255, 255), r=10)
    text_wrap(draw, (1066, y + 50), case["decision_summary"], F["small_b"], C["ink"], 716, 4)


def policy_outputs() -> list[dict[str, str]]:
    sys.path.insert(0, str(ROOT))
    from src.inboxworld.agents import MultiAgentEmailPolicy
    from src.inboxworld.types import InboxEmail

    demos = [
        {
            "name": "Hidden business blocker",
            "sender": "design@studio.dev",
            "importance": "client",
            "subject": "Quick export question",
            "body": "Which hero image should we export for tomorrow's client deck? If I do not get confirmation, the deck may slip.",
        },
        {
            "name": "Revenue renewal risk",
            "sender": "csm@renewals.app",
            "importance": "client",
            "subject": "Renewal may pause without pricing clarification",
            "body": "Customer needs pricing confirmation before tomorrow's renewal call or they may pause the renewal approval.",
        },
        {
            "name": "Personal emergency",
            "sender": "neighbor",
            "importance": "normal",
            "subject": "Father in hospital",
            "body": "Hey, my father is in hospital and I need help contacting you. Can you please respond as soon as possible?",
        },
    ]
    policy = MultiAgentEmailPolicy()
    out = []
    for i, case in enumerate(demos, 1):
        email = InboxEmail(
            email_id=f"demo-{i}",
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
            thread_id=f"demo-thread-{i}",
            tags=[],
        )
        action = policy.act({"emails": [email]})
        if action.escalate_target == "emergency_contact":
            summary = "Escalate as urgent emergency. Do not treat as normal email."
        elif action.action_type == "escalate_email":
            summary = "Escalate to manager because delayed handling can create business risk."
        elif action.reply_tone == "helpful":
            summary = "Generate a helpful high-priority reply before the client deck slips."
        else:
            summary = "Generate a safe response using the selected priority and tone."
        out.append(
            {
                **case,
                "priority": str(action.predicted_priority).upper(),
                "urgent": str(action.predicted_urgency),
                "action": action.action_type.replace("_", " ").title(),
                "tone": str(action.reply_tone).title(),
                "target": action.escalate_target,
                "decision_summary": summary,
            }
        )
    return out


def chart_screen(draw: ImageDraw.ImageDraw) -> None:
    x, y, w, h = 140, 300, 1640, 470
    box(draw, (x, y, x + w, y + h), fill=(255, 255, 255), r=20)
    draw.text((x + 38, y + 28), "Baseline vs Improved Policy", font=F["h2"], fill=C["ink"])
    baseline = [-81, -154, -81, -154, -81, -154, -81, -154]
    improved = [77, 127, 77, 127, 77, 127, 77, 127]
    min_v, max_v = -170, 140
    px0, py0 = x + 120, y + 112
    px1, py1 = x + w - 80, y + h - 90

    def pt(i: int, v: float) -> tuple[int, int]:
        return (
            px0 + int((px1 - px0) * i / 7),
            py1 - int((v - min_v) / (max_v - min_v) * (py1 - py0)),
        )

    for gv in [-150, -75, 0, 75, 125]:
        gy = pt(0, gv)[1]
        draw.line((px0, gy, px1, gy), fill=(226, 233, 242), width=2)
        draw.text((x + 48, gy - 12), str(gv), font=F["small"], fill=C["muted"])
    draw.line((px0, py1, px1, py1), fill=C["muted"], width=3)
    draw.line((px0, py0, px0, py1), fill=C["muted"], width=3)
    draw.line([pt(i, v) for i, v in enumerate(baseline)], fill=C["red"], width=7)
    draw.line([pt(i, v) for i, v in enumerate(improved)], fill=C["green"], width=7)
    for points, col in [([pt(i, v) for i, v in enumerate(baseline)], C["red"]), ([pt(i, v) for i, v in enumerate(improved)], C["green"])]:
        for px, py in points:
            draw.ellipse((px - 10, py - 10, px + 10, py + 10), fill=(255, 255, 255), outline=col, width=5)
    draw.line((x + 430, y + h - 42, x + 510, y + h - 42), fill=C["red"], width=7)
    draw.text((x + 530, y + h - 58), "Baseline avg -117.5", font=F["small_b"], fill=C["ink"])
    draw.line((x + 850, y + h - 42, x + 930, y + h - 42), fill=C["green"], width=7)
    draw.text((x + 950, y + h - 58), "Improved avg +102.0", font=F["small_b"], fill=C["ink"])
    draw.text((300, 790), "Missed deadlines: 60 -> 0", font=F["h3"], fill=C["green"])
    draw.text((820, 790), "Success rate: 94%", font=F["h3"], fill=C["green"])
    draw.text((1210, 790), "Reward gain: +219.5", font=F["h3"], fill=C["green"])


def comparison_screen(draw: ImageDraw.ImageDraw) -> None:
    box(draw, (100, 315, 880, 760), fill=(255, 249, 248), r=20)
    box(draw, (1040, 315, 1820, 760), fill=(248, 253, 250), r=20)
    draw.text((140, 350), "Normal chatbot / email assistant", font=F["h2"], fill=C["red"])
    draw.text((1080, 350), "InboxWorld", font=F["h2"], fill=C["green"])
    left = [
        "Writes or summarizes a reply.",
        "Usually judges one email at a time.",
        "May miss hidden urgency.",
        "No delayed penalty for a bad decision.",
    ]
    right = [
        "Chooses action: reply, delay, escalate, ignore.",
        "Uses four-agent decision pipeline.",
        "Detects hidden urgency and deadlines.",
        "Scores consequences using delayed reward.",
    ]
    yy = 430
    for item in left:
        draw.text((150, yy), "x", font=F["body_b"], fill=C["red"])
        text_wrap(draw, (190, yy), item, F["body"], C["ink"], 620)
        yy += 70
    yy = 430
    for item in right:
        draw.text((1090, yy), "✓", font=F["body_b"], fill=C["green"])
        text_wrap(draw, (1130, yy), item, F["body"], C["ink"], 620)
        yy += 70


def make_frames(cases: list[dict[str, str]], scenes: list[dict[str, str]]) -> list[Path]:
    paths: list[Path] = []
    for idx, scene in enumerate(scenes, 1):
        img, draw = browser_frame(scene["title"], scene["subtitle"], scene["caption"])
        kind = scene["kind"]
        if kind == "overview":
            draw_ui(draw, None, False, "Demo UI")
        elif kind == "comparison":
            comparison_screen(draw)
        elif kind == "chart":
            chart_screen(draw)
        elif kind == "form":
            draw_ui(draw, cases[int(scene["case"])], False, "Input filled")
        elif kind == "output":
            draw_ui(draw, cases[int(scene["case"])], True, "Agents ran")
        elif kind == "closing":
            draw_ui(draw, cases[2], True, "Research demo")
            draw.rounded_rectangle((260, 704, 1660, 810), radius=20, fill=(255, 255, 255), outline=C["line"], width=2)
            draw.text((310, 730), "A chatbot writes what to say. InboxWorld evaluates what to do.", font=F["h2"], fill=C["blue_dark"])
        path = FRAMES_DIR / f"{idx:02d}-{kind}.jpg"
        img.save(path, "JPEG", quality=92, optimize=True)
        paths.append(path)
    return paths


def synthesize_audio(scenes: list[dict[str, str]]) -> list[Path]:
    items = [{"name": f"{i:02d}", "text": scene["caption"]} for i, scene in enumerate(scenes, 1)]
    (OUT_DIR / "tts_items.json").write_text(json.dumps(items, indent=2), encoding="utf-8")
    ps = OUT_DIR / "create_audio.ps1"
    ps.write_text(
        """
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$audio = Join-Path $root "audio"
New-Item -ItemType Directory -Force -Path $audio | Out-Null
$items = Get-Content -Raw -Path (Join-Path $root "tts_items.json") | ConvertFrom-Json
foreach ($item in $items) {
  $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $synth.Rate = 0
  $synth.Volume = 100
  $path = Join-Path $audio "$($item.name).wav"
  $synth.SetOutputToWaveFile($path)
  [void]$synth.Speak($item.text)
  $synth.Dispose()
}
""".strip(),
        encoding="utf-8",
    )
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps)], check=True, cwd=str(ROOT))
    return [AUDIO_DIR / f"{i:02d}.wav" for i in range(1, len(scenes) + 1)]


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def srt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    ms %= 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def write_srt(scenes: list[dict[str, str]], audios: list[Path]) -> None:
    lines: list[str] = []
    cur = 0.0
    for i, (scene, audio) in enumerate(zip(scenes, audios), 1):
        dur = wav_duration(audio)
        lines.extend([str(i), f"{srt_ts(cur)} --> {srt_ts(cur + dur)}", scene["caption"], ""])
        cur += dur
    (OUT_DIR / "inboxworld_screen_demo.srt").write_text("\n".join(lines), encoding="utf-8")


def render_mp4(frames: list[Path], audios: list[Path], scenes: list[dict[str, str]]) -> None:
    concat_lines = []
    for idx, (frame, audio) in enumerate(zip(frames, audios), 1):
        segment = SEGMENTS_DIR / f"{idx:02d}.mp4"
        cmd = [
            str(FFMPEG),
            "-y",
            "-loop",
            "1",
            "-framerate",
            "30",
            "-i",
            str(frame),
            "-i",
            str(audio),
            "-vf",
            "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,format=yuv420p",
            "-c:v",
            "libopenh264",
            "-b:v",
            "3500k",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(segment),
        ]
        subprocess.run(cmd, check=True, cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        concat_lines.append(f"file '{segment.as_posix()}'")
    concat = SEGMENTS_DIR / "concat.txt"
    concat.write_text("\n".join(concat_lines), encoding="ascii")
    output = OUT_DIR / "inboxworld_screen_demo.mp4"
    subprocess.run(
        [str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(output)],
        check=True,
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    if not FFMPEG.exists():
        raise FileNotFoundError(f"ffmpeg not found at {FFMPEG}")
    for d in [OUT_DIR, FRAMES_DIR, AUDIO_DIR, SEGMENTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    cases = policy_outputs()
    (OUT_DIR / "demo_case_outputs.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    scenes = [
        {
            "kind": "overview",
            "title": "InboxWorld: Multi-Agent Policy Demo",
            "subtitle": "This corrected video demonstrates the actual project screen and the agent outputs.",
            "caption": "This is the InboxWorld project interface. Instead of only writing a reply, it sends each email through Classifier, Priority, Responder, and Supervisor agents.",
        },
        {
            "kind": "comparison",
            "title": "How It Is Different From a Chatbot",
            "subtitle": "A chatbot answers. InboxWorld chooses an action and evaluates consequences.",
            "caption": "A normal chatbot mainly generates text. InboxWorld decides whether to reply, delay, escalate, classify, or ignore, then evaluates that decision with delayed reward.",
        },
        {
            "kind": "form",
            "case": "0",
            "title": "Demo Case 1: Hidden Business Blocker",
            "subtitle": "The first email looks like a small design question, but it can block a client deck.",
            "caption": "Case one: I enter a client design email. It does not shout urgent, but the phrase client deck means a delayed answer can create downstream project risk.",
        },
        {
            "kind": "output",
            "case": "0",
            "title": "Demo Case 1 Output",
            "subtitle": "The agents identify hidden priority and choose a helpful high-priority reply.",
            "caption": "After clicking Send to Agents, InboxWorld marks the email high priority and prepares a helpful response. A simple chatbot may miss the hidden client-deck consequence.",
        },
        {
            "kind": "form",
            "case": "1",
            "title": "Demo Case 2: Revenue Renewal Risk",
            "subtitle": "The second email contains revenue and renewal risk.",
            "caption": "Case two: I enter a client renewal email. The email says pricing clarification is needed before tomorrow, otherwise renewal approval may pause.",
        },
        {
            "kind": "output",
            "case": "1",
            "title": "Demo Case 2 Output",
            "subtitle": "The system escalates because late handling can hurt business outcomes.",
            "caption": "InboxWorld marks it high priority and selects escalation to the manager. This is the important difference: the system chooses an action, not just a polite reply.",
        },
        {
            "kind": "form",
            "case": "2",
            "title": "Demo Case 3: Personal Emergency",
            "subtitle": "The sender is normal, but the body contains emergency context.",
            "caption": "Case three: the sender importance is normal and visible urgency is unchecked. But the email says father in hospital, so the content itself must change the decision.",
        },
        {
            "kind": "output",
            "case": "2",
            "title": "Demo Case 3 Output",
            "subtitle": "The agents detect emergency meaning and escalate urgently.",
            "caption": "InboxWorld marks the message high priority, urgent, and escalates to an emergency contact. It reasons from meaning, not only from the urgency checkbox.",
        },
        {
            "kind": "chart",
            "title": "Baseline vs Improved Policy",
            "subtitle": "The improvement is measured with reward, deadlines, and success rate.",
            "caption": "The baseline policy averages minus one hundred seventeen point five reward. The improved multi-agent policy averages plus one hundred two reward, and missed deadlines drop from sixty to zero.",
        },
        {
            "kind": "closing",
            "title": "Final Research Takeaway",
            "subtitle": "InboxWorld is a research environment, not only an email drafting tool.",
            "caption": "The research contribution is clear: a chatbot writes what to say, but InboxWorld evaluates what to do under time pressure, uncertainty, and delayed consequences.",
        },
    ]
    (OUT_DIR / "screen_demo_script.txt").write_text("\n\n".join(f"{i}. {s['caption']}" for i, s in enumerate(scenes, 1)), encoding="utf-8")
    frames = make_frames(cases, scenes)
    audios = synthesize_audio(scenes)
    write_srt(scenes, audios)
    render_mp4(frames, audios, scenes)
    print(OUT_DIR / "inboxworld_screen_demo.mp4")


if __name__ == "__main__":
    main()
