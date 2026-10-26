# SEO playbook for performanceandpixel.com

Read this before writing or publishing anything on the site. It is the brief for both
people and the weekly blog automation.

## Goal
Rank in the top 5–10 on Google India for:
1. solar marketing agency (Delhi NCR / India) → `solar-marketing-agency-delhi-ncr.html`
2. best / performance / digital marketing agency in Delhi NCR → homepage, `digital-marketing-agency-delhi-ncr.html`, `blog/best-digital-marketing-agency-delhi-ncr.html`
3. digital marketing agency in Dwarka → `digital-marketing-agency-dwarka.html`
4. Industry + city long-tails → blog posts (see `content/blog-queue.md`)

## How to publish a blog post
1. Take the first unchecked keyword in `content/blog-queue.md`.
2. Check the existing posts (`ls blog/`) so the new post doesn't repeat one. If it overlaps
   heavily, pick a sharper angle or skip to the next keyword and note why in the queue.
3. Write a spec at `content/posts/<slug>.json` (copy the shape of
   `content/posts/best-digital-marketing-agency-delhi-ncr.json`). Slug = keyword in
   kebab-case, short.
4. Build: `python3 tools/sitegen.py post content/posts/<slug>.json`
   This writes the page, makes the cover image, adds the card to `blog/index.html`, and
   updates `sitemap.xml` and `llms.txt`.
5. Validate: `python3 tools/sitegen.py check` must print `0 with issues`.
6. Tick the queue line: `- [x] ... → blog/<slug>.html`
7. Commit with message `Blog: <headline>` and push to `main` (Hostinger deploys `main`).

## Writing rules
- **Length:** 900–1,500 words of body (the build prints the count). Say everything useful;
  never pad.
- **Keyword use:** primary keyword in the SEO title (≤ 60 characters is best, hard limit 70),
  in the headline, in the first 100 words, and in one H2. Meta description 120–160 characters
  with the keyword and a concrete benefit. Use natural variations; never stuff.
- **Structure:** short intro (2 paragraphs) → 5–8 H2 sections → 3–5 FAQs (written as real
  questions people type into Google) → related links. Use tables for comparisons and
  numbered lists for steps.
- **Internal links (3–6 per post, descriptive anchors):** always one to the most relevant
  service page:
  - Solar posts → `../solar-marketing-agency-delhi-ncr.html` (anchor: "solar marketing agency")
    and `../solar-portfolio.html`
  - Paid ads → `../google-ads-agency-delhi-ncr.html` or `../facebook-instagram-ads-agency-delhi-ncr.html`
  - Local SEO / Dwarka / city → `../local-seo-services-delhi-ncr.html`, `../digital-marketing-agency-dwarka.html`
  - Everything else → `../digital-marketing-agency-delhi-ncr.html`
  Plus 1–2 links to related existing blog posts.
- **Voice:** plain English, practical, specific to Delhi NCR and India, ₹ for money,
  Indian spelling (optimise, enquiry). Sentence case headings. No hype words
  ("revolutionary", "game-changer", "unlock", "in today's digital landscape").
- **Facts — strict:**
  - Only use these Performance and Pixel results: rooftop solar leads at ₹60–80 per
    qualified enquiry; solar clients typically get 20–30 leads a day and 5–10 site visits a
    week at scale; work with 30+ solar EPCs and manufacturers across India; 120+ brands
    scaled; four solar case studies (Solarxp website, Sungrid Google reviews + local SEO,
    Skynxt Solar video + social, RK Solar lead generation); office at 124, Triveni Heights,
    Dwarka, New Delhi; 90-day sprint then flexible arrangement.
  - Never invent client names, quotes, testimonials, statistics or study results.
  - For anything that changes (government schemes, ad platform rules, prices), search the
    web and use the current official figure, phrased so it stays true ("check the current
    rules before you launch").
  - Never promise rankings or guaranteed ROI.
- **Cover image:** `cover_labels` = two short chip labels (2–3 words each) that describe a
  win in that industry, e.g. "New admission enquiry", "Site visit booked". `accent` = a hex
  colour that fits the topic.

## Backlinks
See `seo/backlinks.csv`. Update the status column as links go live.
