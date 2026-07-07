/* Ask Julian — chat client (SSE streaming, 3-pane interactions). */

(() => {
    const $ = (sel) => document.querySelector(sel);

    let currentSessionId = getSidFromURL();
    let streaming = false;

    function getSidFromURL() {
        const p = new URLSearchParams(window.location.search);
        return p.get("sid") || "";
    }
    function setSid(sid) {
        currentSessionId = sid;
        const u = new URL(window.location);
        u.searchParams.set("sid", sid);
        history.replaceState(null, "", u);
    }

    function addBubble(role, text) {
        const wrap = document.createElement("div");
        wrap.className = `msg msg-${role}`;
        const bubble = document.createElement("div");
        bubble.className = "msg-bubble";
        bubble.textContent = text;
        wrap.appendChild(bubble);
        $("#messages").appendChild(wrap);
        scrollMessagesBottom();
        return bubble;
    }

    function scrollMessagesBottom() {
        const m = $("#messages");
        if (m) m.scrollTop = m.scrollHeight;
    }

    // Render a Plotly chart inline, below the assistant's message bubble.
    function renderChart(bubble, payload) {
        if (!payload || !payload.figure) return;
        const host = $("#messages");
        if (!host) return;
        const card = document.createElement("div");
        card.className = "chat-chart";
        if (payload.title) {
            const cap = document.createElement("div");
            cap.className = "chat-chart-title";
            cap.textContent = payload.title;
            card.appendChild(cap);
        }
        const plot = document.createElement("div");
        plot.className = "chat-chart-plot";
        card.appendChild(plot);
        host.appendChild(card);
        if (window.Plotly) {
            Plotly.newPlot(plot, payload.figure.data, payload.figure.layout,
                           { responsive: true, displayModeBar: false });
        }
        scrollMessagesBottom();
    }

    function renderMarkdownLite(text) {
        if (window.marked) return marked.parse(text);
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/\n/g, "<br>");
    }

    // -- Thinking indicator --
    let thinker = null;
    function showThinking(bubble) {
        if (!bubble) return;
        thinker = { started: Date.now(), el: document.createElement("div"), timerId: null };
        thinker.el.className = "thinking-indicator";
        thinker.el.innerHTML = `<span class="dot"></span><span class="label">Thinking… <span class="secs">0s</span></span>`;
        bubble.parentElement.insertBefore(thinker.el, bubble);
        thinker.timerId = setInterval(updateThinking, 500);
    }
    function updateThinking() {
        if (!thinker) return;
        const secs = Math.floor((Date.now() - thinker.started) / 1000);
        thinker.el.querySelector(".label").innerHTML = `Thinking… <span class="secs">${secs}s</span>`;
    }
    function hideThinking() {
        if (!thinker) return;
        clearInterval(thinker.timerId);
        if (thinker.el && thinker.el.parentElement) thinker.el.parentElement.removeChild(thinker.el);
        thinker = null;
    }

    // -- SSE send --
    async function sendMessage(evt) {
        if (evt) evt.preventDefault();
        if (streaming) return;
        const ta = $("#chat-input");
        if (!ta) return;
        const msg = ta.value.trim();
        if (!msg) return;

        streaming = true;
        const sendBtn = $("#send-btn");
        if (sendBtn) sendBtn.disabled = true;

        const wh = $("#welcome-hero");
        if (wh) wh.style.display = "none";

        addBubble("user", msg);
        ta.value = "";
        ta.style.height = "";

        const body = new URLSearchParams({ msg, sid: currentSessionId || "" });
        let resp;
        try {
            resp = await fetch("/app/chat", { method: "POST", body });
        } catch (e) {
            addBubble("assistant", "Network error. Please try again.");
            streaming = false; if (sendBtn) sendBtn.disabled = false; return;
        }
        if (!resp.ok) {
            addBubble("assistant", "Error: " + resp.status);
            streaming = false; if (sendBtn) sendBtn.disabled = false; return;
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let bubble = null;
        let accumulated = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            let idx;
            while ((idx = buffer.indexOf("\n\n")) !== -1) {
                const raw = buffer.slice(0, idx);
                buffer = buffer.slice(idx + 2);
                handleEvent(raw, (type, payload) => {
                    if (type === "gate") {
                        if (bubble) hideThinking();
                        addBubble("assistant", payload.message ||
                            "Please sign in to continue chatting.");
                        // Preserve the pending question + session across the sign-in reload.
                        try {
                            sessionStorage.setItem("aj_pending_q", msg);
                            if (currentSessionId) sessionStorage.setItem("aj_pending_sid", currentSessionId);
                        } catch (e) {}
                        showSignIn();
                    } else if (type === "agent_route") {
                        bubble = addBubble("assistant", "");
                        bubble.classList.add("streaming");
                        showThinking(bubble);
                    } else if (type === "token") {
                        if (!bubble) bubble = addBubble("assistant", "");
                        if (accumulated === "") hideThinking();
                        accumulated += payload.text;
                        bubble.innerHTML = renderMarkdownLite(accumulated);
                        scrollMessagesBottom();
                    } else if (type === "error") {
                        hideThinking();
                        if (!bubble) bubble = addBubble("assistant", "");
                        bubble.textContent = "Error: " + (payload.message || "unknown");
                    } else if (type === "session") {
                        if (payload.sid) setSid(payload.sid);
                    } else if (type === "chart") {
                        renderChart(bubble, payload);
                    } else if (type === "done") {
                        hideThinking();
                        if (bubble) bubble.classList.remove("streaming");
                    }
                });
            }
        }
        streaming = false;
        if (sendBtn) sendBtn.disabled = false;
    }

    function handleEvent(raw, cb) {
        let type = null; let data = "";
        for (const line of raw.split("\n")) {
            if (line.startsWith("event: ")) type = line.slice(7).trim();
            else if (line.startsWith("data: ")) data += line.slice(6);
        }
        if (!type) return;
        try { cb(type, data ? JSON.parse(data) : {}); }
        catch (e) { console.error("bad sse line", raw, e); }
    }

    // -- UI helpers --
    window.toggleLeftPane = () => {
        const lp = $(".left-pane");
        const lo = $(".left-overlay");
        if (lp) lp.classList.toggle("open");
        if (lo) lo.classList.toggle("visible");
    };
    window.toggleArtifactPane = () => {
        const r = $("#right-pane");
        const app = $(".app");
        const ro = $("#right-overlay");
        if (!r) return;
        if (r.classList.contains("open")) {
            r.classList.remove("open");
            if (app) app.classList.add("pane-closed");
            if (ro) ro.classList.remove("visible");
            const ab = $("#artifact-btn");
            if (ab) ab.classList.remove("active");
        } else {
            r.classList.add("open");
            if (app) app.classList.remove("pane-closed");
            if (ro && window.innerWidth <= 768) ro.classList.add("visible");
            const ab = $("#artifact-btn");
            if (ab) ab.classList.add("active");
        }
    };
    window.handleKey = (ev) => {
        if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); sendMessage(ev); }
    };
    window.autoResize = (el) => {
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, 240) + "px";
    };
    window.fillChat = (text) => {
        const ta = $("#chat-input");
        if (!ta) return;
        ta.value = text;
        ta.focus();
        autoResize(ta);
    };
    window.newChat = () => { window.location.href = "/app"; };

    // -- Article tag filter --
    window.filterArticles = (tag, btn) => {
        document.querySelectorAll(".article-tag").forEach(t => t.classList.remove("active"));
        if (btn) btn.classList.add("active");
        document.querySelectorAll(".article-card").forEach(card => {
            const tags = (card.getAttribute("data-tags") || "").split(",");
            card.style.display = (tag === "all" || tags.includes(tag)) ? "" : "none";
        });
    };

    // -- Share / copy --
    const _checkSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>';
    const _shareSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>';
    const _copySvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';

    function _flashIcon(btn, origSvg) {
        btn.innerHTML = _checkSvg;
        setTimeout(() => { btn.innerHTML = origSvg; }, 2000);
    }
    function _copyToClipboard(text, cb) {
        try { navigator.clipboard.writeText(text).then(cb, cb); } catch (e) { cb(); }
    }
    window.copyChat = () => {
        const msgs = document.querySelectorAll(".msg");
        const lines = [];
        msgs.forEach(m => {
            const role = m.classList.contains("msg-user") ? "You" : "Ask Julian";
            const bubble = m.querySelector(".msg-bubble");
            if (bubble) lines.push(`${role}: ${bubble.textContent.trim()}`);
        });
        const btn = $("#copy-chat-btn");
        _copyToClipboard(lines.join("\n\n"), () => { if (btn) _flashIcon(btn, _copySvg); });
    };
    window.shareChat = () => {
        if (!currentSessionId) return;
        const btn = $("#share-chat-btn");
        fetch("/api/share/" + currentSessionId, { method: "POST" })
            .then(r => r.json())
            .then(data => {
                if (data.url) {
                    const full = window.location.origin + data.url;
                    _copyToClipboard(full, () => { if (btn) _flashIcon(btn, _shareSvg); });
                }
            }).catch(() => {});
    };

    document.querySelectorAll(".msg-bubble").forEach(b => {
        if (window.marked) b.innerHTML = marked.parse(b.textContent);
    });

    // Right (Articles) pane: open by default on desktop, collapsed on mobile.
    if (window.innerWidth <= 768) {
        const rp = $("#right-pane");
        if (rp) rp.classList.remove("open");
        const app = $(".app");
        if (app) app.classList.add("pane-closed");
    } else {
        const ab = $("#artifact-btn");
        if (ab) ab.classList.add("active");
    }

    // Restore a question the visitor asked right before the sign-in gate.
    (function restorePending() {
        let q = null;
        try { q = sessionStorage.getItem("aj_pending_q"); } catch (e) {}
        if (!q) return;
        try {
            sessionStorage.removeItem("aj_pending_q");
            sessionStorage.removeItem("aj_pending_sid");
        } catch (e) {}
        const ta = $("#chat-input");
        if (ta) { ta.value = q; if (typeof autoResize === "function") autoResize(ta); }
        // If they're now signed in, continue the conversation automatically.
        if (document.body.dataset.signedIn === "1") {
            const wh = $("#welcome-hero");
            if (wh) wh.style.display = "none";
            sendMessage(null);
        }
    })();

    window.sendMessage = sendMessage;
})();

/* -- Auth functions (global, called from onclick handlers) -- */

function switchAuthTab(tab) {
    document.getElementById('auth-form-login').style.display = tab === 'login' ? '' : 'none';
    document.getElementById('auth-form-register').style.display = tab === 'register' ? '' : 'none';
    document.getElementById('auth-form-forgot').style.display = tab === 'forgot' ? '' : 'none';
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    const tabEl = document.getElementById('auth-tab-' + tab);
    if (tabEl) tabEl.classList.add('active');
}

function showForgotPassword(e) { e && e.preventDefault(); switchAuthTab('forgot'); }

function showSignIn() {
    document.getElementById('signin-overlay').classList.add('visible');
    switchAuthTab('login');
}

async function doLogin() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';
    if (!email || !password) { errEl.textContent = 'Email and password required'; return; }
    const resp = await fetch('/auth/login', { method: 'POST', body: new URLSearchParams({ email, password }) });
    const data = await resp.json();
    if (data.ok) location.reload();
    else if (data.error === 'no_password')
        errEl.innerHTML = 'No password set. <a href="#" onclick="showSetPassword(\'' + email + '\');return false" style="color:#000;font-weight:600;">Set one now</a>';
    else errEl.textContent = data.error || 'Login failed';
}

async function doRegister() {
    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const errEl = document.getElementById('reg-error');
    const okEl = document.getElementById('reg-success');
    errEl.textContent = ''; okEl.textContent = '';
    if (!email || !password) { errEl.textContent = 'Email and password required'; return; }
    const resp = await fetch('/auth/register', { method: 'POST', body: new URLSearchParams({ email, password, name }) });
    const data = await resp.json();
    if (data.ok) { okEl.textContent = data.message || 'Account created.'; setTimeout(() => location.reload(), 1200); }
    else errEl.textContent = data.error || 'Registration failed';
}

async function doForgot() {
    const email = document.getElementById('forgot-email').value.trim();
    const msgEl = document.getElementById('forgot-msg');
    msgEl.textContent = '';
    if (!email) { msgEl.textContent = 'Enter your email'; msgEl.style.color = '#DC2626'; return; }
    const resp = await fetch('/auth/forgot', { method: 'POST', body: new URLSearchParams({ email }) });
    const data = await resp.json();
    msgEl.style.color = '#16A34A';
    msgEl.textContent = data.message || 'Reset link sent if account exists';
}

function showSetPassword(email) {
    const form = document.getElementById('auth-form-login');
    form.innerHTML = '<p style="font-size:13px;color:#4B5563;margin-bottom:12px;">Set a password for <strong>' + email + '</strong></p>'
        + '<input type="password" id="set-pw-input" placeholder="New password (min 6 chars)" style="width:100%;padding:8px 12px;border:1px solid #E5E7EB;border-radius:6px;font-size:14px;margin-bottom:12px;">'
        + '<div id="set-pw-error" style="color:#DC2626;font-size:12px;margin-bottom:8px;"></div>'
        + '<button onclick="doSetPassword(\'' + email + '\')" style="padding:8px 16px;background:#000;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">Set Password</button>';
}

async function doSetPassword(email) {
    const password = document.getElementById('set-pw-input').value;
    const errEl = document.getElementById('set-pw-error');
    if (!password || password.length < 6) { errEl.textContent = 'Min 6 characters'; return; }
    const resp = await fetch('/auth/set-password', { method: 'POST', body: new URLSearchParams({ email, password }) });
    const data = await resp.json();
    if (data.ok) location.reload();
    else errEl.textContent = data.error || 'Failed';
}

function signOut() { fetch('/auth/logout', { method: 'POST' }).then(() => location.reload()); }
