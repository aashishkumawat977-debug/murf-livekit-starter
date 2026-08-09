import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
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
from memory_db import init_database, lookup_caller, save_caller as db_save_caller

# =========================================================
# Anisha - Learning & Literacy Voice Assistant
# =========================================================

logger = logging.getLogger("anisha-learning-agent")

load_dotenv(".env.local")


class Assistant(Agent):
    """Anisha - a friendly multilingual learning assistant."""

    def __init__(
        self,
        user_id: str,
        memory: dict | None = None,
    ) -> None:
        self.user_id = user_id
        self.memory = memory

        memory_context = ""

        if memory:
            memory_context = (
                "\n\nPERSISTENT CALLER MEMORY:\n"
                f"Name: {memory.get('name') or 'Unknown'}\n"
                f"Language preference: "
                f"{memory.get('language_preference') or 'Unknown'}\n"
                f"Known facts: {memory.get('facts') or {}}\n\n"
                "Use this memory naturally when helpful. "
                "Do not claim to remember information that is not "
                "present in this memory."
            )
        else:
            memory_context = (
                "\n\nPERSISTENT CALLER MEMORY:\n"
                "No previous memory was found for this caller. "
                "Treat this as a first interaction and do not "
                "invent any previous information."
            )

        super().__init__(
            instructions=SYSTEM_PROMPT + memory_context,
        )

    @function_tool
    async def save_caller_memory(
        self,
        context: RunContext,
        name: str | None = None,
        language_preference: str | None = None,
        facts: dict | None = None,
    ) -> str:
        """
        Save caller information when the caller explicitly shares it.
        Only save information relevant to future learning conversations.
        """

        memory = db_save_caller(
            user_id=self.user_id,
            name=name,
            language_preference=language_preference,
            facts=facts or {},
        )

        self.memory = memory

        logger.info(
            "Saved persistent memory for caller %s",
            self.user_id,
        )

        return "Caller memory saved successfully."


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

    logger.info(
        "Connecting Anisha to room: %s",
        ctx.room.name,
    )

    await ctx.connect()

    # ---------------------------------------------------------
    # Persistent Memory
    # ---------------------------------------------------------

    init_database()

    # Wait for the human participant to join.
    participant = await ctx.wait_for_participant()
    user_id = participant.identity

    logger.info(
        "Caller connected: %s",
        user_id,
    )

    # Load memory for this caller.
    caller_memory = lookup_caller(user_id)

    if caller_memory:
        logger.info(
            "Found existing memory for caller: %s",
            user_id,
        )
    else:
        logger.info(
            "No previous memory found for caller: %s",
            user_id,
        )

    # ---------------------------------------------------------
    # Voice Agent Configuration
    # ---------------------------------------------------------

    session = AgentSession(
        # Multilingual speech recognition.
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        # Gemini powers Anisha's educational conversation.
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        # Murf Falcon TTS.
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

        # Faster response generation.
        preemptive_generation=True,
    )

    # ---------------------------------------------------------
    # Start LiveKit Session
    # ---------------------------------------------------------

    await session.start(
        agent=Assistant(
            user_id=user_id,
            memory=caller_memory,
        ),
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

    if caller_memory and caller_memory.get("name"):
        welcome = (
            f"Welcome back, {caller_memory['name']}! "
            "Main Anisha hoon, aapki Learning & Literacy assistant. "
            "Aaj kya padhna ya practice karna hai?"
        )
    else:
        welcome = (
            "Give a short and warm welcome as Anisha, "
            "a Learning & Literacy voice assistant. "
            "Speak naturally in Indian Hindi. "
            "Welcome the learner and invite them to ask a "
            "study question, learn a concept, or practice "
            "something they are studying. "
            "Keep the greeting friendly, natural, and concise. "
            "Do not give a long introduction."
        )

    await session.generate_reply(
        instructions=welcome,
    )


# =========================================================
# Application Entry Point
# =========================================================

if __name__ == "__main__":
    cli.run_app(server)