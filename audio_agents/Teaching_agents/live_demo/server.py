"""Teaching Agent — FastAPI WebSocket transport.

Owns: browser session management, Gemini Live audio/video stream,
      transcript routing, and FastAPI routes.

Teaching session state → agent.py
Gemini Live config      → live_tools.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
LIVE_DIR = Path(__file__).resolve().parent       # live_demo/
AGENT_DIR = LIVE_DIR.parent                       # Teaching_agents/
STATIC_DIR = AGENT_DIR / "static"

for p in (str(AGENT_DIR), str(LIVE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Env ───────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(AGENT_DIR / ".env")

# ── Imports ───────────────────────────────────────────────────────────────────
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agent import TeachingSession
from live_tools import build_live_config, LIVE_MODEL_ID

# ── App ───────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Teaching Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    return {"status": "ok", "model": LIVE_MODEL_ID, "has_api_key": bool(key)}


def _get_client():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Set GOOGLE_API_KEY in your .env file.")
    from google import genai
    return genai.Client(api_key=key)


# ── WebSocket session ─────────────────────────────────────────────────────────

@app.websocket("/ws")
async def teaching_ws(ws: WebSocket):
    await ws.accept()
    logger.info("Browser connected")

    # 1. Receive session config from browser
    try:
        init = await asyncio.wait_for(ws.receive_json(), timeout=15.0)
    except asyncio.TimeoutError:
        await ws.close(code=1008, reason="Config timeout")
        return

    class_name = init.get("class", "High School (Grade 9–12)")
    subject    = init.get("subject", "Mathematics")

    # 2. Create teaching session (state machine)
    session = TeachingSession(class_name, subject)

    # 3. Connect to Gemini API
    try:
        client = _get_client()
    except ValueError as exc:
        await ws.send_json({"type": "error", "message": str(exc)})
        await ws.close()
        return

    config = build_live_config(class_name, subject)

    from google.genai import types as gt

    async def _send_text(live, text: str) -> None:
        """Send a text turn to Gemini and signal end-of-turn."""
        await live.send_client_content(
            turns=gt.Content(role="user", parts=[gt.Part(text=text)]),
            turn_complete=True,
        )

    try:
        async with client.aio.live.connect(model=LIVE_MODEL_ID, config=config) as live:
            logger.info("Gemini Live connected  class=%s  subject=%s", class_name, subject)
            await ws.send_json({"type": "connected", "class": class_name, "subject": subject})

            # Kick off the greeting
            await _send_text(live, session.greeting_prompt())

            # ── Browser → Gemini ──────────────────────────────────────────────
            async def from_browser():
                try:
                    while True:
                        try:
                            raw = await ws.receive_text()
                        except WebSocketDisconnect:
                            return

                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        t = msg.get("type", "")

                        # Camera video frame (JPEG)
                        if t == "video_frame":
                            try:
                                frame = base64.b64decode(msg["data"])
                                await live.send_realtime_input(
                                    video=gt.Blob(data=frame, mime_type="image/jpeg")
                                )
                            except Exception as exc:
                                logger.debug("video frame: %s", exc)

                        # Document / paper shared by student
                        elif t == "document":
                            try:
                                doc  = base64.b64decode(msg["data"])
                                mime = msg.get("mime_type", "image/jpeg")
                                await live.send_realtime_input(
                                    video=gt.Blob(data=doc, mime_type=mime)
                                )
                                await asyncio.sleep(0.1)
                                await _send_text(live, session.document_review_prompt())
                            except Exception as exc:
                                logger.warning("document send: %s", exc)

                        # Typed text message
                        elif t == "text":
                            text = msg.get("text", "").strip()
                            if text:
                                await _send_text(live, text)

                        # Web Speech API end-of-utterance — send transcript as Gemini turn
                        elif t == "speech_end":
                            text = msg.get("text", "").strip()
                            if text:
                                await _send_text(live, text)
                                logger.info("speech_end → Gemini: %s", text[:80])

                        # Student enters solving mode
                        elif t == "pause":
                            await _send_text(live, session.pause_prompt())
                            await ws.send_json({"type": "status", "paused": True})

                        # Student finished solving
                        elif t == "resume":
                            await _send_text(live, session.resume_prompt())
                            await ws.send_json({"type": "status", "paused": False})

                        # Hint request
                        elif t == "hint":
                            await _send_text(live, session.hint_prompt())

                        # Quick-action buttons
                        elif t == "quick_action":
                            action = msg.get("action", "")
                            prompts = {
                                "explain_again": "Please explain that concept again in a completely different way.",
                                "example":       "Give me a different worked example for this concept.",
                                "practice":      "Give me a new practice problem to try on my own.",
                                "ask_me":        "Ask me a question to test my understanding of what we just covered.",
                                "stuck":         "[SYSTEM: Student is stuck and frustrated. Encourage them warmly, then give a level-1 hint.]",
                            }
                            text = prompts.get(action, action)
                            if text:
                                await _send_text(live, text)

                except Exception as exc:
                    logger.info("from_browser ended: %s", exc)

            # ── Gemini → Browser ──────────────────────────────────────────────
            async def from_gemini():
                try:
                    while True:
                        turn = live.receive()
                        async for response in turn:

                            # ── Tool calls (e.g. draw_on_board) ──────────────
                            if response.tool_call and response.tool_call.function_calls:
                                for fc in response.tool_call.function_calls:
                                    if fc.name == "draw_on_board":
                                        args = dict(fc.args or {})
                                        await ws.send_json({
                                            "type": "board",
                                            "title": args.get("title", "Diagram"),
                                            "shapes": args.get("shapes", []),
                                        })
                                        logger.info("draw_on_board: %d shapes, title=%s",
                                                    len(args.get("shapes", [])), args.get("title"))
                                    # Send tool response back so Gemini continues speaking
                                    await live.send_tool_response(function_responses=[
                                        gt.FunctionResponse(
                                            id=fc.id,
                                            name=fc.name,
                                            response={"drawn": True},
                                        )
                                    ])

                            sc = response.server_content
                            if not sc:
                                continue

                            # Model audio chunks
                            if sc.model_turn:
                                for part in sc.model_turn.parts or []:
                                    if part.inline_data and isinstance(part.inline_data.data, bytes):
                                        if "audio" in (part.inline_data.mime_type or "") and not session.is_solving:
                                            b64 = base64.b64encode(part.inline_data.data).decode()
                                            await ws.send_json({"type": "audio", "data": b64,
                                                                "mime_type": part.inline_data.mime_type})
                                    elif part.text and part.text.strip():
                                        await ws.send_json({"type": "transcript", "speaker": "agent",
                                                            "text": part.text.strip()})

                            # Input transcription (what student said)
                            if sc.input_transcription and sc.input_transcription.text:
                                await ws.send_json({"type": "transcript", "speaker": "user",
                                                    "text": sc.input_transcription.text})

                            # Output transcription (text form of teacher audio)
                            if sc.output_transcription and sc.output_transcription.text:
                                await ws.send_json({"type": "transcript", "speaker": "agent",
                                                    "text": sc.output_transcription.text})

                            if getattr(sc, "interrupted", False):
                                await ws.send_json({"type": "interrupted"})

                            if getattr(sc, "turn_complete", False):
                                await ws.send_json({"type": "turn_complete"})

                except Exception as exc:
                    logger.info("from_gemini ended: %s", exc)

            t1 = asyncio.create_task(from_browser())
            t2 = asyncio.create_task(from_gemini())
            try:
                await asyncio.gather(t1, t2)
            finally:
                t1.cancel()
                t2.cancel()

    except Exception as exc:
        logger.error("Session error: %s", exc)
        try:
            await ws.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass

    logger.info("Session closed")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
