"""Static site builder for E Worldwide Consulting.

    python3 -I build.py

Reads templates/ and content/, writes HTML pages, sitemap.xml and robots.txt into public/.
Standard library only. Hand-written assets live in public/assets/ and are not touched.
"""
import datetime
import html
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"

# When the site is served from a subpath (e.g. a GitHub Pages project page at
# github.io/REPO/ instead of a custom domain at the root), set BASE_PATH="/REPO"
# so root-relative hrefs/srcs in the templates resolve correctly. Leave unset
# for a custom domain or any host that serves the site at "/".
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")


def load(name):
    return json.loads((CONTENT / name).read_text())


SITE = load("site.json")
CASES = load("case_studies.json")["items"]
TEAM = load("team.json")
MILESTONES = load("milestones.json")["chapters"]
ARTICLES = load("insights.json")["articles"]
REVIEW = SITE.get("review_mode", False)
SITE_URL = SITE["site_url"]["value"].rstrip("/")
esc = html.escape

# slug, template, <title>, meta description, nav group, sitemap priority
PAGES = [
    ("index", "home", "E Worldwide Consulting | Technology, AI & Application Consulting, Atlanta",
     "E Worldwide Consulting helps organizations modernize applications, accelerate digital transformation and put AI to work through intelligent agents, automation and cloud solutions.", "", "1.0"),
    ("about", "about", "About Us | E Worldwide Consulting",
     "A founder-led technology consulting firm headquartered in Atlanta, Georgia, delivering strategy, engineering and AI solutions for clients in the United States and South Africa.", "company", "0.8"),
    ("services", "services", "Technology Consulting Services | AI, Applications, Cloud & Transformation",
     "AI agents, enterprise application development, cloud and DevOps, and digital transformation consulting from E Worldwide Consulting.", "services", "0.9"),
    ("ai-agents", "ai-agents", "AI Agent Development & Intelligent Automation Consulting | E Worldwide Consulting",
     "Design and delivery of governed, production-ready AI agents for workflows, customer service, document processing and enterprise knowledge.", "services", "0.9"),
    ("application-development", "application-development", "Enterprise Application Development | E Worldwide Consulting",
     "Custom web applications, enterprise platforms, APIs, integrations and application modernization built around business objectives.", "services", "0.9"),
    ("cloud-transformation", "cloud-transformation", "Cloud, DevOps & Digital Transformation Consulting | E Worldwide Consulting",
     "Cloud architecture and migration, CI/CD and DevOps, technology strategy, program delivery and data migration planning.", "services", "0.9"),
    ("industries", "industries", "Industries | E Worldwide Consulting",
     "How AI, modern applications, cloud and workflow modernization address needs in financial services, healthcare, public sector, retail and more.", "industries", "0.7"),
    ("case-studies", "case-studies", "Projects & Case Studies | United States and South Africa | E Worldwide Consulting",
     "Approved projects and case studies across the United States, South Africa and cross-border engagements.", "case-studies", "0.8"),
    ("global-presence", "global-presence", "Global Presence | Atlanta and South Africa | E Worldwide Consulting",
     "Atlanta, Georgia is our US base and South Africa a key market for international projects. Learn how we deliver across borders.", "company", "0.7"),
    ("founder", "founder", "Meet Vanessa Ross, Founder | E Worldwide Consulting",
     "Meet Vanessa Ross, founder of E Worldwide Consulting, and the story, philosophy and vision behind the company.", "company", "0.9"),
    ("team", "team", "Our Team | E Worldwide Consulting",
     "The people and multidisciplinary collaboration behind E Worldwide Consulting's work in the United States and South Africa.", "company", "0.6"),
    ("insights", "insights", "Insights & Thought Leadership | E Worldwide Consulting",
     "Practical perspectives on AI agents, enterprise applications, cloud modernization, technology leadership and cross-border delivery.", "insights", "0.7"),
    ("contact", "contact", "Contact Us | Schedule a Consultation | E Worldwide Consulting",
     "Discuss your project with E Worldwide Consulting. AI agents, application development, cloud and digital transformation.", "", "0.8"),
    ("privacy", "privacy", "Privacy Policy | E Worldwide Consulting",
     "How E Worldwide Consulting collects, uses and protects personal information.", "", "0.3"),
    ("terms", "terms", "Terms of Service | E Worldwide Consulting",
     "Terms governing use of the E Worldwide Consulting website.", "", "0.3"),
    ("404", "404", "Page Not Found | E Worldwide Consulting",
     "The page you requested could not be found.", "", None),
]

# Line icons, 24x24, drawn for this site
ICONS = {
    "app": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 6.5h.01M10 6.5h.01M8 13l-2 2 2 2M16 13l2 2-2 2M13 12l-2 6"/>',
    "agent": '<circle cx="12" cy="12" r="3"/><circle cx="4.5" cy="5" r="1.8"/><circle cx="19.5" cy="5" r="1.8"/><circle cx="4.5" cy="19" r="1.8"/><circle cx="19.5" cy="19" r="1.8"/><path d="M6 6.3l3.7 3.7M18 6.3l-3.7 3.7M6 17.7l3.7-3.7M18 17.7l-3.7-3.7"/>',
    "cloud": '<path d="M7 18h10.5a4 4 0 00.6-7.96A6 6 0 006.4 9.1 4.5 4.5 0 007 18z"/><path d="M12 11v5M9.5 13.5L12 11l2.5 2.5"/>',
    "strategy": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/><path d="M14 8l3-3 3 3M17 5v6"/>',
    "program": '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4M7 13h4M7 17h7M15 13l1.5 1.5L19 12"/>',
    "data": '<ellipse cx="9" cy="6" rx="6" ry="2.5"/><path d="M3 6v6c0 1.4 2.7 2.5 6 2.5M3 12v6c0 1.4 2.7 2.5 6 2.5"/><path d="M14 15h7M18 12l3 3-3 3"/>',
    "agile": '<path d="M20 12a8 8 0 11-2.3-5.6"/><path d="M20 4v4h-4"/><path d="M9 12l2 2 4-4"/>',
    "doc": '<path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "support": '<path d="M4 13v-1a8 8 0 0116 0v1"/><rect x="3" y="13" width="4" height="6" rx="1.5"/><rect x="17" y="13" width="4" height="6" rx="1.5"/><path d="M19 19a3 3 0 01-3 3h-3"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20.5 20.5L16 16"/><path d="M8.5 11h5M11 8.5v5"/>',
    "workflow": '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/><path d="M9 6h5a3 3 0 013 3v6M15 18h-5a3 3 0 01-3-3V9"/>',
    "shield": '<path d="M12 3l7.5 3v6c0 4.5-3.2 7.8-7.5 9-4.3-1.2-7.5-4.5-7.5-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "api": '<path d="M8 8l-5 4 5 4M16 8l5 4-5 4"/><circle cx="12" cy="12" r="1.5"/>',
    "people": '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0112 0"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.2A5 5 0 0121 19"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.5 3.7 5.5 3.7 9s-1.2 6.5-3.7 9M12 3C9.5 5.5 8.3 8.5 8.3 12s1.2 6.5 3.7 9"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "gauge": '<path d="M4 17a8 8 0 1116 0"/><path d="M12 17l4-6"/><circle cx="12" cy="17" r="1.2"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "code": '<path d="M9 7l-5 5 5 5M15 7l5 5-5 5"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "building": '<path d="M4 21V5a2 2 0 012-2h8a2 2 0 012 2v16M16 9h3a1 1 0 011 1v11M2 21h20M8 7h4M8 11h4M8 15h4"/>',
    "heart": '<path d="M12 20s-7.5-4.6-7.5-10A4.5 4.5 0 0112 7a4.5 4.5 0 017.5 3c0 5.4-7.5 10-7.5 10z"/><path d="M8 12h2l1-2 2 4 1-2h2"/>',
    "car": '<path d="M5 16h14v-4l-2-5H7l-2 5z"/><circle cx="8" cy="16.5" r="1.8"/><circle cx="16" cy="16.5" r="1.8"/><path d="M5 12h14"/>',
    "cart": '<path d="M3 4h2.5l2.2 11h10.6L20.5 8H7"/><circle cx="9.5" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2M3 13h18"/>',
    "factory": '<path d="M3 21V11l6 3v-3l6 3V5h4v16zM2 21h20"/><path d="M8 17h2M13 17h2"/>',
    "landmark": '<path d="M3 21h18M5 18h14M12 3l9 5H3zM6 10v8M10 10v8M14 10v8M18 10v8"/>',
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 10v7M8 7v.01M12 17v-4a2 2 0 014 0v4M12 10v7"/>',
}


def icon(name, cls="icon"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'


def tbc(text, note="Needs verification before launch"):
    """Inline marker for content that must be confirmed. Plain text when review mode is off."""
    if not REVIEW:
        return esc(text)
    return f'<span class="tbc" title="{esc(note)}">{esc(text)}</span>'


# ---------- Collection renderers ----------

CASE_FIELDS = ["Client context and industry", "Business challenge", "Project objectives",
               "Solution architecture and delivery approach", "Technologies used",
               "Implementation and collaboration model", "Verified outcomes", "Lessons learned"]


def case_card(c):
    region = esc(c["region"])
    if c["status"] != "published":
        fields = "".join(f"<li>{esc(f)}</li>" for f in CASE_FIELDS)
        return f'''<article class="case-card case-card--placeholder" data-region="{region}">
  <div class="case-card-top"><span class="chip">{region}</span><span class="status">Awaiting approval</span></div>
  <h3 class="h4">{esc(c["category"])}</h3>
  <p class="muted">Reserved for an approved engagement in this category. This slot is not a client story; it appears only in preview builds.</p>
  <ul class="case-fields">{fields}</ul>
</article>'''
    tech = "".join(f"<li>{esc(t)}</li>" for t in c.get("technologies", []))
    outcomes = "".join(f"<li>{esc(o)}</li>" for o in c.get("outcomes", []))
    return f'''<article class="case-card" data-region="{region}">
  <div class="case-card-top"><span class="chip">{region}</span><span class="muted">{esc(c.get("industry", ""))}</span></div>
  <h3 class="h4">{esc(c.get("client", c["category"]))}</h3>
  <dl class="case-dl">
    <dt>Challenge</dt><dd>{esc(c.get("challenge", ""))}</dd>
    <dt>Approach</dt><dd>{esc(c.get("approach", ""))}</dd>
    <dt>Technologies</dt><dd><ul class="tags">{tech}</ul></dd>
    <dt>Outcomes</dt><dd><ul>{outcomes}</ul></dd>
  </dl>
</article>'''


def case_cards(region=None):
    items = [c for c in CASES if (region is None or c["region"] == region)
             and (REVIEW or c["status"] == "published")]
    if not items:
        return ('<p class="empty-note">Approved case studies for this region are being prepared for publication. '
                '<a href="/contact.html">Ask us about relevant experience</a>.</p>')
    return '<div class="case-grid">' + "".join(case_card(c) for c in items) + "</div>"


def article_card(a, heading="h3"):
    status = '<span class="status">Draft for review</span>' if REVIEW and a["status"] == "draft" else ""
    return f'''<article class="insight-card">
  <a href="/insights/{a["slug"]}.html" class="insight-link">
    <div class="insight-meta"><span class="eyebrow">{esc(a["category"])}</span>{status}</div>
    <{heading} class="h4">{esc(a["title"])}</{heading}>
    <p>{esc(a["summary"])}</p>
    <span class="text-link">Read the article {icon("arrow", "icon icon--sm")}</span>
  </a>
</article>'''


def insights_cards():
    return '<div class="insight-grid">' + "".join(article_card(a) for a in ARTICLES) + "</div>"


def timeline():
    out = ['<ol class="timeline">']
    for i, ch in enumerate(MILESTONES, 1):
        date = esc(ch["date"]) if ch["date"] else tbc("Date to be confirmed")
        status = '<span class="status">Draft, pending founder approval</span>' if REVIEW and ch["status"] == "draft" else ""
        events = "".join(f"<li>{esc(e)}</li>" for e in ch.get("events", []))
        events_html = f'<ul class="timeline-events">{events}</ul>' if events else ""
        out.append(f'''<li class="timeline-item reveal">
  <div class="timeline-marker" aria-hidden="true"><span>{i:02d}</span></div>
  <div class="timeline-body">
    <p class="timeline-date">{date}</p>
    <h3 class="h3">{esc(ch["title"])}: <span class="accent-text">{esc(ch["subtitle"])}</span></h3>
    <p>{esc(ch["body"])}</p>{events_html}
    {status}
  </div>
</li>''')
    out.append("</ol>")
    return "".join(out)


def team_cards():
    out = ['<div class="team-grid">']
    for m in TEAM["members"]:
        initials = "".join(p[0] for p in m["name"].split()[:2])
        status = '<span class="status">Profile pending approval</span>' if REVIEW and not m.get("approved") else ""
        expertise = "".join(f"<li>{esc(e)}</li>" for e in m.get("expertise", []))
        link = (f'<a class="text-link" href="{esc(m["link"])}" rel="noopener" target="_blank">{icon("linkedin", "icon icon--sm")} Professional profile'
                f'<span class="sr-only"> (opens in a new tab)</span></a>') if m.get("link") else ""
        out.append(f'''<article class="team-card">
  <div class="portrait portrait--sm" aria-hidden="true"><span>{esc(initials)}</span></div>
  <div><h3 class="h4">{esc(m["name"])}</h3><p class="team-title">{esc(m["title"])}</p>{status}</div>
  <p>{esc(m["bio"])}</p>
  <ul class="tags">{expertise}</ul>
  {link}
</article>''')
    out.append("</div>")
    return "".join(out)


def jsonld():
    data = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": SITE["name"],
        "url": SITE_URL + "/",
        "slogan": SITE["tagline"],
        "areaServed": [{"@type": "Country", "name": "United States"}, {"@type": "Country", "name": "South Africa"}],
        "address": {"@type": "PostalAddress", "addressLocality": "Atlanta", "addressRegion": "GA", "addressCountry": "US"},
        "founder": {"@type": "Person", "name": SITE["founder"]["name"], "sameAs": SITE["founder"]["linkedin"]},
    }
    if SITE["contact_email"]["verified"]:
        data["email"] = SITE["contact_email"]["value"]
    return json.dumps(data, separators=(",", ":"))


# ---------- Rendering ----------

TOKEN = re.compile(r"\{\{([\w-]+)(?::([\w-]+))?\}\}")


REVIEW_BLOCK = re.compile(r"<!--review-->.*?<!--/review-->", re.S)


def render(text, ctx):
    # Blocks wrapped in <!--review-->...<!--/review--> exist only to prompt verification; drop them in production.
    if not REVIEW:
        text = REVIEW_BLOCK.sub("", text)

    def sub(m):
        key, arg = m.group(1), m.group(2)
        if key == "icon":
            return icon(arg)
        if key == "active":
            return 'data-active="true"' if ctx.get("group") == arg else ""
        if key == "cases":
            return case_cards({"us": "United States", "za": "South Africa", "global": "Cross-border"}.get(arg) if arg else None)
        if key in ctx:
            v = ctx[key]
            return v() if callable(v) else str(v)
        raise KeyError(f"Unknown template token {{{{{m.group(0)}}}}}")
    return TOKEN.sub(sub, text)


def founded_in():
    fy = SITE["founding_year"]
    if fy["verified"] and fy["value"]:
        return f" in {esc(str(fy['value']))}"
    return " in " + tbc("[founding year]", fy["note"]) if REVIEW else ""


def base_context():
    email = SITE["contact_email"]
    sa = SITE["south_africa_office"]
    return {
        "site_url": SITE_URL,
        "email": esc(email["value"]),
        "email_display": tbc(email["value"], email["note"]) if not email["verified"] else esc(email["value"]),
        "sa_presence": esc(sa["value"]) if sa["verified"] and sa["value"] else tbc("Nature of local presence to be confirmed", sa["note"]),
        "linkedin": esc(SITE["founder"]["linkedin"]),
        "year": datetime.date.today().year,
        "map": (TEMPLATES / "partials" / "world-map.svg").read_text(),
        "insights_cards": insights_cards,
        "timeline": timeline,
        "team_cards": team_cards,
        "founded_in": founded_in(),
        "founder_portrait_note": "Approved portrait pending" if REVIEW else "",
        "jsonld": jsonld(),
        "review_class": " is-review" if REVIEW else "",
        "review_banner": (
            '<div class="review-banner" role="note"><div class="container">Preview build. '
            '<span class="tbc">Dotted-underlined items</span> and labeled drafts need verification or approval before launch.</div></div>'
        ) if REVIEW else "",
    }


def write_page(slug, body, title, description, group, out_path, robots="index,follow"):
    layout = (TEMPLATES / "layout.html").read_text()
    ctx = base_context()
    path = "/" if slug == "index" else f"/{out_path.relative_to(PUBLIC).as_posix()}"
    ctx.update(slug=slug, group=group, title=esc(title), og_title=esc(title.split(" | ")[0]),
               description=esc(description), canonical=SITE_URL + path, robots=robots)
    ctx["body"] = render(body, ctx)
    page = render(layout, ctx)
    if BASE_PATH:
        # Rewrite root-relative hrefs/srcs (not full URLs or protocol-relative "//...") to the subpath.
        page = re.sub(r'(href|src|action)="/(?!/)', '\\1="' + BASE_PATH + '/', page)
    if not REVIEW and 'class="tbc"' in page:
        UNRESOLVED.append(out_path.relative_to(PUBLIC).as_posix())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page)


UNRESOLVED = []


def build():
    urls = []
    for slug, tpl, title, desc, group, prio in PAGES:
        body = (TEMPLATES / "pages" / f"{tpl}.html").read_text()
        out = PUBLIC / f"{slug}.html"
        write_page(slug, body, title, desc, group, out, robots="noindex" if slug == "404" else "index,follow")
        if prio:
            urls.append(("/" if slug == "index" else f"/{slug}.html", prio))

    article_tpl = (TEMPLATES / "pages" / "article.html").read_text()
    for a in ARTICLES:
        status = ('<p class="status status--block">Draft for editorial review. Not yet published.</p>'
                  if REVIEW and a["status"] == "draft" else "")
        date = esc(a["date"]) if a["date"] else tbc("Publication date pending")
        others = "".join(article_card(o) for o in ARTICLES if o["slug"] != a["slug"])
        body = (article_tpl.replace("[[title]]", esc(a["title"])).replace("[[category]]", esc(a["category"]))
                .replace("[[summary]]", esc(a["summary"])).replace("[[reading_time]]", str(a["reading_time"]))
                .replace("[[date]]", date).replace("[[status]]", status).replace("[[body]]", a["body"])
                .replace("[[related]]", f'<div class="insight-grid insight-grid--2">{others}</div>'))
        write_page(f"article-{a['slug']}", body, f"{a['title']} | E Worldwide Consulting", a["summary"],
                   "insights", PUBLIC / "insights" / f"{a['slug']}.html")
        urls.append((f"/insights/{a['slug']}.html", "0.6"))

    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{today}</lastmod><priority>{p}</priority></url>" for u, p in urls]
    sm.append("</urlset>")
    (PUBLIC / "sitemap.xml").write_text("\n".join(sm) + "\n")
    (PUBLIC / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    print(f"Built {len(urls) + 1} pages into {PUBLIC.relative_to(ROOT)}/ (review mode: {'on' if REVIEW else 'off'})")
    if UNRESOLVED:
        print("WARNING: production build still contains unverified placeholders in:\n  " + "\n  ".join(UNRESOLVED))
        raise SystemExit(1)


if __name__ == "__main__":
    build()
