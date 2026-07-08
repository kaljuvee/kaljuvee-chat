"""Structural smoke tests for the Talk to Julian app (no network required)."""

import os

os.environ.setdefault("DB_URL", "sqlite:///:memory:")


def test_db_init():
    import db
    db.init_db()  # should not raise


def test_system_prompt_is_grounded():
    from agents.base import _load_system_prompt
    p = _load_system_prompt("ask_julian")
    assert "Talk to Julian" in p          # persona
    assert "Indurent" in p            # CV injected
    assert "Microsoft" in p
    assert "predictivelabs" in p.lower()  # curated facts injected


def test_router_single_agent():
    from agents import router
    assert router.route("literally anything") == "ask_julian"


def test_articles_loader():
    from utils.articles import load_articles, all_tags
    arts = load_articles()
    assert isinstance(arts, list)
    for a in arts:
        assert a["title"] and a["url"]
    assert isinstance(all_tags(arts), list)


def test_anon_query_counter():
    from utils.session import (increment_anon_query_count, get_anon_query_count,
                               is_signed_in, set_user_email)
    sess = {}
    assert not is_signed_in(sess)
    for i in range(1, 4):
        assert increment_anon_query_count(sess) == i
    assert get_anon_query_count(sess) == 3
    set_user_email(sess, "visitor@example.com")
    assert is_signed_in(sess)


def test_chat_page_renders_nav():
    from chat.layout import chat_page
    html = str(chat_page(user_email=None, sessions=[], messages=[]))
    for needle in ["Talk to Julian", "julian-kaljuvee-portrait.jpeg",
                   "linkedin.com/in/juliankaljuvee", "predictivelabs.ai",
                   "liquidround", "Try asking", "New chat",
                   "Book a call", "cal.com/kaljuvee"]:   # left-menu scheduling
        assert needle in html, f"missing from page: {needle}"


def test_scheduling_intent_detection():
    from scheduling import is_scheduling_request, scheduling_response_html, BOOKING_URL
    for m in ["Can I book a call with Julian?", "schedule a meeting",
              "let's chat sometime", "hop on a call", "book a slot"]:
        assert is_scheduling_request(m), f"should detect: {m}"
    for m in ["What are Julian's strongest skills?", "Can you give me your CV?",
              "Tell me about his company"]:
        assert not is_scheduling_request(m), f"false positive: {m}"
    assert BOOKING_URL in scheduling_response_html()
