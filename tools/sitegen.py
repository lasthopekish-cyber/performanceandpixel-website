#!/usr/bin/env python3
"""Performance and Pixel site generator.

Builds new service pages and blog posts from a JSON spec, reusing the exact
template (styles, logo, header, footer, scripts) of the existing site, and
keeps blog/index.html, sitemap.xml and llms.txt in sync.

Usage:
  python3 tools/sitegen.py page content/pages/<slug>.json
  python3 tools/sitegen.py post content/posts/<slug>.json
  python3 tools/sitegen.py check            # validate every page

Spec fields (both kinds):
  slug, seo_title, description, h1, h1_accent (optional, highlighted tail of h1),
  kicker, crumb, lead (html), sections: [{id, h2, html}], faqs: [[q, a]],
  related: [[href, small, title]], cta_h2, cta_p, wa_text
Page-only: service_type, offers: [..], area: "Delhi NCR" | "Dwarka"
Post-only: category (must be one of blog filter categories), date (YYYY-MM-DD),
  headline, card_title, card_text, cover_labels: [label1, label2], accent (#hex),
  llms_section ("Guides" or "Industry guides")
"""
import html as H
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://performanceandpixel.com/"
PAGE_TEMPLATE = ROOT / "local-seo-services-delhi-ncr.html"
POST_TEMPLATE = ROOT / "blog/how-to-get-solar-leads-delhi-ncr.html"
CATEGORIES = ["Education", "Healthcare", "Real estate", "Solar", "D2C and ecommerce",
              "Food and hospitality", "Beauty and wellness", "B2B and startups",
              "Paid ads", "Local SEO"]
CAT_COLORS = {"Education": "#4D7CFF", "Healthcare": "#1FA070", "Real estate": "#9B6BFF",
              "Solar": "#FFB547", "D2C and ecommerce": "#FF4FB4", "Food and hospitality": "#FF7A45",
              "Beauty and wellness": "#E85AA8", "B2B and startups": "#33D6F2",
              "Paid ads": "#9B6BFF", "Local SEO": "#3DDC97"}
AREAS = ["Delhi", "Gurugram", "Noida", "Greater Noida", "Ghaziabad", "Faridabad"]
ADDRESS = {"@type": "PostalAddress", "streetAddress": "124, Triveni Heights, Dwarka",
           "addressLocality": "New Delhi", "addressRegion": "Delhi", "addressCountry": "IN"}

esc = lambda s: H.escape(s, quote=True)
strip_tags = lambda s: re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def provider():
    return {"@type": "ProfessionalService", "@id": SITE + "#agency", "name": "Performance and Pixel",
            "url": SITE, "email": "support@performanceandpixel.com", "telephone": "+91-8130829730",
            "address": ADDRESS}


def faq_ld(faqs):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
        for q, a in faqs]}


def faq_html(faqs):
    out = []
    for i, (q, a) in enumerate(faqs):
        body = a if a.lstrip().startswith("<") else f"<p>{a}</p>"
        out.append(f'<details class="glass"{" open" if i == 0 else ""}><summary>{esc(q)}</summary>{body}</details>')
    return '<div class="faqs">' + "".join(out) + "</div>"


def related_html(rel, prefix):
    def fix(h):
        return h if h.startswith(("http", "#", "../")) or not prefix else prefix + h
    return '<div class="related">' + "".join(
        f'<a href="{fix(h)}"><small>{esc(s)}</small><b>{esc(t)}</b></a>' for h, s, t in rel) + "</div>"


def cta_html(spec, prefix):
    wa = "https://wa.me/918130829730?text=" + re.sub(r"[^A-Za-z0-9._~-]",
                                                    lambda m: "%" + "%".join(f"{b:02X}" for b in m.group().encode()),
                                                    spec["wa_text"])
    return f'''<section class="sec" id="contact">
    <div class="wrap">
      <div class="cta glass edge">
        <div>
          <span class="kicker"><i></i>Free strategy call</span>
          <h2>{esc(spec["cta_h2"])}</h2>
          <p>{esc(spec["cta_p"])}</p>
        </div>
        <div class="actions">
          <a class="btn btn-wa" href="{wa}" target="_blank" rel="noopener">__WA_SVG__Chat on WhatsApp</a>
          <a class="btn btn-main" href="{prefix}index.html#contact">Book a free strategy call</a>
        </div>
      </div>
    </div>
  </section>'''


def swap_head(tpl, spec, url, ld):
    t = spec["seo_title"]
    d = spec["description"]
    tpl = re.sub(r"<title>.*?</title>", f"<title>{esc(t)}</title>", tpl, count=1)
    tpl = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + esc(d), tpl, count=1)
    tpl = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + url, tpl, count=1)
    tpl = re.sub(r'(<meta property="og:url" content=")[^"]*', lambda m: m.group(1) + url, tpl, count=1)
    tpl = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + esc(t), tpl, count=1)
    tpl = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + esc(d), tpl, count=1)
    if spec.get("og_image"):
        tpl = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")[^"]*',
                     lambda m: m.group(1) + spec["og_image"], tpl)
    if spec.get("geo_placename"):
        tpl = re.sub(r'(<meta name="geo.placename" content=")[^"]*', lambda m: m.group(1) + spec["geo_placename"], tpl)
    ld_txt = json.dumps({"@context": "https://schema.org", "@graph": ld}, indent=1, ensure_ascii=False)
    tpl = re.sub(r'<script type="application/ld\+json">.*?</script>',
                 lambda m: f'<script type="application/ld+json">\n{ld_txt}\n</script>', tpl, count=1, flags=re.S)
    return tpl


def wa_svg(tpl):
    m = re.search(r'<a class="btn btn-wa"[^>]*>(<svg.*?</svg>)', tpl, re.S)
    return m.group(1) if m else ""


def h1_html(spec):
    h1, acc = spec["h1"], spec.get("h1_accent")
    if acc and h1.endswith(acc):
        return esc(h1[: -len(acc)]) + f'<span class="sunt">{esc(acc)}</span>'
    return esc(h1)


def build_page(spec):
    slug = spec["slug"]
    url = SITE + slug + ".html"
    tpl = PAGE_TEMPLATE.read_text()
    crumb_name = spec["crumb"]
    areas = spec.get("areas") or AREAS
    ld = [
        {"@type": "WebPage", "@id": url, "url": url, "name": strip_tags(spec["h1"]), "inLanguage": "en-IN",
         "isPartOf": {"@id": SITE + "#website"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": "Delhi NCR", "item": SITE + "digital-marketing-agency-delhi-ncr.html"},
            {"@type": "ListItem", "position": 3, "name": crumb_name, "item": url}]},
        {"@type": "Service", "name": strip_tags(spec["h1"]), "serviceType": spec["service_type"], "url": url,
         "provider": provider(),
         "areaServed": [{"@type": "City", "name": a} for a in areas] + [{"@type": "Country", "name": "India"}],
         "hasOfferCatalog": {"@type": "OfferCatalog", "name": spec["service_type"], "itemListElement": [
             {"@type": "Offer", "itemOffered": {"@type": "Service", "name": o}} for o in spec["offers"]]}},
        faq_ld(spec["faqs"]),
    ]
    tpl = swap_head(tpl, spec, url, ld)
    secs = []
    for i, s in enumerate(spec["sections"]):
        style = ' style="padding-top:30px"' if i == 0 else ' style="border-top:1px solid var(--edge)"'
        kick = f'<span class="kicker"><i></i>{esc(s["kicker"])}</span>\n      ' if s.get("kicker") else ""
        secs.append(f'''  <section class="sec" id="{s["id"]}"{style}>
    <div class="wrap">
      {kick}<h2 class="h2 reveal">{esc(s["h2"])}</h2>
      {s["html"]}
    </div>
  </section>''')
    main = f'''<main>
<section class="pagehero">
    <div class="wrap">
      <nav class="crumb" aria-label="Breadcrumb"><a href="index.html">Home</a><span aria-hidden="true">/</span><a href="digital-marketing-agency-delhi-ncr.html">Delhi NCR</a><span aria-hidden="true">/</span><span>{esc(crumb_name)}</span></nav>
      <span class="kicker"><i></i>{esc(spec["kicker"])}</span>
      <h1>{h1_html(spec)}</h1>
      <p class="lead">{spec["lead"]}</p>
      <div class="actions"><a class="btn btn-main" href="#contact">{esc(spec.get("hero_cta", "Book a free strategy call"))}</a><a class="btn btn-ghost" href="#{spec["sections"][0]["id"]}">{esc(spec.get("hero_cta2", "See what we do"))}</a></div>
    </div>
  </section>
{chr(10).join(secs)}
  <section class="sec" id="faq" style="border-top:1px solid var(--edge)">
    <div class="wrap">
      <span class="kicker"><i></i>Questions</span>
      <h2 class="h2 reveal">{esc(spec.get("faq_h2", "Frequently asked questions."))}</h2>
      {faq_html(spec["faqs"])}
      {related_html(spec.get("related", []), "")}
    </div>
  </section>
  {cta_html(spec, "")}
</main>'''
    main = main.replace("__WA_SVG__", wa_svg(tpl))
    out = re.sub(r"<main>.*?</main>", lambda m: main, tpl, count=1, flags=re.S)
    path = ROOT / (slug + ".html")
    path.write_text(out)
    update_sitemap(url, 0.9)
    return path


def reading_minutes(text):
    return max(2, round(len(text.split()) / 220))


def build_post(spec):
    slug = spec["slug"]
    url = SITE + "blog/" + slug + ".html"
    cat = spec["category"]
    assert cat in CATEGORIES, f"category must be one of {CATEGORIES}"
    d = spec.get("date") or date.today().isoformat()
    tpl = POST_TEMPLATE.read_text()
    body_text = strip_tags(spec["intro"] + " ".join(s["html"] for s in spec["sections"]))
    words = len(body_text.split())
    cover_rel = f"img/{slug}.jpg"
    make_cover(ROOT / "blog" / cover_rel, spec.get("cover_labels", [cat, "New enquiry"]),
               spec.get("accent") or CAT_COLORS.get(cat, "#9B6BFF"))
    spec = dict(spec, og_image=url.rsplit("/", 1)[0] + "/" + cover_rel)
    ld = [
        {"@type": "BlogPosting", "@id": url + "#article", "mainEntityOfPage": url, "headline": spec["headline"],
         "description": spec["description"], "datePublished": d, "dateModified": d, "inLanguage": "en-IN",
         "image": spec["og_image"], "wordCount": words,
         "author": {"@type": "Organization", "name": "Performance and Pixel", "url": SITE},
         "publisher": {"@type": "Organization", "name": "Performance and Pixel", "url": SITE,
                       "logo": {"@type": "ImageObject", "url": SITE + "og-image.png"}},
         "about": spec.get("about", cat), "isPartOf": {"@id": SITE + "#website"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "blog/index.html"},
            {"@type": "ListItem", "position": 3, "name": spec["headline"], "item": url}]},
        faq_ld(spec["faqs"]),
    ]
    tpl = swap_head(tpl, spec, url, ld)
    toc = "".join(f'<li><a href="#{s["id"]}">{esc(s["h2"])}</a></li>' for s in spec["sections"])
    toc += '<li><a href="#faq">FAQs</a></li>'
    secs = "".join(f'<h2 id="{s["id"]}">{esc(s["h2"])}</h2>{s["html"]}' for s in spec["sections"])
    pretty = date.fromisoformat(d).strftime("%-d %B %Y")
    main = f'''<main>
<article>
  <section class="pagehero" style="padding-bottom:10px">
    <div class="wrap prose" style="margin:0 auto">
      <nav class="crumb" aria-label="Breadcrumb"><a href="../index.html">Home</a><span aria-hidden="true">/</span><a href="../blog/index.html">Blog</a><span aria-hidden="true">/</span><span>{esc(spec.get("crumb", cat))}</span></nav>
      <span class="kicker"><i></i>{esc(spec.get("kicker", cat))}</span>
      <h1 style="max-width:none;font-size:clamp(36px,4.8vw,62px)">{esc(spec["headline"])}</h1>
      <p class="meta-line">By the Performance and Pixel team · <time datetime="{d}">{pretty}</time> · {reading_minutes(body_text)} min read</p>
    </div>
  </section>
  <section class="sec" style="padding-top:20px">
    <div class="wrap">
      <div class="prose">
        {spec["intro"]}
        <nav class="toc" aria-label="In this article"><b>In this article</b><ol>{toc}</ol></nav>
        {secs}
        <h2 id="faq">Frequently asked questions</h2>
        {faq_html(spec["faqs"])}
        {related_html(spec.get("related", []), "../")}
      </div>
    </div>
  </section>
</article>
{cta_html(spec, "../")}
</main>'''
    main = main.replace("__WA_SVG__", wa_svg(tpl))
    out = re.sub(r"<main>.*?</main>", lambda m: main, tpl, count=1, flags=re.S)
    path = ROOT / "blog" / (slug + ".html")
    path.write_text(out)
    add_to_blog_index(slug, cat, spec["card_title"], spec["card_text"], cover_rel)
    update_sitemap(url, 0.7, d)
    update_llms(spec.get("llms_section", "Industry guides"), spec["card_title"], url, cat)
    return path, words


def add_to_blog_index(slug, cat, title, text, cover_rel):
    p = ROOT / "blog/index.html"
    h = p.read_text()
    href = f"../blog/{slug}.html"
    if href in h:
        return
    color = CAT_COLORS.get(cat, "#9B6BFF")
    card = (f'<a class="post glass reveal" data-cat="{esc(cat)}" href="{href}" style="--c:{color}">'
            f'<img src="../blog/{cover_rel}" width="1200" height="630" alt="" loading="lazy">'
            f'<span class="tag">{esc(cat)}</span><h2>{esc(title)}</h2><p>{esc(text)}</p>'
            f'<span class="go">Read article</span></a>')
    h = h.replace('<div class="postlist" id="postlist">', '<div class="postlist" id="postlist">' + card, 1)
    p.write_text(h)


def update_sitemap(url, prio, lastmod=None):
    p = ROOT / "sitemap.xml"
    s = p.read_text()
    lastmod = lastmod or date.today().isoformat()
    line = f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod><priority>{prio}</priority></url>"
    if f"<loc>{url}</loc>" in s:
        s = re.sub(rf"  <url><loc>{re.escape(url)}</loc>.*?</url>", line, s)
    else:
        s = s.replace("</urlset>", line + "\n</urlset>")
    p.write_text(s)


def update_llms(section, title, url, cat):
    p = ROOT / "llms.txt"
    s = p.read_text()
    if url in s:
        return
    entry = f"- [{title}]({url}): {cat}"
    marker = f"## {section}\n"
    if marker in s:
        i = s.index(marker) + len(marker)
        j = s.find("\n## ", i)
        j = len(s) if j == -1 else j + 1
        block = s[i:j].rstrip("\n") + "\n" + entry + "\n"
        s = s[:i] + block + ("\n" if j < len(s) else "") + s[j:].lstrip("\n")
    else:
        s = s.rstrip("\n") + f"\n\n## {section}\n{entry}\n"
    p.write_text(s)


def make_cover(path, labels, accent):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    W, Hh = 1200, 630
    img = Image.new("RGB", (W, Hh), (13, 14, 34))
    glow = Image.new("RGB", (W, Hh), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    ac = tuple(int(accent[i:i + 2], 16) for i in (1, 3, 5))
    g.ellipse((700, -150, 1300, 450), fill=tuple(int(c * .55) for c in ac))
    g.ellipse((-200, 330, 420, 900), fill=(110, 40, 100))
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    img = Image.blend(img, glow, .85)
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, W, 200):
        d.line((x, 0, x, Hh), fill=(255, 255, 255, 14))
    for y in range(0, Hh, 105):
        d.line((0, y, W, y), fill=(255, 255, 255, 14))
    d.ellipse((790, 50, 1010, 270), fill=ac + (70,))
    d.ellipse((830, 90, 970, 230), fill=ac + (255,))
    # bar chart motif
    bars = [120, 170, 150, 230, 210, 290]
    for i, bh in enumerate(bars):
        x0 = 330 + i * 95
        d.rounded_rectangle((x0, 470 - bh, x0 + 62, 470), 12, fill=(43, 52, 140, 235), outline=(120, 130, 230, 160), width=2)
    try:
        font = ImageFont.truetype(str(ROOT / "tools/fonts/Inter-SemiBold.otf"), 30)
    except OSError:
        font = ImageFont.load_default()
    dots = [(232, 80, 170), (31, 160, 112)]
    for (lx, ly), lab, dot in zip([(110, 100), (110, 430)], labels[:2], dots):
        tw = d.textlength(lab, font=font)
        d.rounded_rectangle((lx, ly, lx + tw + 90, ly + 52), 14, fill=(255, 255, 255, 22), outline=(255, 255, 255, 40))
        d.ellipse((lx + 18, ly + 17, lx + 36, ly + 35), fill=dot)
        d.text((lx + 48, ly + 9), lab, font=font, fill=(245, 245, 250))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG", quality=82, optimize=True)


def check():
    """Validate all pages: one h1, title length, meta description, canonical, valid JSON-LD, local links."""
    problems = 0
    files = sorted(ROOT.glob("*.html")) + sorted((ROOT / "blog").glob("*.html"))
    for f in files:
        h = f.read_text()
        rel = f.relative_to(ROOT)
        issues = []
        if f.name != "404.html":
            if len(re.findall(r"<h1[\s>]", h)) != 1:
                issues.append("h1 count != 1")
            t = re.search(r"<title>(.*?)</title>", h)
            if not t or len(H.unescape(t.group(1))) > 70:
                issues.append(f"title length {len(t.group(1)) if t else 0}")
            md = re.search(r'<meta name="description" content="([^"]*)"', h)
            if not md or not (70 <= len(H.unescape(md.group(1))) <= 165):
                issues.append(f"meta description length {len(md.group(1)) if md else 0}")
            if not re.search(r'<link rel="canonical" href="https://performanceandpixel.com/', h):
                issues.append("no canonical")
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try:
                json.loads(m.group(1))
            except Exception as e:
                issues.append(f"bad JSON-LD: {e}")
        for href in re.findall(r'href="([^"#?]+\.html)', h):
            if href.startswith("http"):
                continue
            target = (ROOT / href.lstrip("/")) if href.startswith("/") else (f.parent / href).resolve()
            if not target.exists():
                issues.append(f"broken link {href}")
        if issues:
            problems += 1
            print(rel, "->", "; ".join(sorted(set(issues))))
    print(f"checked {len(files)} pages, {problems} with issues")
    return problems


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "check":
        sys.exit(1 if check() else 0)
    spec = json.loads(Path(sys.argv[2]).read_text())
    if cmd == "page":
        print("wrote", build_page(spec))
    elif cmd == "post":
        p, w = build_post(spec)
        print("wrote", p, f"({w} words)")
    else:
        print(__doc__)
        sys.exit(1)
