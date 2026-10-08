from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from html import escape
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import Course
from app.models.attendance import Enrollment, Student


RESEND_API_URL = "https://api.resend.com/emails"


def _config() -> tuple[str | None, str | None]:
    return (
        os.getenv("RESEND_API_KEY"),
        os.getenv("RESEND_FROM_EMAIL"),
    )


def _recipient_emails(
    db: Session,
    course_id: str,
    lecturer_id: str,
) -> list[str]:
    rows = db.execute(
        select(Student.email)
        .join(
            Enrollment,
            Enrollment.student_id == Student.id,
        )
        .where(
            Enrollment.course_id == course_id,
            Student.lecturer_id == lecturer_id,
            Student.email.is_not(None),
        )
        .order_by(Student.roll_no),
    ).all()

    emails: list[str] = []
    seen: set[str] = set()

    for (email,) in rows:
        if not email:
            continue
        normalized = email.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            emails.append(normalized)

    return emails


def _send_resend(
    *,
    recipients: Iterable[str],
    subject: str,
    text_body: str,
    html_body: str,
) -> dict:
    api_key, from_email = _config()

    if not api_key or not from_email:
        return {
            "status": "not_configured",
            "sent": False,
            "recipient_count": len(list(recipients)),
            "message": (
                "Email delivery is not configured. "
                "Set RESEND_API_KEY and RESEND_FROM_EMAIL."
            ),
        }

    recipient_list = list(recipients)
    if not recipient_list:
        return {
            "status": "no_recipients",
            "sent": False,
            "recipient_count": 0,
            "message": (
                "No enrolled students have an email address."
            ),
        }

    payload = json.dumps(
        {
            "from": from_email,
            "to": recipient_list,
            "subject": subject,
            "text": text_body,
            "html": html_body,
        }
    ).encode("utf-8")

    endpoint = os.getenv(
        "RESEND_API_URL",
        RESEND_API_URL,
    )

    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw) if raw else {}

        return {
            "status": "sent",
            "sent": True,
            "recipient_count": len(recipient_list),
            "provider": "resend",
            "provider_response": data,
        }

    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        return {
            "status": "provider_error",
            "sent": False,
            "recipient_count": len(recipient_list),
            "provider": "resend",
            "message": (
                f"Resend rejected the email request "
                f"({error.code})."
            ),
            "provider_error": detail[:1000],
        }

    except (urllib.error.URLError, TimeoutError) as error:
        return {
            "status": "delivery_error",
            "sent": False,
            "recipient_count": len(recipient_list),
            "provider": "resend",
            "message": f"Email delivery failed: {error}",
        }

    except (ValueError, json.JSONDecodeError) as error:
        return {
            "status": "provider_error",
            "sent": False,
            "recipient_count": len(recipient_list),
            "provider": "resend",
            "message": f"Invalid response from email provider: {error}",
        }


def send_class_notification(
    db: Session,
    *,
    course: Course,
    lecturer_id: str,
    notification_type: str,
    original_date: str,
    original_time: str,
    new_date: str | None = None,
    new_time: str | None = None,
    new_room: str | None = None,
    reason: str | None = None,
) -> dict:
    recipients = _recipient_emails(
        db,
        course.id,
        lecturer_id,
    )

    course_label = course.short_name or course.name

    if notification_type == "cancelled":
        subject = (
            f"[ProfPilot] {course.code} class cancelled — "
            f"{original_date}"
        )

        reason_line = (
            f"Reason: {reason}"
            if reason
            else "No reason was provided."
        )

        text_body = (
            f"Hello,\n\n"
            f"The {course_label} ({course.code}) class for "
            f"{course.section} scheduled on {original_date} "
            f"at {original_time} has been cancelled.\n\n"
            f"{reason_line}\n\n"
            f"ProfPilot"
        )

        html_body = (
            f"<p>Hello,</p>"
            f"<p>The <strong>{escape(course_label)}</strong> "
            f"({escape(course.code)}) class for "
            f"{escape(course.section)} scheduled on "
            f"<strong>{escape(original_date)}</strong> at "
            f"<strong>{escape(original_time)}</strong> has "
            f"been cancelled.</p>"
            f"<p>{escape(reason_line)}</p>"
            f"<p>ProfPilot</p>"
        )

    elif notification_type == "rescheduled":
        subject = (
            f"[ProfPilot] {course.code} class rescheduled — "
            f"{original_date}"
        )

        destination = (
            f"{new_date} at {new_time}"
            if new_date and new_time
            else new_date or new_time or "a new time"
        )

        room_line = (
            f"Room: {new_room}"
            if new_room
            else "Room: unchanged"
        )

        text_body = (
            f"Hello,\n\n"
            f"The {course_label} ({course.code}) class for "
            f"{course.section} originally scheduled on "
            f"{original_date} at {original_time} has been "
            f"rescheduled to {destination}.\n\n"
            f"{room_line}\n"
            f"{f'Reason: {reason}' if reason else ''}\n\n"
            f"ProfPilot"
        )

        html_body = (
            f"<p>Hello,</p>"
            f"<p>The <strong>{escape(course_label)}</strong> "
            f"({escape(course.code)}) class for "
            f"{escape(course.section)} originally scheduled on "
            f"<strong>{escape(original_date)}</strong> at "
            f"<strong>{escape(original_time)}</strong> has been "
            f"rescheduled to <strong>{escape(destination)}</strong>.</p>"
            f"<p>{escape(room_line)}</p>"
            f"<p>{escape(f'Reason: {reason}') if reason else ''}</p>"
            f"<p>ProfPilot</p>"
        )

    else:
        raise ValueError(
            f"Unsupported class notification type: {notification_type}"
        )

    return _send_resend(
        recipients=recipients,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
