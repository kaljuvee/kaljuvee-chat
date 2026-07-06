from __future__ import annotations


def get_user_email(sess) -> str | None:
    return sess.get("chat_email")


def set_user_email(sess, email: str):
    sess["chat_email"] = email


def get_user_id(sess) -> int | None:
    return sess.get("chat_uid")


def set_user_id(sess, uid: int):
    sess["chat_uid"] = uid


def clear_user(sess):
    sess.pop("chat_email", None)
    sess.pop("chat_uid", None)


def is_signed_in(sess) -> bool:
    return bool(sess.get("chat_email"))


# --- Anonymous free-query counter (bot / token-drain protection) ------------

def get_anon_query_count(sess) -> int:
    return int(sess.get("anon_queries", 0))


def increment_anon_query_count(sess) -> int:
    n = get_anon_query_count(sess) + 1
    sess["anon_queries"] = n
    return n


def reset_anon_query_count(sess):
    sess.pop("anon_queries", None)
