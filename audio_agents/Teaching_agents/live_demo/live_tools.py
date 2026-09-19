"""Gemini Live configuration and tool contracts for the Teaching Agent."""

from __future__ import annotations

import os
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

LIVE_MODEL_ID: str = os.getenv("TEACHING_LIVE_MODEL", "gemini-3.8-live")
VOICE_NAME: str    = os.getenv("TEACHING_VOICE", "Kore")
LANGUAGE_CODE: str = os.getenv("TEACHING_LANGUAGE", "en-IN")

# ── System instruction ────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """\
You are an expert, patient, and encouraging teacher running a live voice tutoring session.
The student's class level and subject are injected at session start.

Core teaching behaviour
- Greet the student warmly and ask what they'd like to learn or clarify today
- Prefer the Socratic method: guide with questions rather than handing over answers
- Keep voice responses conversational — you are speaking, not writing essays
- When you pose a problem, tell the student they can click "I'm Solving" to work alone
- When you receive [SYSTEM: student is solving], go completely silent and wait patiently
- When you receive [SYSTEM: student finished solving], respond warmly and check their work

Whiteboard (draw_on_board tool)
- You have a draw_on_board tool that displays a diagram on the student's screen.
- USE IT PROACTIVELY whenever a visual would help: triangles, graphs, number lines, diagrams,
  coordinate planes, Venn diagrams, circuits, molecular structures, timelines, etc.
- Coordinate space: x 0–100 (left→right), y 0–100 (top→bottom). Canvas is square.
- DRAW FIRST, then explain verbally what you drew — say "I've drawn this on the board for you".
- Common examples:
    Right triangle: triangle x1=15 y1=80, x2=75 y2=80, x3=15 y3=20; label1="A", label2="B", label3="C"; add angle_mark at the right angle; add text labels for sides.
    Coordinate axes: use type="axes" then plot points with type="point".
    Circle with radius: type="circle" cx=50 cy=50 r=30.
    Number line: a horizontal line with tick marks as short vertical lines and labels.
- Always give the diagram a clear title.

Visual feedback (camera and documents)
- When the student shares their paper or shows the camera, describe exactly what you see
- Give line-by-line feedback: "Step 2 is correct; in Step 3 I see X which should be Y"

Hint protocol (when [HINT REQUEST] arrives)
- Level 1: conceptual hint only — point to the right idea, no formulas
- Level 2: name the formula or method, but don't show steps
- Level 3: show the first step only, then stop

Safety and trust
- Never give the full answer outright on the first try
- If the student is visibly frustrated, acknowledge their feeling before continuing

Speaking style
- Short, natural sentences — you're talking, not lecturing
- Celebrate small wins: "Nice, that's exactly right!"
- Correct mistakes gently: "Almost — let me show you what to look for…"
""".strip()


def _draw_board_tool(types):
    """Build the draw_on_board FunctionDeclaration."""
    shape_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "type": types.Schema(
                type=types.Type.STRING,
                description=(
                    "Shape type. One of: line, triangle, circle, rectangle, "
                    "text, arrow, point, axes, angle_mark"
                ),
            ),
            # Coordinates (0-100 space)
            "x":  types.Schema(type=types.Type.NUMBER, description="x centre / start / left"),
            "y":  types.Schema(type=types.Type.NUMBER, description="y centre / start / top"),
            "x1": types.Schema(type=types.Type.NUMBER),
            "y1": types.Schema(type=types.Type.NUMBER),
            "x2": types.Schema(type=types.Type.NUMBER),
            "y2": types.Schema(type=types.Type.NUMBER),
            "x3": types.Schema(type=types.Type.NUMBER, description="Third vertex (triangle)"),
            "y3": types.Schema(type=types.Type.NUMBER),
            "r":  types.Schema(type=types.Type.NUMBER, description="Radius (circle)"),
            "width":  types.Schema(type=types.Type.NUMBER),
            "height": types.Schema(type=types.Type.NUMBER),
            # Styling
            "color":     types.Schema(type=types.Type.STRING, description="CSS colour, default chalk-white"),
            "fill":      types.Schema(type=types.Type.STRING, description="Fill colour, or 'none'"),
            "dashed":    types.Schema(type=types.Type.BOOLEAN),
            "thickness": types.Schema(type=types.Type.NUMBER, description="Stroke width, default 2"),
            # Labels / text
            "text":   types.Schema(type=types.Type.STRING, description="Text content (text shapes)"),
            "label":  types.Schema(type=types.Type.STRING, description="Label near the shape centre"),
            "label1": types.Schema(type=types.Type.STRING, description="Label near first vertex (triangle)"),
            "label2": types.Schema(type=types.Type.STRING, description="Label near second vertex"),
            "label3": types.Schema(type=types.Type.STRING, description="Label near third vertex"),
            "size":   types.Schema(type=types.Type.NUMBER, description="Font size for text/labels"),
        },
        required=["type"],
    )

    return types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="draw_on_board",
            description=(
                "Draw a diagram on the student's whiteboard. "
                "Use this whenever a visual aid would help understanding. "
                "Coordinates are 0-100 for both x and y (0,0 = top-left, 100,100 = bottom-right)."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "title": types.Schema(type=types.Type.STRING, description="Diagram title shown above the board"),
                    "shapes": types.Schema(
                        type=types.Type.ARRAY,
                        description="Ordered list of shapes to draw",
                        items=shape_schema,
                    ),
                },
                required=["shapes"],
            ),
        )
    ])


def build_live_config(class_name: str, subject: str):
    """Return a LiveConnectConfig for a teaching session."""
    from google.genai import types

    from agent import SUBJECT_PROFILES, DEFAULT_PROFILE
    profile = SUBJECT_PROFILES.get(subject, DEFAULT_PROFILE)

    preamble = (
        f"Student class: {class_name}\n"
        f"Subject: {subject}\n"
        f"Subject-specific guidance: {profile}\n\n"
    )

    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
            ),
            language_code=LANGUAGE_CODE,
        ),
        system_instruction=types.Content(
            parts=[types.Part(text=preamble + SYSTEM_INSTRUCTION)]
        ),
        tools=[_draw_board_tool(types)],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )
