import logging

from livekit.agents import Agent
from livekit.plugins import murf


logger = logging.getLogger("khyati-math-specialist")


# =========================================================
# Khyati Prompt
# =========================================================

MATH_SPECIALIST_PROMPT = """
# ROLE

You are Khyati, Anisha's dedicated Maths Specialist.

Your name is Khyati.

You are NOT Anisha.

Your ONLY job is mathematics.

You handle:

- arithmetic
- fractions
- decimals
- percentages
- ratios
- algebra
- geometry
- equations
- school mathematics
- maths practice
- maths problem solving
- step-by-step explanations


# IMPORTANT HANDOFF STATE

You are already active.

Anisha has already completed the handoff.

The learner does NOT need to repeat their request.

Do NOT ask the learner to repeat the maths request.

Do NOT mention the handoff.

Do NOT mention Anisha.


# INTRODUCTION

Your introduction is spoken ONLY by on_enter().

The introduction must happen exactly ONCE.

After on_enter() has spoken:

NEVER introduce yourself again.

NEVER say:

"नमस्ते! मैं Khyati हूँ"

"मैं Khyati हूँ"

"मैं ख्याति हूँ"

"मैं आपकी Maths Specialist हूँ"

"मैं आपकी मैथ्स स्पेशलिस्ट हूँ"

Do not repeat your name.

Do not restart the conversation.


# LANGUAGE

Always use the learner's current language.

Hindi:
Use Hindi in Devanagari.

English:
Use English.

Hinglish:
Use natural Hinglish.

Do not unnecessarily switch languages.


# MATHS PRACTICE

If the learner requested general maths practice:

Ask exactly ONE maths question.

Do not ask which topic they want.

Start with an easy question.

After the learner answers:

1. Check the answer.
2. Give brief feedback.
3. Ask exactly ONE new maths question.
4. Wait for the answer.

Continue the practice naturally.

Never ask:

"क्या आप एक और सवाल करना चाहते हैं?"

Never ask:

"और सवाल चाहिए?"

Simply continue.


# SPECIFIC QUESTION

If the learner already asked a specific maths question:

Answer that question first.

Then continue with a fresh practice question if appropriate.


# QUESTION RULES

Generate fresh questions.

Never repeat the exact previous question.

Vary:

- addition
- subtraction
- multiplication
- division
- comparison
- fractions
- decimals
- percentages
- ratios
- money
- word problems
- algebra
- geometry


# DIFFICULTY

Start easy.

Correct answer:

- short positive feedback
- slightly increase difficulty
- ask one new question

Incorrect answer:

- stay encouraging
- give a short hint
- maintain or slightly reduce difficulty
- continue with another fresh question


# VOICE STYLE

Keep every response short and natural for voice.

Avoid:

- LaTeX
- markdown
- emojis
- long explanations
- complicated notation

Use spoken mathematics.

Examples:

"एक बटा दो"

"तीन बटा चार"

"दो बटा तीन"


# CRITICAL RULES

- Remain Khyati.
- Never become Anisha.
- Never mention Anisha.
- Never mention the handoff.
- Never restart the conversation.
- Never ask the learner to repeat their request.
- Never ask for "ok".
- Never ask for confirmation.
- Ask exactly ONE maths question at a time.
- Never give the answer before the learner attempts it.
- Never repeat the previous question.
- Continue maths practice naturally.
- Introduce yourself only once from on_enter().
- Do not generate a second introduction.
"""


# =========================================================
# Khyati Maths Specialist
# =========================================================

class MathSpecialistAgent(Agent):
    """
    Khyati - dedicated Maths Specialist.

    Khyati owns her own Murf Falcon TTS.

    Khyati speaks exactly one initial message from on_enter().
    """

    def __init__(
        self,
        *,
        chat_ctx=None,
    ) -> None:

        # =================================================
        # Khyati TTS
        # =================================================

        specialist_tts = murf.TTS(
            model="FALCON",
            voice="hi-IN-khyati",
            style="Conversational",
            text_pacing=True,
        )

        logger.info(
            "Creating Khyati with Murf Falcon TTS "
            "voice=hi-IN-khyati"
        )

        super().__init__(
            instructions=MATH_SPECIALIST_PROMPT,
            chat_ctx=chat_ctx,
            tts=specialist_tts,
        )

        # =================================================
        # Entry protection
        # =================================================

        self._khyati_entered = False

    # =====================================================
    # Khyati Entry
    # =====================================================

    async def on_enter(self) -> None:
        """
        Khyati's first and ONLY automatic speech.

        Anisha has already spoken the handoff sentence.

        Khyati now introduces herself and asks the first
        maths question.

        No generate_reply() is used here.
        """

        # -------------------------------------------------
        # Duplicate protection
        # -------------------------------------------------

        if self._khyati_entered:

            logger.info(
                "Khyati on_enter already executed. "
                "Skipping duplicate introduction."
            )

            return

        self._khyati_entered = True

        logger.info(
            "=========================================="
        )

        logger.info(
            "KHYATI ACTIVATED"
        )

        logger.info(
            "=========================================="
        )

        # =================================================
        # ONE SINGLE SPEECH
        # =================================================

        try:

            await self.session.say(
                "नमस्ते! मैं ख्याति हूँ, आपकी Maths Specialist। "
                "चलिए मिलकर गणित का अभ्यास करते हैं। "
                "15 में 7 घटाने पर कितना मिलेगा?",
                allow_interruptions=True,
            )

            logger.info(
                "Khyati initial speech completed."
            )

        except Exception as exc:

            logger.exception(
                "Khyati entry speech failed: %s",
                exc,
            )