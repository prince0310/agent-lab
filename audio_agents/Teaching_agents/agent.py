"""Teaching Agent — session logic, subject profiles, and tutoring state machine.

This is the brain of the agent. It owns:
  - Subject-specific teaching profiles
  - Solving-mode state machine (pause / resume / hint progression)
  - Prompt generation for each event

live_demo/server.py calls into this; live_demo/live_tools.py owns the
Gemini Live config and system instruction.
"""

from __future__ import annotations

# ── Subject profiles ──────────────────────────────────────────────────────────
# Each entry adds subject-specific guidance appended to the system instruction.

SUBJECT_PROFILES: dict[str, str] = {
    "Mathematics": (
        "Walk through every problem step by step. Verify each arithmetic operation. "
        "When the student shows their work, check every line and point to the exact step "
        "where an error occurred. Draw diagrams or number lines when it helps."
    ),
    "Physics": (
        "Always link formulas to the physical intuition behind them. "
        "Encourage the student to draw free-body diagrams or energy diagrams. "
        "Check units at every step. Relate abstract concepts to everyday examples."
    ),
    "Chemistry": (
        "Balance equations together out loud. Use the periodic table as a reference. "
        "Explain reaction mechanisms with analogies. Emphasize safety rules when relevant."
    ),
    "Biology": (
        "Use real-world analogies for cell processes and systems. "
        "Encourage the student to draw diagrams of structures (cells, organs). "
        "Connect micro-level events to macro-level outcomes."
    ),
    "Computer Science": (
        "Ask the student to trace through their code line by line before revealing bugs. "
        "Use pseudocode to plan before coding. Reinforce Big-O intuition with small examples. "
        "Praise good variable naming and clean structure."
    ),
    "English / Literature": (
        "Focus on comprehension, argument structure, and evidence. "
        "Ask the student to paraphrase passages in their own words first. "
        "Guide essay structure: claim → evidence → analysis → link back."
    ),
    "History": (
        "Frame events as causes and effects. Encourage the student to consider multiple "
        "perspectives. Ask 'why did this happen?' before 'what happened?'."
    ),
    "Geography": (
        "Use maps and spatial reasoning. Ask the student to describe locations relative "
        "to landmarks. Connect physical geography to human patterns."
    ),
    "Economics": (
        "Always ground concepts in real-world markets. Use supply-and-demand diagrams. "
        "Ask the student to give a personal example before explaining the theory."
    ),
    "Art & Music": (
        "Be encouraging and supportive — creative subjects need emotional safety. "
        "Ask the student to describe what they are trying to express, then give technique tips."
    ),
}

DEFAULT_PROFILE = (
    "Teach clearly, patiently, and with encouragement. "
    "Adapt your language to the student's level."
)


# ── Teaching session state ────────────────────────────────────────────────────

class TeachingSession:
    """Tracks per-session state and generates context-aware prompts."""

    def __init__(self, class_name: str, subject: str) -> None:
        self.class_name = class_name
        self.subject = subject
        self.is_solving = False      # True while student is in pause/solve mode
        self.hint_level = 0          # 0 = no hints yet; increments each request
        self.solve_count = 0         # how many times student entered solve mode
        self.questions_asked = 0

    # ── Prompt generators ─────────────────────────────────────────────────────

    def greeting_prompt(self) -> str:
        profile = SUBJECT_PROFILES.get(self.subject, DEFAULT_PROFILE)
        return (
            f"Warmly greet your new student. They are in {self.class_name} studying {self.subject}. "
            f"Ask what they would like to learn today or what doubts they have. "
            f"Remember: {profile}"
        )

    def pause_prompt(self) -> str:
        self.is_solving = True
        self.solve_count += 1
        self.hint_level = 0  # reset hint progression for this problem
        return (
            "[SYSTEM: The student clicked 'I'm Solving Now'. They are working independently. "
            "Stay completely silent. Do not speak or respond until you receive the resume notice.]"
        )

    def resume_prompt(self) -> str:
        self.is_solving = False
        return (
            "[SYSTEM: The student finished solving. They may share their work via camera or file, "
            "or ask a follow-up question. Respond warmly — acknowledge their effort first, "
            "then review their solution if they show it.]"
        )

    def hint_prompt(self) -> str:
        self.hint_level += 1
        level = min(self.hint_level, 3)
        guidance = {
            1: "Give only a conceptual hint — point them toward the right idea without formulas.",
            2: "Give a formula or method hint — name the technique but don't show the steps.",
            3: "Show the first step only — write or say the very first line of the solution, then stop.",
        }
        return (
            f"[HINT REQUEST — level {level}/3: {guidance[level]} "
            f"Do not reveal the full solution.]"
        )

    def document_review_prompt(self) -> str:
        return (
            "I just shared my work with you. Please look at it carefully. "
            "Tell me what I did correctly and point out exactly where I need to improve."
        )

    def subject_profile(self) -> str:
        return SUBJECT_PROFILES.get(self.subject, DEFAULT_PROFILE)
