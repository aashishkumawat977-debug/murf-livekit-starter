import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
    tokenize,
)
from livekit.plugins import (
    deepgram,
    google,
    murf,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from prompt import SYSTEM_PROMPT


# =========================================================
# Anisha - Learning & Literacy Voice Assistant
# =========================================================

logger = logging.getLogger("anisha-learning-agent")

load_dotenv(".env.local")


class Assistant(Agent):
    """Anisha - a friendly multilingual learning assistant."""

    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
        )


# =========================================================
# LiveKit Agent Server
# =========================================================

server = AgentServer()


def prewarm(proc: JobProcess):
    """Load the voice activity detector before sessions start."""
    logger.info("Loading Silero VAD...")
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("Silero VAD loaded successfully.")


server.setup_fnc = prewarm


# =========================================================
# Anisha Voice Session
# =========================================================

@server.rtc_session(agent_name="anisha")
async def anisha_agent(ctx: JobContext):
    """Start an Anisha Learning & Literacy voice session."""

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    logger.info("Connecting Anisha to room: %s", ctx.room.name)

    await ctx.connect()

    # ---------------------------------------------------------
    # Voice Agent Configuration
    # ---------------------------------------------------------

    session = AgentSession(
        # Multilingual speech recognition.
        # Detects Hindi, Hinglish, English and other
        # supported languages automatically.
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        # Gemini powers Anisha's educational conversation.
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        # Murf Falcon TTS.
        # Locale is intentionally NOT hardcoded so that
        # multilingual conversations can be handled naturally.
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2,
            ),
            text_pacing=True,
        ),

        # Multilingual turn detection.
        turn_detection=MultilingualModel(),

        # Voice activity detection.
        vad=ctx.proc.userdata["vad"],

        # Start preparing responses before the user has
        # completely finished speaking for faster interaction.
        preemptive_generation=True,
    )

    # ---------------------------------------------------------
    # Start LiveKit Session
    # ---------------------------------------------------------

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    logger.info(
        "Anisha is ready and listening in room: %s",
        ctx.room.name,
    )

    # ---------------------------------------------------------
    # Learning-Focused Welcome
    # ---------------------------------------------------------

    await session.generate_reply(
        instructions=(
            "Give a short and warm welcome as Anisha, "
            "a Learning & Literacy voice assistant. "
            "Speak naturally in Indian Hindi. "
            "Welcome the learner and invite them to ask a "
            "study question, learn a concept, or practice "
            "something they are studying. "
            "Keep the greeting friendly, natural, and concise. "
            "Do not give a long introduction."
        ),
    )


# =========================================================
# Application Entry Point
# =========================================================

if __name__ == "__main__":
    cli.run_app(server)
