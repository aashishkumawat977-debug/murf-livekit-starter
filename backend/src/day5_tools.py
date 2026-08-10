from livekit.agents import RunContext, function_tool


LEARNING_EXERCISES = {
    "3": {
        "math": [
            "What is 25 plus 17?",
            "What is 8 times 4?",
        ],
        "english": [
            "Make a sentence using the word 'school'.",
            "What is the opposite of 'big'?",
        ],
    },
    "4": {
        "math": [
            "What is 56 divided by 7?",
            "What is 125 plus 238?",
        ],
        "english": [
            "Write one sentence about your favorite book.",
            "What is the opposite of 'early'?",
        ],
    },
    "5": {
        "math": [
            "What is 48 divided by 6?",
            "What is 25 percent of 200?",
        ],
        "english": [
            "What is the meaning of the word 'brave'?",
            "Make a sentence using the word 'knowledge'.",
        ],
    },
}


@function_tool(
    description=(
        "Use this tool automatically whenever the learner asks for a "
        "practice exercise, quiz question, homework question, or learning "
        "activity for a specific school level and subject. "
        "Use it for subjects such as math or English. "
        "Examples include: 'give me a level 5 math exercise', "
        "'मुझे लेवल 5 का math exercise दो', "
        "'मुझे level five का math question दो', "
        "'give me an English question for class 4', "
        "or similar natural requests. "
        "If the learner says a number as a word, such as 'five', "
        "interpret it as the corresponding numeric level, such as '5'. "
        "Do not wait for the learner to explicitly say 'use the learning "
        "tool'. Call this tool when the learner is clearly requesting "
        "a specific learning exercise. "
        "Do not use this tool for general conversation or questions "
        "that are unrelated to learning exercises."
    )
)
async def get_learning_exercise(
    context: RunContext,
    level: str,
    subject: str,
) -> str:
    """
    Get a learning exercise for a school level and subject.

    The dataset is local and was created for the Learning & Literacy
    track. It is not a live external API.
    """

    try:
        normalized_level = level.strip()
        normalized_subject = subject.strip().lower()

        exercises_for_level = LEARNING_EXERCISES.get(normalized_level)

        if not exercises_for_level:
            return (
                f"I don't have a learning exercise available for level "
                f"{normalized_level} right now."
            )

        exercises = exercises_for_level.get(normalized_subject)

        if not exercises:
            return (
                f"I don't have a {normalized_subject} exercise available "
                f"for level {normalized_level} right now."
            )

        exercise = exercises[0]

        return (
            f"Here is a level {normalized_level} {normalized_subject} "
            f"exercise: {exercise}"
        )

    except Exception:
        return (
            "I couldn't access the learning exercises right now. "
            "Please try again in a moment."
        )