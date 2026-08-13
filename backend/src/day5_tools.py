import json
import logging
import os
import random
import re
import urllib.error
import urllib.request

from dotenv import load_dotenv
from livekit.agents import RunContext, function_tool


load_dotenv(".env.local")

logger = logging.getLogger("anisha-learning-exercises")


# =========================================================
# Gemini configuration
# =========================================================

# Confirmed working with the current GOOGLE_API_KEY.
GEMINI_MODEL = "gemini-flash-lite-latest"

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{GEMINI_MODEL}:generateContent"
)


# =========================================================
# Local fallback exercises
# =========================================================

LEARNING_EXERCISES = {
    "3": {
        "math": [
            "What is 25 plus 17?",
            "What is 8 times 4?",
            "What is 36 divided by 6?",
            "What is 15 plus 28?",
            "What is 9 times 5?",
        ],
        "english": [
            "Make a sentence using the word 'school'.",
            "What is the opposite of 'big'?",
            "What is the opposite of 'hot'?",
            "Make a sentence using the word 'friend'.",
            "What is the meaning of the word 'happy'?",
        ],
    },
    "4": {
        "math": [
            "What is 56 divided by 7?",
            "What is 125 plus 238?",
            "What is 9 times 8?",
            "What is 450 minus 175?",
            "What is half of 80?",
        ],
        "english": [
            "Write one sentence about your favorite book.",
            "What is the opposite of 'early'?",
            "What is the meaning of the word 'honest'?",
            "Make a sentence using the word 'beautiful'.",
            "What is the opposite of 'strong'?",
        ],
    },
    "5": {
        "math": [
            "What is 48 divided by 6?",
            "What is 25 percent of 200?",
            "What is 15 times 7?",
            "What is 360 divided by 9?",
            "What is 35 percent of 200?",
        ],
        "english": [
            "What is the meaning of the word 'brave'?",
            "Make a sentence using the word 'knowledge'.",
            "What is the meaning of the word 'curious'?",
            "What is the opposite of 'ancient'?",
            "Make a sentence using the word 'honest'.",
            "What is the meaning of the word 'confident'?",
        ],
    },
}


# =========================================================
# Recent question tracking
# =========================================================

# Keeps recently generated questions separately for every
# level + subject combination.
#
# Example:
# ("5", "math") -> [...]
# ("5", "english") -> [...]
#
_recent_questions: dict[tuple[str, str], list[str]] = {}


# =========================================================
# Question normalization
# =========================================================

def _normalize_question(question: str) -> str:
    """
    Normalize a question for duplicate detection.

    This removes:
    - capitalization differences
    - punctuation differences
    - extra whitespace
    - simple question prefixes

    Example:

        "What is 25 + 10?"
        "what is 25 + 10"

    are treated as the same question.
    """

    normalized = question.strip().lower()

    if normalized.startswith("question:"):
        normalized = normalized[len("question:"):].strip()

    normalized = re.sub(
        r"^\d+\s*[\.\)]\s*",
        "",
        normalized,
    )

    normalized = re.sub(
        r"[^\w\s%]",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


def _is_recent_question(
    question: str,
    recent_questions: list[str],
) -> bool:
    """
    Check whether a question already exists in recent history.

    Uses normalized comparison rather than exact string comparison.
    """

    normalized_question = _normalize_question(question)

    if not normalized_question:
        return True

    for recent in recent_questions:
        if _normalize_question(recent) == normalized_question:
            return True

    return False


# =========================================================
# Recent question helpers
# =========================================================

def _get_recent_questions(
    level: str,
    subject: str,
) -> list[str]:
    """Return recent questions for a level + subject."""

    return _recent_questions.setdefault(
        (level, subject),
        [],
    )


def _remember_question(
    level: str,
    subject: str,
    question: str,
) -> None:
    """Remember a newly generated question."""

    recent = _get_recent_questions(
        level,
        subject,
    )

    recent.append(question)

    # Keep only the latest five questions.
    del recent[:-5]


# =========================================================
# Gemini question generation
# =========================================================

def _generate_question_with_gemini(
    level: str,
    subject: str,
    recent_questions: list[str] | None = None,
) -> str | None:
    """
    Generate a fresh learning question using Gemini REST API.

    Args:
        level:
            Student level.

        subject:
            Learning subject.

        recent_questions:
            Recently generated questions that Gemini must avoid.

    Returns:
        A generated question string, or None if generation fails.
    """

    api_key = (
        os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
    )

    if not api_key:
        logger.warning(
            "No GOOGLE_API_KEY or GEMINI_API_KEY found. "
            "Using local fallback exercises."
        )
        return None

    recent_questions = recent_questions or []

    # -----------------------------------------------------
    # Tell Gemini which questions were recently used.
    # -----------------------------------------------------

    recent_section = ""

    if recent_questions:
        recent_text = "\n".join(
            f"- {question}"
            for question in recent_questions
        )

        recent_section = f"""
Recently used questions:
{recent_text}

IMPORTANT:
- Do NOT repeat any recently used question.
- Do NOT create a question with the same numbers,
  words, structure, or answer pattern as a recently used
  question.
- Create a genuinely different question.
"""

    prompt = f"""
You are creating one short school-level practice question.

Student level: {level}
Subject: {subject}

Rules:
- Generate exactly ONE question.
- It must be appropriate for the student's level.
- It must be suitable for a voice conversation.
- Keep it short and clear.
- Do not provide the answer.
- Do not provide explanations.
- Do not use markdown.
- Do not number the question.
- For English, use vocabulary, grammar, sentence formation,
  comprehension, synonyms, antonyms, or simple usage.
- For Math, use arithmetic, fractions, percentages,
  basic geometry, or age-appropriate word problems.
- Vary the question type and numbers.
- Avoid common repeated examples.
- Never repeat a recently used question.

{recent_section}

Return ONLY the question text.
""".strip()

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 1.0,
            "topP": 0.95,
            "maxOutputTokens": 120,
        },
    }

    try:
        request = urllib.request.Request(
            GEMINI_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        candidates = data.get(
            "candidates",
            [],
        )

        if not candidates:
            logger.warning(
                "Gemini returned no candidates."
            )
            return None

        content = candidates[0].get(
            "content",
            {},
        )

        parts = content.get(
            "parts",
            [],
        )

        if not parts:
            logger.warning(
                "Gemini response contained no text parts."
            )
            return None

        # Gemini can potentially return multiple text parts.
        question_parts = []

        for part in parts:
            text = part.get("text")

            if text:
                question_parts.append(text)

        question = " ".join(
            question_parts
        ).strip()

        if not question:
            logger.warning(
                "Gemini returned an empty question."
            )
            return None

        # -------------------------------------------------
        # Clean accidental formatting.
        # -------------------------------------------------

        question = question.strip(
            " \n\t\"'"
        )

        if question.lower().startswith(
            "question:"
        ):
            question = question[
                len("Question:"):
            ].strip()

        # Remove simple numbering:
        #
        # 1. What is...
        # 1) What is...
        #
        if (
            len(question) >= 3
            and question[0].isdigit()
            and question[1] in {".", ")"}
            and question[2].isspace()
        ):
            question = question[3:].strip()

        # -------------------------------------------------
        # Reject exact/normalized duplicates.
        # -------------------------------------------------

        if _is_recent_question(
            question,
            recent_questions,
        ):
            logger.info(
                "Gemini generated a duplicate recent question."
            )
            return None

        logger.info(
            "Generated fresh Gemini question "
            "for level=%s subject=%s",
            level,
            subject,
        )

        return question

    except urllib.error.HTTPError as error:
        try:
            error_body = error.read().decode(
                "utf-8"
            )
        except Exception:
            error_body = ""

        logger.warning(
            "Gemini HTTP error %s: %s",
            error.code,
            error_body[:1000],
        )

        return None

    except urllib.error.URLError as error:
        logger.warning(
            "Gemini network error: %s",
            error,
        )

        return None

    except Exception as error:
        logger.warning(
            "Gemini question generation failed: %s",
            error,
        )

        return None


# =========================================================
# Local fallback
# =========================================================

def _get_fallback_question(
    level: str,
    subject: str,
) -> str | None:
    """
    Get a randomized local fallback question.

    Avoids recently used questions where possible.
    """

    exercises_for_level = LEARNING_EXERCISES.get(
        level
    )

    if not exercises_for_level:
        return None

    exercises = exercises_for_level.get(
        subject
    )

    if not exercises:
        return None

    recent = _get_recent_questions(
        level,
        subject,
    )

    # -----------------------------------------------------
    # Remove anything that has recently appeared.
    # -----------------------------------------------------

    available = [
        exercise
        for exercise in exercises
        if not _is_recent_question(
            exercise,
            recent,
        )
    ]

    # -----------------------------------------------------
    # If every local question was recently used,
    # start a new fallback cycle.
    # -----------------------------------------------------

    if not available:
        logger.info(
            "All fallback questions for level=%s "
            "subject=%s were recently used. "
            "Starting a new fallback cycle.",
            level,
            subject,
        )

        available = exercises.copy()

    exercise = random.choice(
        available
    )

    _remember_question(
        level,
        subject,
        exercise,
    )

    return exercise


# =========================================================
# Gemini retry helper
# =========================================================

def _generate_fresh_gemini_question(
    level: str,
    subject: str,
) -> str | None:
    """
    Try multiple times to get a genuinely fresh Gemini question.

    Gemini is probabilistic, so one request can occasionally
    produce a duplicate. We retry before falling back locally.
    """

    recent = _get_recent_questions(
        level,
        subject,
    )

    # Try Gemini up to three times.
    for attempt in range(3):
        question = _generate_question_with_gemini(
            level,
            subject,
            recent,
        )

        if not question:
            logger.info(
                "Gemini attempt %s did not produce "
                "a fresh question.",
                attempt + 1,
            )
            continue

        if _is_recent_question(
            question,
            recent,
        ):
            logger.info(
                "Gemini attempt %s produced a duplicate. "
                "Retrying.",
                attempt + 1,
            )
            continue

        _remember_question(
            level,
            subject,
            question,
        )

        return question

    logger.info(
        "Gemini could not produce a fresh question "
        "after three attempts."
    )

    return None


# =========================================================
# Learning Exercise Tool
# =========================================================

@function_tool(
    description=(
        "Use this tool automatically whenever the learner asks for a "
        "practice exercise, quiz question, homework question, or learning "
        "activity for a specific school level and subject. "
        "Use it for subjects such as math or English. "
        "Examples include: 'give me a level 5 math exercise', "
        "'give me a level five English question', "
        "'give me an English question for class 4', "
        "'मुझे level 5 का math question दो', "
        "'मुझे level five का English question दो', "
        "or similar natural requests. "
        "If the learner says a number as a word, such as 'five', "
        "interpret it as the corresponding numeric level. "
        "Generate a fresh question whenever possible. "
        "Do not wait for the learner to explicitly say 'use the tool'. "
        "Do not use this tool for general conversation or unrelated "
        "questions."
    )
)
async def get_learning_exercise(
    context: RunContext,
    level: str,
    subject: str,
) -> str:
    """
    Generate a fresh learning exercise for a school level and subject.

    Gemini is attempted first. Recent questions are supplied to Gemini
    so it can avoid repetition. If Gemini fails repeatedly, the local
    exercise dataset is used as a fallback.
    """

    try:
        normalized_level = level.strip()

        normalized_subject = (
            subject.strip().lower()
        )

        # -------------------------------------------------
        # Validate subject.
        # -------------------------------------------------

        if normalized_subject not in {
            "math",
            "english",
        }:
            return (
                "I currently have Math and English "
                "practice exercises available."
            )

        # -------------------------------------------------
        # Validate level.
        # -------------------------------------------------

        if normalized_level not in LEARNING_EXERCISES:
            return (
                f"I don't have a learning exercise "
                f"available for level {normalized_level} "
                f"right now."
            )

        # -------------------------------------------------
        # First try Gemini with duplicate protection.
        # -------------------------------------------------

        question = _generate_fresh_gemini_question(
            normalized_level,
            normalized_subject,
        )

        # -------------------------------------------------
        # Fallback if Gemini fails.
        # -------------------------------------------------

        if not question:
            logger.info(
                "Using local fallback for level=%s "
                "subject=%s.",
                normalized_level,
                normalized_subject,
            )

            question = _get_fallback_question(
                normalized_level,
                normalized_subject,
            )

        # -------------------------------------------------
        # Nothing available.
        # -------------------------------------------------

        if not question:
            return (
                f"I don't have a "
                f"{normalized_subject} exercise "
                f"available for level "
                f"{normalized_level} right now."
            )

        # -------------------------------------------------
        # Final response.
        # -------------------------------------------------

        return (
            f"Here is a level {normalized_level} "
            f"{normalized_subject} exercise: "
            f"{question}"
        )

    except Exception as error:
        logger.exception(
            "Learning exercise tool failed: %s",
            error,
        )

        return (
            "I couldn't access the learning exercises "
            "right now. Please try again in a moment."
        )