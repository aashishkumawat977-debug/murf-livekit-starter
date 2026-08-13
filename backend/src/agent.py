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
from math_specialist import MathSpecialistAgent

from memory_db import (
    init_database,
    lookup_caller,
    save_caller as db_save_caller,
)

# Day 8
from call_analytics_db import record_call

# Day 7
from escalation_db import create_escalation as db_create_escalation

# Day 5
from day5_tools import get_learning_exercise


# =========================================================
# Anisha
# =========================================================

logger = logging.getLogger("anisha-learning-agent")

load_dotenv(".env.local")


class Assistant(Agent):
    """
    Anisha - Learning & Literacy Voice Assistant.

    Maths is handled by Khyati.
    """

    def __init__(
        self,
        user_id: str,
        memory: dict | None = None,
    ) -> None:

        self.user_id = user_id
        self.memory = memory

        # Day 8
        self.exercise_completed = False

        # Day 9
        self.math_transfer_completed = False

        # =================================================
        # Persistent memory
        # =================================================

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

        # =================================================
        # Language
        # =================================================

        language_instruction = """
IMPORTANT LANGUAGE RULE:

Always reply in the same language the caller is using.

- Hindi -> Hindi in Devanagari.
- English -> English.
- Hinglish -> natural Hinglish.

Do not unnecessarily switch languages.

For mathematics, use natural spoken notation.
Avoid LaTeX.
"""

        # =================================================
        # Memory permission
        # =================================================

        memory_permission_instruction = """
PERSISTENT MEMORY PERMISSION RULES:

When the caller provides NEW personal or learning information
that could be useful in future conversations, ask permission
before saving it.

If the caller explicitly asks to remember something:

- Do not ask permission again.
- Save it immediately with permission="yes".

Never claim something was saved unless the tool succeeds.

Existing memory can be used naturally.

Do not save existing information again unless genuinely new.
"""

        # =================================================
        # Human help
        # =================================================

        human_help_instruction = """
HUMAN HELP RULES:

Ask whether the caller wants human help when:

1. They explicitly ask for a teacher or human.
2. They are clearly upset and need human support.

Before creating escalation, ALWAYS ask permission.

Do not escalate normal learning questions.
"""

        # =================================================
        # Exercise completion
        # =================================================

        exercise_completion_instruction = """
DAY 8 - LEARNING EXERCISE COMPLETION:

A successful call means the learner successfully completes
a learning exercise.

Only mark the exercise completed after the learner actually
answers it successfully.
"""

        # =================================================
        # Day 9 - Maths handoff
        # =================================================

        specialist_handoff_instruction = """
DAY 9 - KHYATI MATHS SPECIALIST

You are Anisha, the main Learning & Literacy assistant.

When the learner clearly asks for mathematics:

YOU MUST call:

transfer_to_math_specialist

Examples:

- maths practice
- math practice
- मुझे maths practice करनी है
- fractions समझाओ
- percentage समझाओ
- algebra practice
- geometry समझाओ
- maths question solve करो
- 3/4 + 1/4 कितना है?

IMPORTANT:

Do NOT solve mathematics yourself.

Do NOT answer mathematics yourself.

Do NOT create a maths problem yourself.

Transfer to Khyati.

After the transfer succeeds:

STOP ACTING AS ANISHA.

Do not generate another reply after the transfer tool call.

Do not say anything after the transfer is complete.

The transfer tool itself speaks the SINGLE handoff sentence.

Never say Khyati's introduction.

Never say:

"नमस्ते! मैं Khyati हूँ..."

Never say:

"मैं Khyati हूँ..."

Never ask the learner to say "ok".

The learner must NOT repeat the maths request.

Khyati automatically continues from the preserved conversation.

IMPORTANT:

The learner should NOT need to say "ok" after the handoff.

Khyati starts the maths practice automatically.
"""

        # =================================================
        # Register Anisha
        # =================================================

        super().__init__(
            instructions=(
                SYSTEM_PROMPT
                + memory_context
                + language_instruction
                + memory_permission_instruction
                + human_help_instruction
                + exercise_completion_instruction
                + specialist_handoff_instruction
            ),
            tools=[
                get_learning_exercise,
            ],
        )

    # =====================================================
    # Persistent Memory
    # =====================================================

    @function_tool
    async def save_caller_memory(
        self,
        context: RunContext,
        name: str | None = None,
        language_preference: str | None = None,
        facts: dict | None = None,
        permission: str = "no",
    ) -> str:

        approved = permission.strip().lower() in {
            "yes",
            "y",
            "haan",
            "ha",
            "हाँ",
            "हां",
            "हाँ जी",
            "हां जी",
        }

        if not approved:
            logger.info(
                "Memory permission denied for caller %s",
                self.user_id,
            )

            return "Memory was not saved because permission was not given."

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

    # =====================================================
    # Human Help
    # =====================================================

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        who_needs_help: str,
        problem: str,
        already_checked: str | list[str],
        urgency: str,
        language: str,
        preferred_followup: str,
    ) -> str:

        if isinstance(already_checked, list):
            already_checked = " ".join(already_checked)

        reference_id = db_create_escalation(
            who_needs_help=who_needs_help,
            problem=problem,
            already_checked=already_checked,
            urgency=urgency,
            language=language,
            preferred_followup=preferred_followup,
        )

        logger.info(
            "Created escalation %s for caller %s",
            reference_id,
            self.user_id,
        )

        return (
            f"Human-help request created successfully. "
            f"Reference ID: {reference_id}. "
            f"Status: open."
        )

    # =====================================================
    # Day 8
    # =====================================================

    @function_tool
    async def mark_exercise_completed(
        self,
        context: RunContext,
    ) -> str:

        self.exercise_completed = True

        logger.info(
            "Learning exercise completed for caller %s",
            self.user_id,
        )

        return (
            "The learning exercise has been marked as successfully completed."
        )

    # =====================================================
    # Day 9 - Maths Specialist Transfer
    # =====================================================

    @function_tool
    async def transfer_to_math_specialist(
        self,
        context: RunContext,
    ) -> tuple[Agent, str]:
        """
        Transfer from Anisha to Khyati.

        Flow:

        1. Anisha speaks ONE handoff sentence.
        2. Khyati becomes active.
        3. Khyati automatically starts maths.
        4. No "ok" required.
        5. Anisha does not speak again.
        """

        # -------------------------------------------------
        # Prevent duplicate transfer
        # -------------------------------------------------

        if self.math_transfer_completed:
            logger.warning(
                "Duplicate maths transfer blocked for caller %s",
                self.user_id,
            )

            return self, ""

        self.math_transfer_completed = True

        logger.info(
            "Transferring caller %s to Khyati",
            self.user_id,
        )

        # -------------------------------------------------
        # Preserve COMPLETE conversation context
        # -------------------------------------------------

        specialist_chat_ctx = self.chat_ctx.copy(
            exclude_instructions=True,
        )

        # -------------------------------------------------
        # Create Khyati
        # -------------------------------------------------

        specialist = MathSpecialistAgent(
            chat_ctx=specialist_chat_ctx,
        )

        logger.info(
            "Khyati created for caller %s",
            self.user_id,
        )

        # -------------------------------------------------
        # SINGLE ANISHA HANDOFF
        # -------------------------------------------------

        await self.session.say(
            "ठीक है, मैं आपको Maths Specialist Khyati के पास transfer कर रही हूँ।",
            allow_interruptions=False,
        )

        # -------------------------------------------------
        # Return Khyati
        #
        # Empty message is intentional.
        # Khyati's on_enter() handles her own first response.
        # -------------------------------------------------

        return specialist, ""


# =========================================================
# LiveKit Server
# =========================================================

server = AgentServer()


# =========================================================
# Prewarm
# =========================================================

def prewarm(proc: JobProcess):

    logger.info("Loading Silero VAD...")

    proc.userdata["vad"] = silero.VAD.load()

    logger.info("Silero VAD loaded successfully.")


server.setup_fnc = prewarm


# =========================================================
# Anisha Session
# =========================================================

@server.rtc_session(agent_name="anisha")
async def anisha_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    logger.info(
        "Connecting Anisha to room: %s",
        ctx.room.name,
    )

    await ctx.connect()

    # =====================================================
    # Persistent memory
    # =====================================================

    init_database()

    participant = await ctx.wait_for_participant()

    user_id = participant.identity

    logger.info(
        "Caller connected: %s",
        user_id,
    )

    caller_memory = lookup_caller(user_id)

    if caller_memory:
        logger.info(
            "Found existing memory for caller: %s",
            user_id,
        )
    else:
        logger.info(
            "No previous memory for caller: %s",
            user_id,
        )

    # =====================================================
    # Agent Session
    # =====================================================

    session = AgentSession(

        # -------------------------------------------------
        # STT
        # -------------------------------------------------

        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        # -------------------------------------------------
        # LLM
        # -------------------------------------------------

        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        # -------------------------------------------------
        # Anisha TTS
        # -------------------------------------------------

        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2,
            ),
            text_pacing=True,
        ),

        # -------------------------------------------------
        # Turn Detection
        # -------------------------------------------------

        turn_detection=MultilingualModel(),

        # -------------------------------------------------
        # VAD
        # -------------------------------------------------

        vad=ctx.proc.userdata["vad"],

        # -------------------------------------------------
        # Preemptive generation
        # -------------------------------------------------

        preemptive_generation=True,
    )

    # =====================================================
    # Create Anisha
    # =====================================================

    assistant = Assistant(
        user_id=user_id,
        memory=caller_memory,
    )

    # =====================================================
    # Day 8 Analytics
    # =====================================================

    def on_session_close(event):

        outcome = (
            "success"
            if assistant.exercise_completed
            else "failed"
        )

        record_call(
            call_id=ctx.room.name,
            user_id=user_id,
            outcome=outcome,
        )

        logger.info(
            "Call analytics recorded: "
            "call_id=%s user_id=%s outcome=%s",
            ctx.room.name,
            user_id,
            outcome,
        )

    session.on("close", on_session_close)

    # =====================================================
    # Start
    # =====================================================

    await session.start(
        agent=assistant,
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
        "Anisha ready in room: %s",
        ctx.room.name,
    )

    # =====================================================
    # Welcome
    # =====================================================

    if caller_memory and caller_memory.get("name"):

        name = caller_memory.get("name")

        welcome = (
            f"नमस्ते {name}! वापस स्वागत है। "
            "आज क्या पढ़ना या अभ्यास करना है?"
        )

    else:

        welcome = (
            "नमस्ते! मैं अनिशा हूँ, आपकी Learning & Literacy assistant। "
            "आज क्या पढ़ना या अभ्यास करना है?"
        )

    await session.say(
        welcome,
        allow_interruptions=False,
    )


# =========================================================
# Application Entry
# =========================================================

if __name__ == "__main__":
    cli.run_app(server)