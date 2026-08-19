"""Canonical FastSME/Fast* portfolio data used by chat grounding and navigation."""

from __future__ import annotations


FASTSME_SITE = "https://fastsme.com"
GITHUB_ORG = "https://github.com/predictivelabsai"


# Customer-facing portfolio, kept in the same groups as the FastSME landing site.
FASTSME_GROUPS = [
    ("Collaborate & communicate", [
        ("FastOffice", "Productivity suite", "https://office.fastsme.com"),
        ("FastCal", "Calendar & scheduling", "https://cal.fastsme.com"),
        ("FastMail", "Email", "https://mail.fastsme.com"),
        ("FastDrive", "Files", "https://drive.fastsme.com"),
        ("FastDocs", "Documents", "https://docs.fastsme.com"),
        ("FastSheets", "Spreadsheets", "https://sheets.fastsme.com"),
        ("FastSlides", "Presentations", "https://slides.fastsme.com"),
        ("FastMeet", "Meetings", "https://meet.fastsme.com"),
    ]),
    ("Grow & serve customers", [
        ("FastFunnel", "Autonomous marketing", "https://funnel.fastsme.com"),
        ("FastCRM", "Sales CRM", "https://crm.fastsme.com"),
        ("FastHelpdesk", "Customer support", "https://helpdesk.fastsme.com"),
        ("FastVoice", "Voice automation", "https://voice.fastsme.com"),
        ("FastSocial", "Social media", "https://fastsocial.org"),
        ("FastESM", "Service management", "https://esm.fastsme.com"),
    ]),
    ("Operate & govern", [
        ("FastERP", "ERP & accounting", "https://erp.fastsme.com"),
        ("FastFPA", "Financial planning", "https://fpa.fastsme.com"),
        ("FastHRM", "People operations", "https://hrm.fastsme.com"),
        ("FastPPM", "Projects & portfolios", "https://ppm.fastsme.com"),
        ("FastCMS", "Content management", "https://cms.fastsme.com"),
        ("FastDataGov", "Data governance", "https://datagov.fastsme.com"),
        ("FastSSO", "Enterprise identity", "https://sso.fastsme.com"),
    ]),
    ("Learn & analyse", [
        ("FastBI", "Business intelligence", "https://bi.fastsme.com"),
        ("FastLMS", "Learning management", "https://lms.fastsme.com"),
    ]),
    ("Finance & investment", [
        ("FastFund", "Family office", "https://fund.fastsme.com"),
        ("FastVC", "Venture capital", "https://vc.fastsme.com"),
        ("FastPE", "Private equity", "https://pe.fastsme.com"),
        ("FastFactoring", "Invoice finance", "https://fastfactoring.org"),
    ]),
    ("Booking & care", [
        ("FastBooking", "Booking & commerce", "https://booking.fastsme.com"),
        ("FastClinic", "Clinic operations", "https://clinic.fastsme.com"),
    ]),
]


# All public, capital-F Fast* repositories in predictivelabsai as of 2026-08-19.
# Description and homepage values mirror GitHub repository metadata.
FAST_REPOSITORIES = [
    ("FastAccounts", "", ""),
    ("FastATS", "", ""),
    ("FastBI", "Open-source business intelligence with dashboards and conversational SQL/Cypher.", "https://bi.fastsme.com"),
    ("FastBooking", "Multi-tenant booking and commerce for facilities, hospitality, clinics and events.", "https://booking.fastsme.com"),
    ("FastCMS", "Content management with page trees, workflows, revisions, forms and a headless API.", "https://cms.fastsme.com"),
    ("FastCRE", "AI squad for commercial-real-estate underwriting, closing and deal management.", ""),
    ("FastCal", "Team calendar, public booking links and availability scheduling.", "https://cal.fastsme.com"),
    ("FastCity", "Smart-city IoT registry, telemetry, maps, alarms and AI assistance.", ""),
    ("FastClinic", "Multi-specialty clinic operations, appointments, invoicing, recall and revenue.", "https://clinic.fastsme.com"),
    ("FastCRM", "Sales CRM with leads, contacts, tasks, activity and a Kanban pipeline.", "https://crm.fastsme.com"),
    ("FastDataGov", "Data catalog, glossary, lineage, quality, stewardship and access requests.", "https://datagov.fastsme.com"),
    ("FastDevOps", "FastSME development and operations tooling.", ""),
    ("FastDocs", "Server-rendered document editor with blocks, templates, versions and public links.", "https://docs.fastsme.com"),
    ("FastDrive", "File manager with sharing, permissions, uploads, trash and AI assistance.", "https://drive.fastsme.com"),
    ("FastERP", "ERP for order-to-cash, procurement, inventory, accounting and AI operations.", "https://erp.fastsme.com"),
    ("FastESM", "Enterprise service management with catalog, approvals, RBAC, SLAs and knowledge.", "https://esm.fastsme.com"),
    ("FastFPA", "Driver-based budgets, forecasts, scenarios, variance analysis and statements.", "https://fpa.fastsme.com"),
    ("FastFactoring", "Invoice-financing from onboarding and verification through settlement.", "https://fastfactoring.org"),
    ("FastFund", "Family-office relationships, portfolios, entities, tax and compliance.", "https://fund.fastsme.com"),
    ("FastGTM", "", ""),
    ("FastGrants", "Grant and EU-funds lifecycle from calls through beneficiary reporting.", ""),
    ("FastHRM", "HR platform for employee records, leave, attendance, payroll and payslips.", "https://hrm.fastsme.com"),
    ("FastHealthData", "Health research data lifecycle, OMOP/FHIR catalog, governance and cohorts.", ""),
    ("FastHelpdesk", "Support desk with queues, SLA timers, conversations, knowledge and AI triage.", "https://helpdesk.fastsme.com"),
    ("FastLCA", "Whole-building life-cycle carbon assessment aligned with EN 15978.", ""),
    ("FastLMS", "Learning platform with courses, quizzes, progress, tutoring and gamification.", "https://lms.fastsme.com"),
    ("FastLegal", "AI-powered legal document analysis.", ""),
    ("FastMSR", "Mortgage Servicing Rights management with simulated Freddie Mac CRX.", ""),
    ("FastMail", "Webmail with threads, contacts, summaries and AI reply drafting.", "https://mail.fastsme.com"),
    ("FastMeet", "Meeting scheduler with rooms, agendas and AI-generated summaries.", "https://meet.fastsme.com"),
    ("FastOffice", "FastSME productivity suite and shared identity/control plane.", "https://office.fastsme.com"),
    ("FastPE", "Agentic private-equity workspace from sourcing through portfolio operations.", "https://pe.fastsme.com"),
    ("FastPPM", "Project portfolio management with ingestion, Gantt, value tracking and AI analysis.", "https://ppm.fastsme.com"),
    ("FastSSO", "Enterprise SSO broker connecting applications to SAML/OIDC providers.", "https://sso.fastsme.com"),
    ("FastSheets", "Spreadsheet with editable grid, formulas, multiple sheets and AI assistance.", "https://sheets.fastsme.com"),
    ("FastSlides", "Presentation builder with themes, presenting and AI deck generation.", "https://slides.fastsme.com"),
    ("FastSocial", "Multi-brand social publishing, scheduling, analytics, inboxes and listening.", "https://fastsocial.org"),
    ("FastSurvey", "", ""),
    ("FastVC", "AI workspace for venture sourcing, screening, diligence, IC, LPs and portfolios.", "https://vc.fastsme.com"),
    ("FastVoice", "Self-hosted voice agents with workflows, telephony, tools, MCP and SDKs.", "https://voice.fastsme.com"),
    ("FastWiki", "", ""),
]


def grounding_markdown() -> str:
    """Render compact factual context for the LLM system prompt."""
    lines = [
        "# FastSME and Predictive Labs Fast* projects",
        "",
        ("FastSME is an open-source business-software portfolio for SMEs and SMBs. "
         f"Portfolio: {FASTSME_SITE}/products. Source organisation: {GITHUB_ORG}."),
        "When asked for a project, provide both its GitHub repository and live site when listed.",
        "A blank description means GitHub currently supplies no project description; do not invent one.",
        "",
    ]
    for name, description, site in FAST_REPOSITORIES:
        details = description or "No public description supplied."
        links = f"GitHub: {GITHUB_ORG}/{name}"
        if site:
            links += f"; site: {site}"
        lines.append(f"- {name} — {details} {links}")
    lines.extend([
        "",
        ("FastFunnel is also in the FastSME customer-facing portfolio at "
         "https://funnel.fastsme.com; no capital-F public repository was returned by GitHub."),
    ])
    return "\n".join(lines)
