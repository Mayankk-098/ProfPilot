import re
from app.services.action_planner import plan_action
from sqlalchemy.orm import Session
from app.services.entity_resolver import resolve_entities
from app.services.context_engine import (
    build_academic_context,
)
from app.services.prediction_engine import (
    predict_course_completion,
)
from app.services.what_if_engine import (
    simulate_schedule_change,
)
from app.services.syllabus_drift_engine import (
    detect_syllabus_drift,
)
from app.services.memory_relevance import (
    get_relevant_memories,
)


def build_action_message(
    action_plan: dict,
) -> str:
    action = action_plan["action"]

    proposal = action_plan["proposal"]

    if action == "cancel_class":
        course_id = proposal["course_id"]
        date = proposal["date"]
        time = proposal["time"]

        answer = (
            f"I can prepare the cancellation of "
            f"{course_id.upper()} on {date}"
        )

        if time:
            answer += f" at {time}"

        answer += ". Would you like me to proceed?"

        return answer

    if action == "reschedule_class":
        course_id = proposal["course_id"]
        date = proposal["date"]
        time = proposal["time"]
        new_date = proposal["new_date"]
        new_time = proposal["new_time"]

        answer = (
            f"I can prepare a reschedule for "
            f"{course_id.upper()}"
        )

        if date:
            answer += f" on {date}"

        if time:
            answer += f" at {time}"

        if new_date:
            answer += f" → {new_date}"

        if new_time:
            answer += f" at {new_time}"

        answer += ". Would you like me to proceed?"

        return answer

    if action == "notify_batch":
        return (
            f"I can prepare a notification for "
            f"{proposal['batch']} about "
            f"{proposal['course_id'].upper()}. "
            "Would you like me to proceed?"
        )

    if action == "log_lecture":
        answer = (
            f"I can prepare a lecture record for "
            f"{proposal['course_id'].upper()} covering "
            f"{proposal['topic']}"
        )

        if proposal.get("date"):
            answer += f" on {proposal['date']}"

        if proposal.get("duration"):
            answer += f" for {proposal['duration']}"

        matches = proposal.get(
            "syllabus_matches",
            [],
        )

        if matches:
            answer += (
                ".\n\n"
                "I matched it to these syllabus topics:\n"
            )

            for match in matches:
                # Support the mapper's current output keys.
                topic_name = (
                    match.get("topic_name")
                    or match.get("topic")
                    or match.get("name")
                    or "Unknown topic"
                )

                unit_name = (
                    match.get("unit_name")
                    or match.get("unit")
                    or "Unknown unit"
                )

                score = match.get(
                    "score",
                    0.0,
                )

                answer += (
                    f"• {topic_name} "
                    f"(Unit: {unit_name}, "
                    f"score: {score:.2f})\n"
                )

        elif proposal.get(
            "mapping_status"
        ) == "no_match":
            answer += (
                ".\n\n"
                "I couldn't confidently match "
                "this lecture to the current syllabus."
            )

        elif proposal.get(
            "mapping_status"
        ) == "error":
            answer += (
                ".\n\n"
                "The lecture will still be prepared, "
                "but syllabus mapping could not be completed."
            )

        answer += "\nWould you like me to proceed?"

        return answer

    return (
        "I understood the requested action, "
        "but I need more information before proceeding."
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
            intent = nlp_analysis.get(
                "intent"
            )

            # --------------------------------
            # EXPLICIT ACTION OVERRIDE
            # --------------------------------
            #
            # A clear action phrase should not be
            # classified as out_of_scope merely because
            # the ML classifier is uncertain.
            #
            # Example:
            # "log a DBMS lecture about databases"
            #
            # The action is clear, but the lecture topic
            # itself may still be missing. Let action_planner
            # handle that as a clarification request.
            # --------------------------------

            # --------------------------------
            # EXPLICIT ACTION OVERRIDE
            # --------------------------------

            explicit_action_override = False

            if intent == "out_of_scope":
                original_message_lower = (
                    message.lower().strip()
                )

                starts_with_action = (
                    original_message_lower.startswith("log ")
                    or original_message_lower.startswith("record ")
                    or original_message_lower.startswith("add ")
                    or original_message_lower.startswith("mark ")
                )

                mentions_lecture_or_class = (
                    "lecture" in original_message_lower
                    or "class" in original_message_lower
                )

                if (
                    starts_with_action
                    and mentions_lecture_or_class
                ):
                    intent = "log_lecture"
                    explicit_action_override = True

                    if explicit_action_override and nlp_analysis:
                        nlp_analysis["intent"] = intent

            # --------------------------------
            # ACTION SAFETY GATE
            # --------------------------------

            action_intents = {
                "cancel_class",
                "reschedule_class",
                "log_lecture",
                "notify_batch",
            }

            if (
                intent in action_intents
                and not explicit_action_override
            ):
                intent_score = float(
                    nlp_analysis.get(
                        "intent_score",
                        0.0,
                    )
                )

                top_intents = (
                    nlp_analysis.get(
                        "top_intents",
                        [],
                    )
                )

                second_score = 0.0

                if len(top_intents) > 1:
                    second_score = float(
                        top_intents[1].get(
                            "score",
                            0.0,
                        )
                    )

                intent_margin = (
                    intent_score
                    - second_score
                )

                MIN_ACTION_CONFIDENCE = 0.20
                MIN_ACTION_MARGIN = 0.08

                if (
                    intent_score
                    < MIN_ACTION_CONFIDENCE
                    or intent_margin
                    < MIN_ACTION_MARGIN
                ):
                    intent = None

                    # --------------------------------
                    # ACTION SAFETY GATE
                    # --------------------------------
                    #
                    # Mutating actions require stronger
                    # NLP confidence than read-only queries.
                    #
                    # This prevents a weak/ambiguous prediction
                    # from automatically reaching action_planner.
                    # --------------------------------

                    action_intents = {
                        "cancel_class",
                        "reschedule_class",
                        "log_lecture",
                        "notify_batch",
                    }

                    if intent in action_intents:
                        intent_score = float(
                            nlp_analysis.get(
                                "intent_score",
                                0.0,
                            )
                        )

                        top_intents = (
                            nlp_analysis.get(
                                "top_intents",
                                [],
                            )
                        )

                        second_score = 0.0

                        if len(top_intents) > 1:
                            second_score = float(
                                top_intents[1].get(
                                    "score",
                                    0.0,
                                )
                            )

                        intent_margin = (
                            intent_score
                            - second_score
                        )

                        MIN_ACTION_CONFIDENCE = 0.20
                        MIN_ACTION_MARGIN = 0.08

                        if (
                            intent_score
                            < MIN_ACTION_CONFIDENCE
                            or intent_margin
                            < MIN_ACTION_MARGIN
                        ):
                            # Treat the action as unresolved.
                            # Do NOT let action_planner create
                            # a mutation proposal.
                            intent = None

        def route_to(
            expected_intent: str,
            *legacy_phrases: str,
        ) -> bool:
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

        def is_syllabus_drift_query() -> bool:
            """
            Detect explicit syllabus-plan/drift questions.

            The learned intent model remains the primary router.
            This narrow secondary detector covers the new capability
            before we have a separately trained intent label.
            """
            drift_phrases = (
                "syllabus drift",
                "drifting from",
                "drift from",
                "drift in",
                "teaching plan",
                "planned syllabus",
                "off plan",
                "off-plan",
                "deviating from the plan",
                "deviation from the plan",
                "diverging from the plan",
                "coverage issue",
                "syllabus coverage issue",
            )

            return any(
                phrase in message_lower
                for phrase in drift_phrases
            )

        # --------------------------------
        # BUILD REAL ACADEMIC CONTEXT
        # --------------------------------

        resolved_entities = resolve_entities(
            db=db,
            nlp_analysis=nlp_analysis,
            fallback_course_id=course_id,
        )

        effective_course_id = (
            resolved_entities["course_id"]
        )

        if resolved_entities.get(
            "course_resolution_failed"
        ):
            return {
                "type": "course_not_found",
                "answer": (
                    f"I couldn't find "
                    f"'{resolved_entities['course_text']}' "
                    "in the current academic records. "
                    "Please check the course name or code."
                ),
                "data": {
                    "course_text": (
                        resolved_entities[
                            "course_text"
                        ]
                    ),
                },
                "confidence": 0.95,
                "requires_confirmation": False,
            }

        action_plan = plan_action(
            intent=intent,
            resolved_entities=resolved_entities,
            db=db,
        )

        if action_plan is not None:
            # --------------------------------
            # LOG LECTURE WITH NO SYLLABUS MATCH
            # --------------------------------
            #
            # A topic may be present but still be too
            # vague to map to the current syllabus.
            # Do not create a confirmation proposal
            # in that case.
            # --------------------------------

            if (
                action_plan.get("action") == "log_lecture"
                and action_plan.get("proposal")
                and action_plan["proposal"].get(
                    "mapping_status"
                ) == "no_match"
            ):
                topic_text = (
                    resolved_entities.get("topic_text")
                    or action_plan["proposal"].get("topic")
                    or "that topic"
                )

                clarification_plan = {
                    "action": "log_lecture",
                    "status": "needs_clarification",
                    "requires_confirmation": False,
                    "missing": [
                        "a specific syllabus topic"
                    ],
                    "proposal": None,
                }

                return {
                    "type": "action_clarification",
                    "answer": (
                        f"I understand that you want to log a "
                        f"lecture, but I couldn't match "
                        f"'{topic_text}' to the current syllabus. "
                        "Please give me a specific syllabus topic "
                        "such as Indexing, B Trees, or B+ Trees."
                    ),
                    "data": {
                        "action_plan": clarification_plan,
                        "resolved_entities": resolved_entities,
                    },
                    "confidence": 0.90,
                    "requires_confirmation": False,
                }

            # --------------------------------
            # UNSUPPORTED ACTION
            # --------------------------------
            #
            # The planner may understand an action
            # that the executor does not implement yet.
            #
            # Do not ask for confirmation when the
            # action cannot actually be executed.
            # --------------------------------

            if (
                action_plan["status"]
                == "unsupported"
            ):
                return {
                    "type": "action_unavailable",
                    "answer": (
                        f"I understand that you want to "
                        f"{action_plan['action'].replace('_', ' ')}, "
                        "but that action is not executable "
                        "in the current ProfPilot version yet."
                    ),
                    "data": {
                        "action": (
                            action_plan[
                                "action"
                            ]
                        ),
                    },
                    "confidence": 0.95,
                    "requires_confirmation": False,
                }

            if (
                action_plan["status"]
                == "needs_clarification"
            ):
                missing_text = ", ".join(
                    action_plan["missing"]
                )

                return {
                    "type": "action_clarification",
                    "answer": (
                        "I understand that you want to "
                        f"{action_plan['action'].replace('_', ' ')}, "
                        "but I need the following information: "
                        f"{missing_text}."
                    ),
                    "data": {
                        "action_plan": action_plan,
                        "resolved_entities": resolved_entities,
                    },
                    "confidence": 0.90,
                    "requires_confirmation": True,
                }

            return {
                "type": "action_proposal",
                "answer": build_action_message(
                    action_plan
                ),
                "data": {
                    "action_plan": action_plan,
                    "resolved_entities": resolved_entities,
                },
                "confidence": 0.90,
                "requires_confirmation": True,
            }

        # --------------------------------
        # OUT-OF-SCOPE QUERY
        # --------------------------------
        #
        # Do not fall through to the academic
        # context for queries that the trained
        # classifier explicitly identifies as
        # outside ProfPilot's domain.
        # --------------------------------
        
        if intent == "out_of_scope":
            return {
                "type": "out_of_scope",
                "answer": (
                    "I can help with your academic "
                    "work, such as course progress, "
                    "syllabus tracking, lecture records, "
                    "predictions, schedules, and "
                    "academic planning."
                ),
                "data": {},
                "confidence": float(
                    nlp_analysis.get(
                        "intent_score",
                        0.0,
                    )
                    if nlp_analysis
                    else 0.0
                ),
                "requires_confirmation": False,
            }

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

        memory_context = "\n".join(
            memory_lines
        )

        if not memory_context:
            memory_context = (
                "No relevant academic memories found."
            )

        # --------------------------------
        # SYLLABUS DRIFT DETECTION
        # --------------------------------

        if is_syllabus_drift_query():

            if not effective_course_id:
                return {
                    "type": "error",
                    "answer": (
                        "I couldn't determine which course "
                        "you want me to analyse."
                    ),
                    "confidence": 0.95,
                    "requires_confirmation": False,
                }

            drift_result = detect_syllabus_drift(
                db=db,
                course_id=effective_course_id,
            )

            if drift_result.get(
                "status"
            ) != "ok":
                return {
                    "type": "syllabus_drift",
                    "answer": (
                        "I couldn't analyse syllabus drift "
                        "from the current academic data."
                    ),
                    "data": drift_result,
                    "confidence": 0.60,
                    "requires_confirmation": False,
                }

            severity = drift_result["severity"]
            summary = drift_result["summary"]
            signals = drift_result["signals"]

            if severity == "high_drift":
                status_text = (
                    "shows substantial deviation "
                    "from the current plan"
                )
            elif severity == "moderate_drift":
                status_text = (
                    "shows a moderate deviation "
                    "from the current plan"
                )
            elif severity == "mild_drift":
                status_text = (
                    "shows a mild deviation "
                    "from the current plan"
                )
            else:
                status_text = (
                    "is broadly aligned "
                    "with the current plan"
                )

            answer = (
                f"{course['name']} {status_text}. "
                f"Actual syllabus progress is "
                f"{summary['actual_progress']:.2f}%, compared with "
                f"{summary['planned_progress']:.2f}% planned "
                f"({summary['progress_gap']:.2f} percentage points). "
                f"There are {summary['remaining_topics']} syllabus topics "
                f"remaining across {summary['lecture_count']} recorded lectures."
            )

            if summary["lecture_count"] > 0:
                answer += (
                    f" Recent teaching pace is "
                    f"{summary['recent_pace']:.2f} new topics per lecture, "
                    f"versus a required pace of "
                    f"{summary['required_pace']:.2f}."
                )

            answer += (
                f" Drift score: "
                f"{drift_result['drift_score']:.2f}/100."
            )

            if signals:
                answer += "\n\nEvidence:"

                for signal in signals[:4]:

                    if (
                        signal["type"]
                        == "repeated_coverage"
                    ):
                        names = signal[
                            "evidence"
                        ].get(
                            "repeated_topics",
                            [],
                        )

                        answer += (
                            "\n• Repeated coverage: "
                            + ", ".join(names)
                        )

                    else:
                        answer += (
                            f"\n• {signal['description']}"
                        )

            answer += (
                "\n\nRecommendation: "
                f"{drift_result['recommendation']}"
            )

            return {
                "type": "syllabus_drift",
                "answer": answer,
                "data": drift_result,
                "confidence": 0.85,
                "requires_confirmation": False,
            }

        # --------------------------------
        # COURSE FINISH PREDICTION
        # --------------------------------

        if route_to(
            "query_course_completion",
            "when",
            "finish",
            "complete",
        ):
            if not effective_course_id:
                return {
                    "type": "error",
                    "answer": (
                        "I couldn't determine which "
                        "course you want to analyse."
                    ),
                    "confidence": 0.95,
                    "requires_confirmation": False,
                }

            prediction = (
                predict_course_completion(
                    db=db,
                    course_id=effective_course_id,
                )
            )

            if prediction.get(
                "status"
            ) == "insufficient_data":
                return {
                    "type": "prediction",
                    "answer": (
                        f"I don't have enough lecture "
                        f"history to produce a reliable "
                        f"completion forecast for "
                        f"{course['short_name']} yet."
                    ),
                    "data": {
                        "course": (
                            course["short_name"]
                        ),
                        "prediction": None,
                        "reason": (
                            prediction.get(
                                "evidence"
                            )
                        ),
                    },
                    "confidence": 0.50,
                    "requires_confirmation": False,
                }

            if prediction.get(
                "status"
            ) == "complete":
                predicted = prediction[
                    "prediction"
                ]

                return {
                    "type": "prediction",
                    "answer": (
                        f"{course['name']} has "
                        f"no remaining syllabus topics."
                    ),
                    "data": {
                        "course": (
                            course["short_name"]
                        ),
                        "prediction": predicted,
                    },
                    "confidence": 0.99,
                    "requires_confirmation": False,
                }

            predicted = prediction[
                "prediction"
            ]

            evidence = prediction[
                "evidence"
            ]

            predicted_date = predicted[
                "predicted_completion"
            ]

            lower_bound = predicted[
                "lower_bound"
            ]

            upper_bound = predicted[
                "upper_bound"
            ]

            confidence = predicted[
                "confidence"
            ]

            remaining = evidence[
                "remaining_topics"
            ]

            working_pace = evidence[
                "working_pace"
            ]

            interval_days = evidence[
                "typical_lecture_interval_days"
            ]

            estimated_lectures = predicted[
                "estimated_lectures_remaining"
            ]

            # Compare the newly derived forecast against
            # the old stored/demo forecast.
            stored_prediction = (
                course.get(
                    "predicted_completion"
                )
            )

            answer = (
                f"Your {course['name']} has "
                f"{remaining} syllabus topics remaining. "
                f"Based on your recorded teaching history, "
                f"I estimate about "
                f"{estimated_lectures} more lectures are needed. "
                f"Your current derived pace is "
                f"{working_pace:.2f} new topics per lecture, "
                f"with a typical lecture interval of "
                f"{interval_days:.1f} days. "
                f"The estimated completion date is "
                f"{predicted_date}."
            )

            answer += (
                f"\n\nForecast range: "
                f"{lower_bound} to {upper_bound}."
            )

            answer += (
                f"\nForecast confidence: "
                f"{confidence}."
            )

            if stored_prediction:
                answer += (
                    f"\n\nStored course forecast: "
                    f"{stored_prediction}"
                )

            return {
                "type": "prediction",
                "answer": answer,
                "data": {
                    "course": (
                        course["short_name"]
                    ),
                    "progress": (
                        course["progress"]
                    ),
                    "planned_progress": (
                        course["planned_progress"]
                    ),
                    "remaining_topics": remaining,
                    "lecture_count": (
                        evidence["lecture_count"]
                    ),
                    "overall_pace": (
                        evidence["overall_pace"]
                    ),
                    "recent_pace": (
                        evidence["recent_pace"]
                    ),
                    "working_pace": working_pace,
                    "typical_lecture_interval_days": (
                        interval_days
                    ),
                    "estimated_lectures_remaining": (
                        estimated_lectures
                    ),
                    "predicted_completion": (
                        predicted_date
                    ),
                    "prediction_range": {
                        "lower": lower_bound,
                        "upper": upper_bound,
                    },
                    "confidence": confidence,
                    "stored_prediction": (
                        stored_prediction
                    ),
                },
                "confidence": 0.80,
                "requires_confirmation": False,
            }

        # --------------------------------
        # WHAT-IF SCHEDULE CHANGE
        # --------------------------------

        if route_to(
            "what_if_schedule_change",
            "what if",
        ):
            if not effective_course_id:
                return {
                    "type": "error",
                    "answer": (
                        "I couldn't determine which "
                        "course you mean."
                    ),
                    "confidence": 0.95,
                    "requires_confirmation": False,
                }

            what_if = simulate_schedule_change(
                db=db,
                course_id=effective_course_id,
                message=message,
            )

            if (
                what_if.get("status")
                == "insufficient_data"
            ):
                return {
                    "type": "what_if",
                    "answer": (
                        f"I don't have enough teaching history "
                        f"to simulate a schedule change for "
                        f"{course['short_name']} reliably yet."
                    ),
                    "data": what_if,
                    "confidence": 0.50,
                    "requires_confirmation": False,
                }

            if (
                what_if.get("status")
                == "complete"
            ):
                return {
                    "type": "what_if",
                    "answer": (
                        f"{course['name']} has no remaining "
                        f"syllabus topics, so there is no "
                        f"completion date left to simulate."
                    ),
                    "data": what_if,
                    "confidence": 0.99,
                    "requires_confirmation": False,
                }

            if what_if.get(
                "status"
            ) != "ok":
                return {
                    "type": "what_if",
                    "answer": (
                        "I understood the what-if scenario, "
                        "but I couldn't simulate it from the "
                        "current academic data."
                    ),
                    "data": what_if,
                    "confidence": 0.60,
                    "requires_confirmation": False,
                }

            scenario_label = what_if[
                "scenario_label"
            ]

            baseline = what_if[
                "baseline"
            ]

            simulation = what_if[
                "simulation"
            ]

            evidence = what_if[
                "evidence"
            ]

            change_days = simulation[
                "change_days"
            ]

            abs_change = abs(
                change_days
            )

            if change_days > 0:
                impact_text = (
                    f"about {abs_change:.0f} day"
                    f"{'s' if abs_change != 1 else ''} later"
                )

            elif change_days < 0:
                impact_text = (
                    f"about {abs_change:.0f} day"
                    f"{'s' if abs_change != 1 else ''} earlier"
                )

            else:
                impact_text = "no change"

            answer = (
                f"If you {scenario_label} for "
                f"{course['short_name']}, the derived completion "
                f"forecast moves from "
                f"{baseline['predicted_completion']} to "
                f"{simulation['predicted_completion']} "
                f"({impact_text})."
                f" You would have "
                f"{simulation['estimated_lectures_remaining']} "
                f"estimated lectures remaining instead of "
                f"{baseline['estimated_lectures_remaining']}."
            )

            answer += (
                f" This simulation uses a working pace of "
                f"{evidence['working_pace']:.2f} new topics per "
                f"lecture and a typical lecture interval of "
                f"{evidence['typical_lecture_interval_days']:.1f} days."
            )

            return {
                "type": "what_if",
                "answer": answer,
                "data": {
                    "course": course["short_name"],
                    **what_if,
                },
                "confidence": 0.80,
                "requires_confirmation": False,
            }

        # --------------------------------
        # NEXT CLASS
        # --------------------------------

        if route_to(
            "query_next_class",
            "next class",
            "next lecture",
        ):
            next_class = context[
                "next_class"
            ]

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
            lectures = context[
                "recent_lectures"
            ]

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

            progress = course[
                "progress"
            ]

            planned_progress = course[
                "planned_progress"
            ]

            gap = round(
                planned_progress
                - progress,
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
                    "course": course[
                        "short_name"
                    ],
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

        lecturer = context[
            "lecturer"
        ]

        return {
            "type": "general",
            "answer": (
                f"I'm currently working with "
                f"{lecturer['name']}'s academic context. "
                f"You have "
                f"{context['summary']['total_courses']} "
                f"active courses, with "
                f"{context['summary']['courses_behind']} "
                "currently behind their planned pace."
            ),
            "data": {
                "context_summary": context[
                    "summary"
                ],
                "alerts": context[
                    "alerts"
                ],
            },
            "confidence": 0.72,
        }


ai = ProfPilotAI()