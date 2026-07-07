"""FastHTML components for the Talk to Julian 3-pane chat UI."""

from __future__ import annotations

import json

from fasthtml.common import (
    Div, Span, H2, H3, H4, P, A, Img, Button, Form, Input, Textarea,
    Script, NotStr,
)
from agents.registry import AGENTS, AGENTS_BY_SLUG, SAMPLE_QUESTIONS


# ── Static nav data (mirrors prompts/shared/career_facts.md) ─────────────────

PROFILE_LINKS = [
    ("LinkedIn", "https://www.linkedin.com/in/juliankaljuvee/"),
    ("Personal site", "https://juliankaljuvee.org/"),
    ("GitHub", "https://github.com/kaljuvee"),
    ("Predictive Labs", "https://predictivelabs.ai"),
    ("Predictive Labs — GitHub", "https://github.com/orgs/predictivelabsai/repositories"),
    ("How this was built?", "https://github.com/kaljuvee/kaljuvee-chat"),
]

PROJECTS_BY_SECTOR = [
    ("Private Equity & Capital Markets", [
        ("liquidround — AI M&A / IPO analyst", "https://github.com/predictivelabsai/liquidround"),
        ("pehero — PE research platform", "https://github.com/predictivelabsai/pehero"),
        ("macrohero — macro analysis", "https://github.com/predictivelabsai/macrohero"),
    ]),
    ("Trading & Investment Research", [
        ("assethero — strategy backtester", "https://github.com/predictivelabsai/assethero"),
    ]),
    ("Health & Life Sciences", [
        ("prostate-cancer-screening", "https://github.com/predictivelabsai/prostate-cancer-screening"),
        ("FastClinic — patient activation", "https://github.com/predictivelabsai/FastClinic"),
    ]),
    ("Real Estate · Climate", [
        ("building-lca — lifecycle assessment", "https://github.com/predictivelabsai/building-lca"),
        ("climate-risk-toolkit", "https://github.com/predictivelabsai/climate-risk-toolkit"),
    ]),
    ("Art & Culture", [
        ("kanvas — AI art advisory", "https://github.com/predictivelabsai/kanvas"),
    ]),
]

LOGO_IMG = "/img/julian-kaljuvee-portrait.jpeg"


# ── Sign-in / register overlay ───────────────────────────────────────────────

def signin_overlay():
    return Div(
        Div(
            Div(
                Button("Sign In", id="auth-tab-login", cls="auth-tab active",
                       onclick="switchAuthTab('login')"),
                Button("Register", id="auth-tab-register", cls="auth-tab",
                       onclick="switchAuthTab('register')"),
                cls="flex border-b border-gray-200 mb-4",
            ),
            # Login
            Div(
                P("Sign in to keep chatting with Talk to Julian.", cls="text-sm text-gray-500 mb-4"),
                A(
                    Span(NotStr('<svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/><path d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9s.348 1.452.957 2.042l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>'),
                         cls="google-btn-icon"),
                    Span("Continue with Google", cls="google-btn-text"),
                    href="/auth/google", cls="google-btn",
                ),
                Div(Span(cls="google-divider-line"), Span("or", cls="google-divider-text"), Span(cls="google-divider-line"), cls="google-divider"),
                Input(type="email", id="login-email", placeholder="Email",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3",
                      onkeydown="if(event.key==='Enter')document.getElementById('login-password').focus()"),
                Input(type="password", id="login-password", placeholder="Password",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-2",
                      onkeydown="if(event.key==='Enter')doLogin()"),
                A("Forgot password?", href="#", onclick="showForgotPassword(event)",
                  cls="text-xs text-gray-400 hover:text-black block mb-4"),
                Div(id="login-error", cls="text-red-500 text-xs mb-2"),
                Div(
                    Button("Sign In", onclick="doLogin()",
                           cls="px-4 py-2 bg-black text-white rounded-md text-sm cursor-pointer border-none"),
                    Button("Cancel", onclick="document.getElementById('signin-overlay').classList.remove('visible')",
                           cls="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm cursor-pointer border-none ml-2"),
                    cls="flex gap-2",
                ),
                id="auth-form-login",
            ),
            # Register
            Div(
                P("Create an account — free and takes a few seconds.", cls="text-sm text-gray-500 mb-4"),
                Input(type="text", id="reg-name", placeholder="Name (optional)",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3"),
                Input(type="email", id="reg-email", placeholder="Email",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3"),
                Input(type="password", id="reg-password", placeholder="Password (min 6 chars)",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3",
                      onkeydown="if(event.key==='Enter')doRegister()"),
                Div(id="reg-error", cls="text-red-500 text-xs mb-2"),
                Div(id="reg-success", cls="text-green-600 text-xs mb-2"),
                Div(
                    Button("Register", onclick="doRegister()",
                           cls="px-4 py-2 bg-black text-white rounded-md text-sm cursor-pointer border-none"),
                    Button("Cancel", onclick="document.getElementById('signin-overlay').classList.remove('visible')",
                           cls="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm cursor-pointer border-none ml-2"),
                    cls="flex gap-2",
                ),
                id="auth-form-register", style="display:none",
            ),
            # Forgot
            Div(
                P("Enter your email to receive a reset link.", cls="text-sm text-gray-500 mb-4"),
                Input(type="email", id="forgot-email", placeholder="Email",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3",
                      onkeydown="if(event.key==='Enter')doForgot()"),
                Div(id="forgot-msg", cls="text-sm mb-2"),
                Div(
                    Button("Send Reset Link", onclick="doForgot()",
                           cls="px-4 py-2 bg-black text-white rounded-md text-sm cursor-pointer border-none"),
                    A("Back to login", href="#", onclick="switchAuthTab('login');return false",
                      cls="text-sm text-gray-500 ml-3"),
                    cls="flex items-center gap-2",
                ),
                id="auth-form-forgot", style="display:none",
            ),
            cls="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full",
        ),
        id="signin-overlay", cls="signin-overlay",
    )


# ── Left pane ────────────────────────────────────────────────────────────────

def left_pane(user_email=None, sessions=None, current_sid=""):
    sessions = sessions or []

    session_items = []
    for s in sessions[:30]:
        sid = str(s.get("id", ""))
        title = (s.get("title") or "New chat")[:40]
        active_cls = " active" if sid == current_sid else ""
        session_items.append(
            Div(
                A(title, href=f"/app?sid={sid}", cls="session-item-link"),
                cls=f"session-item{active_cls}",
            )
        )

    question_items = [
        Button(q, cls="nav-question", onclick=f"fillChat({json.dumps(q)}); sendMessage(null);")
        for q in SAMPLE_QUESTIONS
    ]

    link_items = [
        A(label, href=href, target="_blank", rel="noopener", cls="workspace-link")
        for label, href in PROFILE_LINKS
    ]

    project_groups = []
    for sector, items in PROJECTS_BY_SECTOR:
        project_groups.append(Div(
            H4(sector, cls="project-sector"),
            *[A(name, href=url, target="_blank", rel="noopener", cls="project-link")
              for name, url in items],
            cls="project-group",
        ))

    auth_section = (
        Div(
            Span(user_email, cls="text-xs text-gray-500 truncate"),
            Button("Sign out", onclick="signOut()",
                   cls="text-xs text-gray-400 hover:text-black cursor-pointer bg-transparent border-none"),
            cls="flex items-center justify-between gap-2 px-3 py-2",
        ) if user_email else
        Button("Sign in", onclick="showSignIn()",
               cls="w-full text-sm py-2 bg-black text-white rounded-md cursor-pointer border-none")
    )

    return Div(
        Div(
            A(
                Img(src=LOGO_IMG, alt="Julian Kaljuvee", cls="brand-logo"),
                Div(
                    Span("Talk to Julian", cls="brand-name"),
                    Span("kaljuvee.chat", cls="brand-sub"),
                    cls="brand-text",
                ),
                href="/app", cls="brand",
            ),
            Button("＋ New chat", onclick="newChat()", cls="new-chat-btn"),
            A(
                NotStr('<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'),
                Span("Visuals", cls="visuals-link-text"),
                href="/visuals", cls="visuals-link",
            ),
            cls="px-3 pt-3",
        ),
        Div(
            H4("Try asking", cls="section-label"),
            Div(*question_items, cls="nav-questions"),
            cls="agents-section",
        ),
        Div(
            H4("Recent", cls="section-label"),
            Div(*session_items, cls="session-list") if session_items else
            P("No conversations yet", cls="text-xs text-gray-400 px-3"),
            cls="history-section",
        ),
        Div(
            H4("Links", cls="section-label"),
            *link_items,
            H4("Selected projects", cls="section-label mt-3"),
            *project_groups,
            cls="agents-section",
        ),
        Div(auth_section, cls="auth-section"),
        cls="left-pane",
    )


# ── Center pane ──────────────────────────────────────────────────────────────

def center_pane(messages=None, current_agent_slug=None):
    messages = messages or []

    msg_els = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        bubble = Div(content, cls="msg-bubble")
        msg_els.append(Div(bubble, cls=f"msg msg-{role}"))

    sample_cards = [
        Button(Span(q, cls="sample-card-text"), cls="sample-card", title=q,
               onclick=f"fillChat({json.dumps(q)}); sendMessage(null);")
        for q in SAMPLE_QUESTIONS
    ]

    welcome = Div(
        Img(src=LOGO_IMG, alt="Julian Kaljuvee", cls="welcome-avatar"),
        H2("Talk to Julian", cls="welcome-title text-2xl font-display font-bold mb-1"),
        P("An AI assistant that never sleeps — ask anything about Julian Kaljuvee's "
          "career, skills, projects and experience.",
          cls="welcome-sub text-sm text-gray-500 max-w-md mx-auto"),
        id="welcome-hero", cls="welcome-hero",
        style="" if not messages else "display:none",
    )

    return Div(
        Div(
            Button(NotStr('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>'), cls="mobile-menu-btn", onclick="toggleLeftPane()"),
            Div(
                Img(src=LOGO_IMG, alt="Julian Kaljuvee", cls="chat-header-logo"),
                Span("Talk to Julian", id="current-agent-label", cls="chat-header-title"),
                cls="chat-header-brand",  # shown on mobile only (hidden on desktop via CSS)
            ),
            Div(
                Button(
                    NotStr('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>'),
                    id="share-chat-btn", onclick="shareChat()", cls="header-icon-btn", title="Share chat",
                ),
                Button(
                    NotStr('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'),
                    id="copy-chat-btn", onclick="copyChat()", cls="header-icon-btn", title="Copy chat",
                ),
                Button(
                    NotStr('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>'),
                    id="artifact-btn", onclick="toggleArtifactPane()", cls="header-icon-btn", title="Research & Talks",
                ),
                cls="chat-header-actions",
            ),
            cls="chat-header",
        ),
        Div(welcome, *msg_els, id="messages", cls="messages"),
        Form(
            Textarea(
                id="chat-input", name="msg", rows="1",
                placeholder="Ask about Julian's experience, skills or projects…",
                onkeydown="handleKey(event)", oninput="autoResize(this)",
            ),
            Button(
                NotStr('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>'),
                id="voice-btn", type="button", onclick="toggleVoice()", cls="voice-btn", title="Talk to Julian (voice)",
            ),
            Button("→", id="send-btn", type="button", onclick="sendMessage(event)", cls="send-btn"),
            cls="chat-form",
        ),
        # Persistent quick-question chips below the input — always visible, incl. mobile.
        Div(
            Div(*sample_cards, id="sample-cards-row", cls="sample-cards-row"),
            cls="sample-cards",
        ),
        Script(json.dumps({a.slug: list(a.example_prompts) for a in AGENTS}),
               id="agent-prompts-data", type="application/json"),
        cls="center-pane",
    )


# ── Right pane: Articles feed ────────────────────────────────────────────────

def _article_card(a):
    data_tags = ",".join(t.lower() for t in a["tags"])
    meta_bits = []
    if a["date"]:
        meta_bits.append(Span(a["date"], cls="article-date"))
    for t in a["tags"]:
        meta_bits.append(Span(t, cls="article-chip"))
    return A(
        Div(a["title"], cls="article-title"),
        Div(*meta_bits, cls="article-meta") if meta_bits else "",
        href=a["url"], target="_blank", rel="noopener",
        cls="article-card", **{"data-tags": data_tags},
    )


def right_pane():
    from utils.articles import load_articles, load_sections, all_tags
    articles = load_articles()
    tags = all_tags(articles)
    sections = load_sections()

    tag_chips = [Button("All", cls="article-tag active", onclick="filterArticles('all', this)")]
    tag_chips += [
        Button(t, cls="article-tag", onclick=f"filterArticles({json.dumps(t.lower())}, this)")
        for t in tags
    ]

    section_blocks = [
        Div(
            H4(name, cls="article-section-title"),
            *[_article_card(a) for a in items],
            cls="article-section", **{"data-section": name},
        )
        for name, items in sections
    ]

    body = (
        Div(
            Div(*tag_chips, cls="article-tags") if tags else "",
            Div(*section_blocks, id="article-list", cls="article-list"),
        ) if articles else
        P("No articles yet — check back soon.", cls="text-sm text-gray-400 px-4 py-8 text-center")
    )

    return Div(
        Div(
            Div(
                H4("Research and Talks", cls="artifact-title"),
                Span("Articles & talks by Julian", cls="artifact-subtitle"),
            ),
            Button(NotStr('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'), cls="right-pane-close", onclick="toggleArtifactPane()"),
            cls="artifact-header",
        ),
        body,
        # Open by default on desktop; chat.js collapses it on mobile at load.
        id="right-pane", cls="right-pane open",
    )
