from __future__ import annotations

import hashlib
import hmac
import json
import os
import time


ACTION_TOKEN_TTL_SECONDS = 300


def _get_secret() -> str:
    """
    Get the server-side secret used to sign action proposals.

    Set PROFPILOT_ACTION_SECRET in the environment.
    """
    secret = os.getenv(
        "PROFPILOT_ACTION_SECRET"
    )

    if not secret:
        raise RuntimeError(
            "PROFPILOT_ACTION_SECRET is not configured."
        )

    return secret


def _canonicalize_action_plan(
    action_plan: dict,
) -> str:
    """
    Produce deterministic JSON for signing.

    The token itself is excluded from the signed content.
    """
    unsigned_plan = dict(action_plan)

    unsigned_plan.pop(
        "proposal_token",
        None,
    )

    return json.dumps(
        unsigned_plan,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def create_action_token(
    action_plan: dict,
    ttl_seconds: int = ACTION_TOKEN_TTL_SECONDS,
) -> str:
    """
    Create a short-lived HMAC signature for an action plan.

    Any modification to the action plan after proposal
    creation will invalidate the token.
    """

    expires_at = int(
        time.time()
        + ttl_seconds
    )

    canonical_plan = (
        _canonicalize_action_plan(
            action_plan
        )
    )

    signed_payload = (
        f"{expires_at}."
        f"{canonical_plan}"
    )

    signature = hmac.new(
        _get_secret().encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return (
        f"{expires_at}."
        f"{signature}"
    )


def verify_action_token(
    action_plan: dict,
) -> tuple[bool, str]:
    """
    Verify that the action plan was signed by the server
    and has not expired.
    """

    token = action_plan.get(
        "proposal_token"
    )

    if not token:
        return (
            False,
            "Action proposal is missing its security token.",
        )

    try:
        expires_text, provided_signature = (
            str(token).split(".", 1)
        )

        expires_at = int(
            expires_text
        )

    except (
        ValueError,
        TypeError,
    ):
        return (
            False,
            "Action proposal token is malformed.",
        )

    current_time = int(
        time.time()
    )

    if current_time >= expires_at:
        return (
            False,
            "Action proposal has expired. Please create a new proposal.",
        )

    canonical_plan = (
        _canonicalize_action_plan(
            action_plan
        )
    )

    signed_payload = (
        f"{expires_at}."
        f"{canonical_plan}"
    )

    expected_signature = hmac.new(
        _get_secret().encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        provided_signature,
        expected_signature,
    ):
        return (
            False,
            "Action proposal was modified or is invalid.",
        )

    return (
        True,
        "ok",
    )