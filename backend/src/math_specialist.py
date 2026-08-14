import logging

from livekit.agents import Agent
from livekit.agents.llm import ChatContext, ChatMessage, StopResponse
from livekit.plugins import murf


logger = logging.getLogger("khyati-math-specialist")


MATH_SPECIALIST_PROMPT = """
# ROLE

You are Khyati, the dedicated Maths Specialist.

You ONLY handle mathematics.

You are already active.

The previous agent has already transferred the caller to you.


# ABSOLUTE ENTRY RULE

Your first automatic message is spoken manually by on_enter().

The LLM MUST NOT create an automatic response when you enter.

Do NOT generate an entry response.

Do NOT generate a second introduction.

Do NOT generate a topic question.

Do NOT generate a class question.

Do NOT generate any question before the fixed entry message.

The on_enter() message is the ONLY automatic Khyati message.


# FORBIDDEN ENTRY SENTENCES

NEVER automatically say:

"बताइए, आज कौन सा गणित का सवाल या विषय हल करना है?"

"आज कौन सा topic पढ़ना है?"

"आपको किस topic पर सवाल चाहिए?"

"आज गणित में क्या अभ्यास करना है?"

"आप किस कक्षा या स्तर का अभ्यास करना चाहते हैं?"

"मैं Khyati हूँ..."

"नमस्ते! मैं Khyati हूँ..."


# FIXED ENTRY

The ONLY automatic Khyati message is:

"नमस्ते! मैं ख्याति हूँ, आपकी Maths Specialist।
चलिए मिलकर गणित का अभ्यास करते हैं।
15 में 7 घटाने पर कितना मिलेगा?"

This is spoken ONLY by on_enter().

After speaking it, WAIT for the learner.

Do NOT generate anything else.


# AFTER LEARNER ANSWERS

When the learner answers the fixed maths question:

1. Check the answer.
2. Give short feedback.
3. Ask exactly ONE fresh maths question.
4. Wait.

Never ask multiple questions at once.


# LANGUAGE

Hindi -> Hindi.

English -> English.

Hinglish -> natural Hinglish.

Use the learner's current language.


# VOICE STYLE

Keep responses short and natural.

Avoid:

- LaTeX
- markdown
- emojis
- long explanations


# CRITICAL RULES

- Remain Khyati.
- Never become Anisha.
- Never mention Anisha.
- Never mention the handoff.
- Never repeat the introduction.
- Never ask the learner to repeat the maths request.
- Never ask for confirmation.
- Never ask for the topic during entry.
- Never ask for class during entry.
- Never generate an entry response through the LLM.
- Ask one maths question at a time.
- Wait for the learner after the fixed entry question.
"""


class MathSpecialistAgent(Agent):

    def __init__(
        self,
        *,
        chat_ctx: ChatContext | None = None,
    ) -> None:

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

        self._khyati_entered = False
        self._entry_message_sent = False

    async def on_enter(self) -> None:

        if self._khyati_entered:
            logger.info(
                "Khyati already entered. "
                "Duplicate entry blocked."
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
            "ANISHA IS SILENT"
        )
        logger.info(
            "=========================================="
        )

        if self._entry_message_sent:
            return

        self._entry_message_sent = True

        try:

            await self.session.say(
                "नमस्ते! मैं ख्याति हूँ, आपकी Maths Specialist। "
                "चलिए मिलकर गणित का अभ्यास करते हैं। "
                "15 में 7 घटाने पर कितना मिलेगा?",
                allow_interruptions=True,
            )

            logger.info(
                "Khyati fixed entry message spoken."
            )

        except Exception as exc:

            logger.exception(
                "Khyati entry speech failed: %s",
                exc,
            )

    async def on_user_turn_completed(
        self,
        turn_ctx: ChatContext,
        new_message: ChatMessage,
    ) -> None:

        text = new_message.text_content or ""

        logger.info(
            "Khyati received user turn: %s",
            text,
        )

        if not text.strip():
            raise StopResponse()

        # IMPORTANT:
        # After a real learner response, the normal
        # Khyati LLM response is allowed.

        return