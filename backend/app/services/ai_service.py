from datetime import datetime, timedelta
from app.services.memory_relevance import get_relevant_memories
from sqlalchemy.orm import Session
from app.services.context_engine import (
    build_academic_context,
)


class ProfPilotAI:

    def query(
        self,
        message: str,
        db: Session,
        course_id: str | None = None,
        lecturer_id: str = "lecturer_001",
    ) -> dict:

        message_lower = message.lower()


        # --------------------------------
        # BUILD REAL ACADEMIC CONTEXT
        # --------------------------------

        context = build_academic_context(
            db=db,
            lecturer_id=lecturer_id,
            course_id=course_id,
        )

        course = context["selected_course"]

        memories = get_relevant_memories(
            db=db,
            query=message,
            lecturer_id=lecturer_id,
            course_id=course_id,
            limit=5,
        )
        memory_lines = []

        for memory in memories:
            memory_lines.append(
                f"- {memory.title}: {memory.summary}"
            )

        memory_context = "\n".join(memory_lines)

        if not memory_context:
            memory_context = "No relevant academic memories found."
        # --------------------------------
        # COURSE FINISH PREDICTION
        # --------------------------------

        if (
            "when" in message_lower
            and (
                "finish" in message_lower
                or "complete" in message_lower
            )
        ):

            if not course:
                return {
                    "type": "error",
                    "answer":
                        "I couldn't find a course "
                        "to analyse.",
                }

            gap = (
                course["planned_progress"]
                - course["progress"]
            )

            if gap > 0:
                status = (
                    f"{gap:.0f}% behind the "
                    "planned pace"
                )
            else:
                status = "on or ahead of schedule"

            return {
                "type": "prediction",

                "answer": (
                    f"Your {course['name']} is "
                    f"currently {course['progress']:.0f}% "
                    f"complete and is {status}. "
                    f"At the current teaching pace, "
                    f"the estimated completion date is "
                    f"{course['predicted_completion']}."
                ),

                "data": {
                    "course":
                        course["short_name"],

                    "progress":
                        course["progress"],

                    "planned_progress":
                        course["planned_progress"],

                    "current_pace":
                        course["current_pace"],

                    "required_pace":
                        course["required_pace"],

                    "predicted_completion":
                        course["predicted_completion"],
                },

                "confidence": 0.88,
            }


        # --------------------------------
        # WHAT IF CANCEL
        # --------------------------------

        if (
            "what if" in message_lower
            and "cancel" in message_lower
        ):

            if not course:
                return {
                    "type": "error",
                    "answer":
                        "I couldn't determine which "
                        "course you mean.",
                }


            # --------------------------------
            # TEMPORARY RULE-ASSISTED MODEL
            # --------------------------------
            #
            # This is NOT our final prediction
            # model.
            #
            # The real ML forecasting model will
            # replace this later.
            # --------------------------------

            if (
                course["current_pace"]
                < course["required_pace"]
            ):
                delay_days = 3

            else:
                delay_days = 1


            current_date = datetime.strptime(
                course["predicted_completion"],
                "%d %B %Y",
            )

            new_date = (
                current_date
                + timedelta(days=delay_days)
            )


            return {
                "type": "what_if",

                "answer": (
                    f"If you cancel the next "
                    f"{course['short_name']} class, "
                    f"the current model estimates a "
                    f"delay of approximately "
                    f"{delay_days} days. "
                    f"The predicted completion would "
                    f"shift from "
                    f"{course['predicted_completion']} "
                    f"to "
                    f"{new_date.day} {new_date.strftime('%B %Y')}"
                ),

                "data": {
                    "course":
                        course["short_name"],

                    "original_completion":
                        course[
                            "predicted_completion"
                        ],

                    "simulated_completion":
                        f"{new_date.day} {new_date.strftime('%B %Y')}",

                    "delay_days":
                        delay_days,
                },

                "confidence": 0.81,

                "requires_confirmation": True,
            }


        # --------------------------------
        # NEXT CLASS
        # --------------------------------

        if (
            "next class" in message_lower
            or "next lecture" in message_lower
        ):

            next_class = (
                context["next_class"]
            )

            if not next_class:
                return {
                    "type": "schedule",
                    "answer":
                        "You have no classes "
                        "scheduled.",
                    "confidence": 0.98,
                }


            return {
                "type": "schedule",

                "answer": (
                    f"Your next class is "
                    f"{next_class['subject']} "
                    f"for {next_class['batch']} "
                    f"at {next_class['time']} "
                    f"{next_class['period']} "
                    f"in {next_class['room']}."
                ),

                "data": next_class,

                "confidence": 0.98,
            }


        # --------------------------------
        # WHAT DID I TEACH?
        # --------------------------------

        if (
            "what did i teach" in message_lower
            or "last lecture" in message_lower
            or "previous lecture" in message_lower
        ):

            lectures = context[
                "recent_lectures"
            ]

            if not lectures:
                return {
                    "type": "lecture_history",
                    "answer":
                        "I don't have any lecture "
                        "history for this course yet.",
                    "confidence": 0.96,
                }


            latest = lectures[0]


            return {
                "type": "lecture_history",

                "answer": (
                    f"Your latest recorded lecture "
                    f"was on {latest['date']}. "
                    f"You taught: "
                    f"{latest['description']}"
                ),

                "data": latest,

                "confidence": 0.97,
            }


        # --------------------------------
        # COURSE STATUS
        # --------------------------------

        if (
            "how am i doing" in message_lower
            or "course status" in message_lower
            or "course progress" in message_lower
            or "syllabus progress" in message_lower
        ):

            if not course:
                return {
                    "type": "error",
                    "answer":
                        "I couldn't determine the "
                        "course you want to analyse.",
                }


            return {
                "type": "course_status",

                "answer": (
                    f"{course['name']} is "
                    f"{course['progress']:.0f}% complete. "
                    f"The planned progress is "
                    f"{course['planned_progress']:.0f}%. "
                    f"Your current pace is "
                    f"{course['current_pace']:.2f} "
                    f"topics per class, compared with "
                    f"a required pace of "
                    f"{course['required_pace']:.2f}."
                ),

                "data": course,

                "confidence": 0.95,
            }


        # --------------------------------
        # GENERAL CONTEXT RESPONSE
        # --------------------------------

        lecturer = context["lecturer"]

        if (
            "why am i behind" in message_lower
            or "why behind" in message_lower
        ):
            course = context.get("selected_course")

            if course:
                progress = course["progress"]
                planned_progress = course["planned_progress"]

                gap = round(planned_progress - progress, 1)

                if gap > 0:
                    answer = (
                        f"Your {course['short_name']} course is currently "
                        f"{gap}% behind the planned syllabus progress. "
                        f"Current progress is {progress}% while planned progress "
                        f"is {planned_progress}%."
                    )

                    if memories:
                        answer += "\n\nRecent academic events that may be relevant:\n"

                        for memory in memories[:5]:
                            answer += (
                                f"• {memory.title} — {memory.summary}\n"
                            )

                    return {
                        "answer": answer,
                        "confidence": 0.92,
                        "requires_confirmation": False,
                    }
        if (
            "what happened recently" in message_lower
            or "recent events" in message_lower
            or "what happened in dbms" in message_lower
        ):
            if memories:
                answer = "Here are the recent DBMS academic events I remember:\n\n"

                for memory in memories[:5]:
                    answer += (
                        f"• {memory.title}\n"
                        f"  {memory.summary}\n"
                    )

                return {
                    "answer": answer,
                    "confidence": 0.95,
                    "requires_confirmation": False,
                }

            return {
                "answer": "I don't have any recorded academic events for this course yet.",
                "confidence": 0.95,
                "requires_confirmation": False,
            }
        return {
            "type": "general",

            "answer": (
                f"I'm currently working with "
                f"{lecturer['name']}'s academic context. "
                f"You have "
                f"{context['summary']['total_courses']} "
                f"active courses, with "
                f"{context['summary']['courses_behind']} "
                f"currently behind their planned pace."
            ),

            "data": {
                "context_summary":
                    context["summary"],

                "alerts":
                    context["alerts"],
            },

            "confidence": 0.72,
        }