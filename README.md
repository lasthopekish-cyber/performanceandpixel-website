# Performance and Pixel website

The live site for performanceandpixel.com.

## How it works
- `index.html` is the whole website (styles, scripts and logo are built in).
- Hostinger watches the `main` branch. Any change saved to `main` is deployed automatically.

## Making a change
1. Open `index.html` on GitHub and click the pencil icon, or upload a new `index.html` over the old one.
2. Click **Commit changes** on `main`.
3. The site updates within a minute or two. Hard refresh (Ctrl+Shift+R) if you don't see it.

## Things to edit at the top of the script in index.html
- `WHATSAPP` — the number the booking form and buttons send to.
- `PLATFORM_LOGOS` — optional official platform logo image links.
- `CLIENT_LOGOS` — the client logo images shown in the logo strip.

## SEO and blog automation
- `content/SEO-PLAYBOOK.md` — target keywords, writing rules and the publish steps.
- `content/blog-queue.md` — keyword queue. A scheduled task publishes the next post four times a week (Mon, Wed, Fri, Sat).
- `tools/sitegen.py` — builds a page or post from a JSON spec in `content/` using the site's own template, and updates `blog/index.html`, `sitemap.xml` and `llms.txt`. Run `python3 tools/sitegen.py check` before every push.
- `seo/backlinks.csv` — backlink and listing tracker.
- `content/`, `seo/` and `tools/` are blocked from the web (`.htaccess`) and from crawlers (`robots.txt`).
