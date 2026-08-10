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
from memory_db import (
    init_database,
    lookup_caller,
    save_caller as db_save_caller,
)

# Day 5: Learning exercise tool
from day5_tools import get_learning_exercise


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

        language_instruction = """
IMPORTANT LANGUAGE RULE:
Always reply in the same language the caller is using.

- If the caller speaks Hindi, reply completely in Hindi using Devanagari script.
- If the caller speaks English, reply in English.
- If the caller speaks Hinglish, reply naturally in Hinglish.
- Do not switch to English when the caller is speaking Hindi.
- Do not translate a Hindi question into English unless the caller asks.
"""

        memory_permission_instruction = """
PERSISTENT MEMORY PERMISSION RULES — HIGHEST PRIORITY:

When the caller provides NEW personal or learning information that could
be useful in future conversations, you MUST ask for permission to remember
it BEFORE continuing the conversation.

CRITICAL RULE:
The permission question MUST come first.

Example:

Caller:
"मुझे Python function समझने में दिक्कत होती है।"

Your FIRST response MUST be:
"क्या मैं ये जानकारी अगली बार के लिए याद रखूँ?"

Do NOT:

- explain Python
- give an example
- ask another question
- give advice
- say "कोई बात नहीं"
- continue the learning conversation

ONLY ask for permission first.

Then WAIT for the caller's answer.

If the caller says:

- yes
- हाँ
- haan
- याद रखो
- याद रखना
- yes remember
- or clearly agrees

then:

1. Call save_caller_memory with permission="yes".
2. Save the NEW information the caller just provided.
3. Only after the tool succeeds, tell the caller it has been remembered.
4. Then continue the conversation normally.

If the caller says:

- no
- नहीं
- nahi
- don't remember
- or refuses

then:

- Do NOT call save_caller_memory.
- Do NOT save the information.
- Continue the conversation normally.

DIRECT MEMORY REQUEST:
If the caller explicitly says:
"मुझे याद रखो"
"इसे याद रखो"
"याद रखना"
"इसको याद रखना"
or an equivalent direct request,

this is already explicit permission.

In that case:

- Do NOT ask permission again.
- Immediately call save_caller_memory with permission="yes".
- Save the information the caller is asking you to remember.

IMPORTANT:
Never claim information was saved unless save_caller_memory actually
returns successfully.

Existing memory:

- You may read and use existing memory naturally.
- Do not ask permission to use information already stored.
- Do not save existing information again unless the caller provides
  genuinely new information.
- Never invent memories.

Useful information includes:

- caller's name
- preferred language
- learning level
- subjects being studied
- topics being studied
- topics already covered
- recurring learning difficulties
- recurring mistakes

If new useful learning information is provided, ALWAYS ask for permission
before saving it.
"""

        super().__init__(
            instructions=(
                SYSTEM_PROMPT
                + memory_context
                + language_instruction
                + memory_permission_instruction
            ),
            # Day 5 tool
            tools=[get_learning_exercise],
        )

    @function_tool
    async def save_caller_memory(
        self,
        context: RunContext,
        name: str | None = None,
        language_preference: str | None = None,
        facts: dict | None = None,
        permission: str = "no",
    ) -> str:
        """
        Save caller information only after explicit permission.
        """

        approved = permission.strip().lower() in {
            "yes",
            "y",
            "haan",
            "ha",
            "हाँ",
            "हां",
            "हां जी",
            "हाँ जी",
        }

        if not approved:
            logger.info(
                "Caller did not give permission to save memory for %s",
                self.user_id,
            )
            return (
                "Memory was not saved because permission was not given."
            )

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
            "No previous memory found for caller: %s",
            user_id,
        )

    # ---------------------------------------------------------
    # Voice Agent Configuration
    # ---------------------------------------------------------

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        # Anisha voice - locale intentionally not hardcoded.
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2,
            ),
            text_pacing=True,
        ),

        turn_detection=MultilingualModel(),

        vad=ctx.proc.userdata["vad"],

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
# Application Entry Point
# =========================================================

if __name__ == "__main__":
    cli.run_app(server)