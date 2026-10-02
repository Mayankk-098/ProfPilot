from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from app.services.entity_resolver import resolve_entities
from app.services.context_engine import (
    build_academic_context,
)
from app.services.memory_relevance import (
    get_relevant_memories,
)


class ProfPilotAI:

    def query(
        self,
        message: str,
        db: Session,
        course_id: str | None = None,
        lecturer_id: str = "lecturer_001",
        nlp_analysis: dict | None = None,
    ) -> dict:

        message_lower = message.lower()

        # The learned NLP pipeline is the primary router.
        # If nlp_analysis is not supplied, the legacy keyword
        # routing below remains available as a fallback.
        intent = None
        if nlp_analysis:
            intent = nlp_analysis.get("intent")

        def route_to(expected_intent: str, *legacy_phrases: str) -> bool:
            """
            Use the learned intent when available.
            Fall back to legacy keyword matching only when
            the AI service is called without NLP analysis.
            """
            if intent is not None:
                return intent == expected_intent

            return any(
                phrase in message_lower
                for phrase in legacy_phrases
            )

        # --------------------------------
        # BUILD REAL ACADEMIC CONTEXT
        # --------------------------------
        resolved_entities = resolve_entities(
            db=db,
            nlp_analysis=nlp_analysis,
            fallback_course_id=course_id,
        )

        effective_course_id = resolved_entities["course_id"]

        context = build_academic_context(
            db=db,
            lecturer_id=lecturer_id,
            course_id=effective_course_id,
        )

        course = context["selected_course"]

        memories = get_relevant_memories(
            db=db,
            query=message,
            lecturer_id=lecturer_id,
            course_id=effective_course_id,
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

        if route_to(
            "query_course_completion",
            "when",
            "finish",
            "complete",
        ):
            if not course:
                return {
                    "type": "error",
                    "answer": (
                        "I couldn't find a course "
                        "to analyse."
                    ),
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
                    "course": course["short_name"],
                    "progress": course["progress"],
                    "planned_progress": course["planned_progress"],
                    "current_pace": course["current_pace"],
                    "required_pace": course["required_pace"],
                    "predicted_completion": (
                        course["predicted_completion"]
                    ),
                },
                "confidence": 0.88,
            }

        # --------------------------------
        # WHAT-IF SCHEDULE CHANGE
        # --------------------------------

        if route_to(
            "what_if_schedule_change",
            "what if",
        ):
            if not course:
                return {
                    "type": "error",
                    "answer": (
                        "I couldn't determine which "
                        "course you mean."
                    ),
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

            scenario = "cancel the next"

            if (
                "extra" in message_lower
                or "additional" in message_lower
                or "add one more" in message_lower
            ):
                scenario = "add an extra"

            elif (
                "miss" in message_lower
                or "skip" in message_lower
                or "postpone" in message_lower
            ):
                scenario = "miss or postpone the next"

            return {
                "type": "what_if",
                "answer": (
                    f"If you {scenario} "
                    f"{course['short_name']} class, "
                    f"the current demo model estimates "
                    f"a schedule impact of approximately "
                    f"{delay_days} days. "
                    f"The predicted completion would "
                    f"shift from "
                    f"{course['predicted_completion']} "
                    f"to "
                    f"{new_date.day} "
                    f"{new_date.strftime('%B %Y')}. "
                    "This is a prototype simulation and "
                    "will later be replaced by the real "
                    "prediction model."
                ),
                "data": {
                    "course": course["short_name"],
                    "original_completion": (
                        course["predicted_completion"]
                    ),
                    "simulated_completion": (
                        f"{new_date.day} "
                        f"{new_date.strftime('%B %Y')}"
                    ),
                    "delay_days": delay_days,
                },
                "confidence": 0.81,
                "requires_confirmation": True,
            }

        # --------------------------------
        # NEXT CLASS
        # --------------------------------

        if route_to(
            "query_next_class",
            "next class",
            "next lecture",
        ):
            next_class = context["next_class"]

            if not next_class:
                return {
                    "type": "schedule",
                    "answer": (
                        "You have no classes "
                        "scheduled."
                    ),
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

        if route_to(
            "query_last_lecture",
            "what did i teach",
            "last lecture",
            "previous lecture",
        ):
            lectures = context["recent_lectures"]

            if not lectures:
                return {
                    "type": "lecture_history",
                    "answer": (
                        "I don't have any lecture "
                        "history for this course yet."
                    ),
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

        if route_to(
            "query_course_status",
            "how am i doing",
            "course status",
            "course progress",
            "syllabus progress",
        ):
            if not course:
                return {
                    "type": "error",
                    "answer": (
                        "I couldn't determine the "
                        "course you want to analyse."
                    ),
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
        # EXPLAIN DELAY
        # --------------------------------

        if route_to(
            "explain_delay",
            "why am i behind",
            "why behind",
        ):
            if not course:
                return {
                    "type": "error",
                    "answer": (
                        "I couldn't determine the "
                        "course you want to analyse."
                    ),
                }

            progress = course["progress"]
            planned_progress = course["planned_progress"]
            gap = round(
                planned_progress - progress,
                1,
            )

            if gap > 0:
                answer = (
                    f"Your {course['short_name']} course "
                    f"is currently {gap}% behind the "
                    "planned syllabus progress. "
                    f"Current progress is {progress}% "
                    f"while planned progress is "
                    f"{planned_progress}%."
                )
            elif gap < 0:
                answer = (
                    f"Your {course['short_name']} course "
                    f"is currently {abs(gap)}% ahead of "
                    "the planned syllabus progress."
                )
            else:
                answer = (
                    f"Your {course['short_name']} course "
                    "is currently exactly on the planned "
                    "syllabus progress."
                )

            if memories:
                answer += (
                    "\n\nRecent academic events that "
                    "may be relevant:\n"
                )

                for memory in memories[:5]:
                    answer += (
                        f"• {memory.title} — "
                        f"{memory.summary}\n"
                    )

            return {
                "type": "delay_explanation",
                "answer": answer,
                "data": {
                    "course": course["short_name"],
                    "progress": progress,
                    "planned_progress": planned_progress,
                    "gap": gap,
                    "memories_used": [
                        memory.title
                        for memory in memories[:5]
                    ],
                },
                "confidence": 0.92,
                "requires_confirmation": False,
            }

        # --------------------------------
        # QUERY MEMORY EVENTS
        # --------------------------------

        if route_to(
            "query_memory_events",
            "what happened recently",
            "recent events",
            "what happened in dbms",
        ):
            if memories:
                answer = (
                    "Here are the relevant academic "
                    "events I remember:\n\n"
                )

                for memory in memories[:5]:
                    answer += (
                        f"• {memory.title}\n"
                        f"  {memory.summary}\n"
                    )

                return {
                    "type": "memory",
                    "answer": answer,
                    "data": {
                        "memories": [
                            {
                                "title": memory.title,
                                "summary": memory.summary,
                                "event_type": memory.event_type,
                            }
                            for memory in memories[:5]
                        ]
                    },
                    "confidence": 0.95,
                    "requires_confirmation": False,
                }

            return {
                "type": "memory",
                "answer": (
                    "I don't have any recorded academic "
                    "events relevant to this query yet."
                ),
                "confidence": 0.95,
                "requires_confirmation": False,
            }

        # --------------------------------
        # GENERAL CONTEXT RESPONSE
        # --------------------------------

        lecturer = context["lecturer"]

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
                "context_summary": context["summary"],
                "alerts": context["alerts"],
            },
            "confidence": 0.72,
        }


ai = ProfPilotAI()