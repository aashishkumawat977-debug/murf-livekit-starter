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

# Day 8: Call Analytics
from call_analytics_db import record_call

# Day 7: Human Help / Escalation
from escalation_db import create_escalation as db_create_escalation

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

        # Day 8: Call Analytics
        self.exercise_completed = False

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
- For fractions and simple math, prefer natural spoken notation such as "1/4" or "एक-चौथाई" instead of LaTeX such as "$\\frac{1}{4}$".
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

        # Day 7: Human Help / Escalation
        human_help_instruction = """
HUMAN HELP AND ESCALATION RULES:

You are Anisha, a Learning & Literacy voice assistant.

There are TWO situations where you should ask whether the caller wants
human help:

1. The learner explicitly asks for a teacher or human help.
2. The learner is clearly upset or frustrated and needs human support.

Do NOT create a human-help request for a normal learning question
that you can reasonably answer yourself.

IMPORTANT PERMISSION RULE:

Before calling create_escalation, ALWAYS ask the caller for permission.

Tell the caller what information will be shared:

- who needs help
- what happened
- what you already checked
- urgency
- language
- preferred follow-up method

Ask for permission in the caller's language.

For Hindi, say naturally:

"मैं आपकी समस्या और ज़रूरी जानकारी एक teacher को भेज सकती हूँ।
क्या आप इसकी अनुमति देते हैं?"

Then WAIT for the caller's answer.

If the caller clearly says YES:

- Call create_escalation.
- Include only useful information.
- Do not include passwords, OTPs, PINs, account numbers,
  or other private information.
- Give the caller the reference ID returned by the tool.
- Tell the caller that the request is open.
- Explain the next step honestly.
- Never promise an immediate human response unless it is guaranteed.

If the caller says NO:

- Do NOT call create_escalation.
- Do NOT create a request.
- Continue helping the caller normally.

A normal learning conversation MUST NOT create an escalation request.

Examples:

Caller:
"मुझे fractions समझाओ।"

This is normal. Do not escalate.

Caller:
"मुझे teacher से बात करनी है।"

Ask permission before creating an escalation.

Caller:
"मैं बहुत परेशान हूँ और मुझे किसी इंसान से मदद चाहिए।"

Ask permission before creating an escalation.

Always answer Hindi in Devanagari script.
Never romanize Hindi.
"""

        # Day 8: Learning Exercise Completion
        exercise_completion_instruction = """
DAY 8 - LEARNING EXERCISE COMPLETION:

A successful call for the Learning & Literacy track means that the
learner successfully completes a learning exercise.

When you give the learner a learning exercise using the learning
exercise tool:

- Listen to the learner's answer.
- Check whether the learner has actually completed the exercise.
- If the learner gives the correct answer or otherwise successfully
  completes the requested exercise, call mark_exercise_completed.
- Only call mark_exercise_completed after the exercise is actually
  completed successfully.
- Do NOT call it merely because an exercise was requested or provided.
- Do NOT call it when the learner gives an incorrect or incomplete answer.
- If the learner needs another attempt, continue helping them normally.
"""

        super().__init__(
            instructions=(
                SYSTEM_PROMPT
                + memory_context
                + language_instruction
                + memory_permission_instruction
                + human_help_instruction
                + exercise_completion_instruction
            ),
            # Day 5 tool - PRESERVED
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
            "हाँ जी",
            "हां जी",
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

    # =====================================================
    # Day 7: Human Help / Escalation Tool
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
        """
        Create a human-help request only after the caller has
        explicitly given permission to share the necessary information.

        Use this only when:
        1. The learner explicitly needs a teacher/human.
        2. The learner is upset or frustrated and needs human support.

        Never include passwords, OTPs, PINs, account numbers,
        or other private credentials.
        """

        # Day 7 fix:
        # Gemini may provide already_checked as a list,
        # while the database expects a string.
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
            "Created human-help escalation %s for caller %s",
            reference_id,
            self.user_id,
        )

        return (
            f"Human-help request created successfully. "
            f"Reference ID: {reference_id}. "
            f"Status: open."
        )

    # =====================================================
    # DAY 8 - CALL ANALYTICS
    # =====================================================

    @function_tool
    async def mark_exercise_completed(
        self,
        context: RunContext,
    ) -> str:
        """
        Mark the learner's exercise as successfully completed.

        Use this only when the learner has actually completed
        the learning exercise successfully.
        """

        self.exercise_completed = True

        logger.info(
            "Learning exercise completed successfully for caller %s",
            self.user_id,
        )

        return (
            "The learning exercise has been marked as successfully completed."
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
    """Start Anisha Learning & Literacy voice session."""

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
    # Day 8: Create Assistant Instance
    # ---------------------------------------------------------

    assistant = Assistant(
        user_id=user_id,
        memory=caller_memory,
    )

    # ---------------------------------------------------------
    # Day 8: Call Analytics Close Handler
    # ---------------------------------------------------------

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
            "Day 8 call analytics recorded: "
            "call_id=%s user_id=%s outcome=%s",
            ctx.room.name,
            user_id,
            outcome,
        )

    session.on("close", on_session_close)

    # ---------------------------------------------------------
    # Start LiveKit Session
    # ---------------------------------------------------------

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