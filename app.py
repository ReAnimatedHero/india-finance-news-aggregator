from datetime import datetime, timedelta, timezone
import feedparser
import requests
from dateutil import tz
from flask import Flask, render_template_string

app = Flask(__name__)

INDIA_TZ = tz.gettz("Asia/Kolkata")

# ------------------ 1) RSS FEEDS ------------------
# These are the feeds we use. Any feed that returns entries
# will get AT LEAST one story shown on the page.
FEEDS = {
    # Moneycontrol – latest news
    "Moneycontrol": "http://www.moneycontrol.com/rss/latestnews.xml",

    # Business Standard Hindi – markets
    "BS Hindi - Markets News": "https://hindi.business-standard.com/rss/markets/news.xml",
    "BS Hindi - Share Market": "https://hindi.business-standard.com/rss/markets/share-market.xml",

    # The Hindu – markets
    "The Hindu - Markets": "https://www.thehindu.com/business/markets/feeder/default.rss",

    # Google News – India stock market (aggregates many publishers)
    "Google News - India Markets": (
        "https://news.google.com/rss/search"
        "?q=india+stock+market+OR+nifty+OR+sensex"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),
}

# How far back to prefer (in hours)
HOURS_WINDOW = 24

# HTTP session with a browser-like User-Agent
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
})


# ------------------ 2) FETCHING + NORMALISATION ------------------
def extract_image(entry):
    """Try to find an image URL in common media fields."""
    media_content = getattr(entry, "media_content", None)
    if media_content:
        if isinstance(media_content, list) and media_content:
            url = media_content[0].get("url")
            if url:
                return url
        elif isinstance(media_content, dict):
            url = media_content.get("url")
            if url:
                return url

    media_thumb = getattr(entry, "media_thumbnail", None)
    if media_thumb:
        if isinstance(media_thumb, list) and media_thumb:
            url = media_thumb[0].get("url")
            if url:
                return url
        elif isinstance(media_thumb, dict):
            url = media_thumb.get("url")
            if url:
                return url

    for link in getattr(entry, "links", []):
        link_type = getattr(link, "type", "") or link.get("type", "")
        href = getattr(link, "href", "") or link.get("href", "")
        if link_type and link_type.startswith("image/") and href:
            return href

    return None


def get_publisher_name(default_source_name, entry):
    """
    Try to show the *actual news publisher*:
    - For Google News, entry.source.title is usually like 'The Hindu', 'Economic Times', etc.
    - For direct feeds (Moneycontrol, BS, The Hindu) it may also be present.
    If not found, fall back to the feed name (default_source_name).
    """
    publisher = default_source_name

    src = getattr(entry, "source", None)
    if src:
        # attribute form
        title_attr = getattr(src, "title", None) or getattr(src, "name", None)
        if title_attr:
            publisher = title_attr
        else:
            # dict-like form
            try:
                title_dict = src.get("title") or src.get("name")
                if title_dict:
                    publisher = title_dict
            except Exception:
                pass

    return publisher


def fetch_feed(source_name, url):
    """Fetch one RSS feed using requests + feedparser."""
    print(f"[INFO] Fetching: {source_name} -> {url}")
    try:
        resp = SESSION.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] HTTP error for {source_name}: {e}")
        return []

    parsed = feedparser.parse(resp.content)
    print(f"[INFO]  {source_name}: HTTP {resp.status_code}, entries={len(parsed.entries)}")

    items = []
    for entry in parsed.entries:
        dt_struct = getattr(entry, "published_parsed", None) or getattr(
            entry, "updated_parsed", None
        )

        if dt_struct:
            dt_utc = datetime(*dt_struct[:6], tzinfo=timezone.utc)
        else:
            dt_utc = None  # handle later

        image_url = extract_image(entry)
        publisher = get_publisher_name(source_name, entry)

        items.append(
            {
                "source": publisher,        # visible publisher name
                "feed": source_name,        # which FEED this came from
                "title": getattr(entry, "title", "No title"),
                "link": getattr(entry, "link", ""),
                "summary": getattr(entry, "summary", ""),
                "dt_utc": dt_utc,
                "image": image_url,
            }
        )

    return items


def fetch_all():
    """Fetch all feeds without killing the app if one fails."""
    all_items = []
    for name, url in FEEDS.items():
        try:
            feed_items = fetch_feed(name, url)
            all_items.extend(feed_items)
        except Exception as e:
            print(f"[WARN] Failed parsing for {name}: {e}")
    print(f"[INFO] Total items fetched from all feeds: {len(all_items)}")
    return all_items


# ------------------ 3) FILTERING ------------------
def filter_last_window(items, fallback_limit_per_feed=1, global_limit=120):
    """
    1) Prefer items from the last HOURS_WINDOW hours (IST).
    2) Ensure at least `fallback_limit_per_feed` items from EACH FEED in FEEDS
       (if that feed has any data at all), even if older than the time window.
    3) Sort newest -> oldest and optionally trim to `global_limit`.
    """
    now_ist = datetime.now(INDIA_TZ)
    cutoff = now_ist - timedelta(hours=HOURS_WINDOW)

    # Ensure every item has a dt_ist we can sort on
    for item in items:
        if item.get("dt_utc") is not None:
            item["dt_ist"] = item["dt_utc"].astimezone(INDIA_TZ)
        else:
            # No timestamp in feed → treat as "now" for ordering
            item["dt_ist"] = now_ist

    # 1) Primary list: items within time window
    within_window = [it for it in items if it["dt_ist"] >= cutoff]
    within_window.sort(key=lambda x: x["dt_ist"], reverse=True)

    print(f"[INFO] Items after {HOURS_WINDOW}h filter: {len(within_window)}")

    # Start building the final list from within-window items
    final_items = list(within_window)
    seen_keys = {(it["feed"], it["link"]) for it in final_items}

    # 2) Guarantee at least fallback_limit_per_feed items per FEED
    for feed_name in FEEDS.keys():
        # all items from this feed (regardless of time window)
        feed_items = [it for it in items if it.get("feed") == feed_name]
        if not feed_items:
            # This feed either 404'd or returned zero entries
            continue

        # Count how many from this FEED are already in the filtered list
        already_in = [it for it in final_items if it.get("feed") == feed_name]
        if len(already_in) >= fallback_limit_per_feed:
            # Already satisfied the minimum
            continue

        # Need to add some from this feed (even if older than window)
        feed_items_sorted = sorted(feed_items, key=lambda x: x["dt_ist"], reverse=True)

        for cand in feed_items_sorted:
            key = (cand["feed"], cand["link"])
            if key in seen_keys:
                continue
            final_items.append(cand)
            seen_keys.add(key)
            already_in.append(cand)
            if len(already_in) >= fallback_limit_per_feed:
                break

    # 3) Global sort (newest first) and optional overall trim
    final_items.sort(key=lambda x: x["dt_ist"], reverse=True)

    if global_limit is not None and len(final_items) > global_limit:
        final_items = final_items[:global_limit]

    # Debug: how many per FEED + per displayed source
    counts_by_feed = {}
    counts_by_source = {}
    for it in final_items:
        counts_by_feed[it["feed"]] = counts_by_feed.get(it["feed"], 0) + 1
        counts_by_source[it["source"]] = counts_by_source.get(it["source"], 0) + 1

    print("[INFO] Items per FEED (final):", counts_by_feed)
    print("[INFO] Items per SOURCE (final):", counts_by_source)

    return final_items


# ------------------ 4) HTML TEMPLATE ------------------
TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>India Finance Pulse</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      color-scheme: dark;
      --bg: #020617;
      --card-border: #1e293b;
      --accent: #22d3ee;
      --accent-soft: rgba(34, 211, 238, 0.15);
      --text-main: #e5e7eb;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 0;
      background: radial-gradient(circle at top, #0f172a 0, #020617 46%, #000 100%);
      color: var(--text-main);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .page {
      max-width: 1100px;
      margin: 0 auto;
      padding: 20px 16px 32px;
    }
    header {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 18px;
    }
    .title-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }
    h1 {
      font-size: 1.85rem;
      margin: 0;
      letter-spacing: 0.02em;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pill {
      font-size: 0.75rem;
      padding: 3px 9px;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.5);
      color: var(--text-muted);
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .pill-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #22c55e;
      box-shadow: 0 0 0 4px rgba(34,197,94,0.25);
    }
    .subtitle {
      font-size: 0.9rem;
      color: var(--text-muted);
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .chip {
      background: rgba(15, 23, 42, 0.75);
      border-radius: 999px;
      padding: 3px 10px;
      border: 1px solid rgba(148, 163, 184, 0.35);
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .grid {
      margin-top: 16px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 16px;
    }
    .card {
      background: linear-gradient(145deg, rgba(15,23,42,0.95), rgba(15,23,42,0.98));
      border-radius: 14px;
      border: 1px solid var(--card-border);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      min-height: 220px;
      box-shadow:
        0 18px 35px rgba(15, 23, 42, 0.75),
        0 0 0 1px rgba(148, 163, 184, 0.15);
      position: relative;
      transition: transform 0.16s ease-out, box-shadow 0.16s ease-out,
                  border-color 0.16s ease-out, background 0.16s ease-out;
    }
    .card::before {
      content: "";
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at top left, rgba(34,211,238,0.14), transparent 60%);
      opacity: 0;
      transition: opacity 0.2s ease-out;
      pointer-events: none;
    }
    .card:hover {
      transform: translateY(-3px) translateZ(0);
      border-color: rgba(56, 189, 248, 0.75);
      box-shadow:
        0 22px 45px rgba(15, 23, 42, 0.95),
        0 0 0 1px rgba(56, 189, 248, 0.65);
      background: radial-gradient(circle at top, rgba(15,23,42,0.95), rgba(15,23,42,0.98));
    }
    .card:hover::before { opacity: 1; }
    .card-image-wrapper {
      position: relative;
      padding-top: 55%;
      overflow: hidden;
      background: radial-gradient(circle at center, #1e293b, #020617);
    }
    .card-image {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      filter: saturate(1.15) contrast(1.02);
      transition: transform 0.4s ease-out, filter 0.3s ease-out, opacity 0.25s ease-out;
    }
    .card:hover .card-image {
      transform: scale(1.04);
      filter: saturate(1.3) contrast(1.04);
    }
    .card-body {
      padding: 10px 12px 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
    }
    .source-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-bottom: 1px;
    }
    .source-name { font-weight: 500; letter-spacing: 0.02em; }
    .time-pill {
      padding: 2px 8px;
      border-radius: 999px;
      background: rgba(15,23,42,0.9);
      border: 1px solid rgba(148, 163, 184, 0.45);
      font-size: 0.72rem;
      white-space: nowrap;
    }
    .card-title {
      font-size: 0.95rem;
      line-height: 1.35;
      font-weight: 500;
    }
    .card-title a {
      text-decoration: none;
      color: var(--text-main);
    }
    .card-title a:hover {
      text-decoration: underline;
      text-decoration-thickness: 1px;
      text-decoration-color: var(--accent);
    }
    .card-footer {
      margin-top: auto;
      display: flex;
      justify-content: flex-end;
      font-size: 0.75rem;
    }
    .read-link {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      text-decoration: none;
      border: 1px solid rgba(34,211,238,0.35);
    }
    .read-link span { font-size: 0.78rem; }
    .read-link:hover {
      background: rgba(34,211,238,0.22);
      border-color: rgba(34,211,238,0.6);
    }
    .empty-state {
      margin-top: 40px;
      text-align: center;
      color: var(--text-muted);
      font-size: 0.92rem;
    }
    .empty-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px dashed rgba(148,163,184,0.6);
      margin-bottom: 10px;
      font-size: 0.78rem;
      background: rgba(15,23,42,0.8);
    }
    @media (max-width: 640px) {
      .page { padding-inline: 12px; }
      h1 { font-size: 1.5rem; }
    }
  </style>
</head>
<body>
  <div class="page">
    <header>
      <div class="title-row">
        <h1>
          India Finance Pulse
          <span class="pill">
            <span class="pill-dot"></span>
            live · last {{ hours_window }}h*
          </span>
        </h1>
        <div class="chip">
          {{ items|length }} stories · {{ unique_sources|length }} sources
        </div>
      </div>

      <div class="subtitle">
        <span>Curated headlines from major Indian finance, business and markets portals.</span>
        <span>*If some feeds don’t send timestamps, you may see their latest stories instead.</span>
      </div>
    </header>

    {% if not items %}
      <div class="empty-state">
        <div class="empty-badge">
          No stories available
        </div>
        <div>
          No finance headlines could be loaded.  
          Check your internet connection and try refreshing.
        </div>
      </div>
    {% else %}
      <main class="grid">
        {% for item in items %}
          <article class="card">
            {% if item.image %}
              <div class="card-image-wrapper">
                <img src="{{ item.image }}" alt="" class="card-image" loading="lazy">
              </div>
            {% endif %}

            <div class="card-body">
              <div class="source-row">
                <div class="source-name">{{ item.source }}</div>
                <div class="time-pill">
                  {{ item.dt_ist.strftime('%d %b, %H:%M') }} IST
                </div>
              </div>

              <div class="card-title">
                <a href="{{ item.link }}" target="_blank" rel="noopener noreferrer">
                  {{ item.title }}
                </a>
              </div>

              <div class="card-footer">
                <a href="{{ item.link }}" target="_blank"
                   rel="noopener noreferrer" class="read-link">
                  <span>Open story</span>
                  <span>↗</span>
                </a>
              </div>
            </div>
          </article>
        {% endfor %}
      </main>
    {% endif %}
  </div>
</body>
</html>
"""


# ------------------ 5) ROUTE ------------------
@app.route("/")
def index():
    all_items = fetch_all()
    recent = filter_last_window(all_items)
    unique_sources = sorted({item["source"] for item in recent})
    return render_template_string(
        TEMPLATE,
        items=recent,
        unique_sources=unique_sources,
        hours_window=HOURS_WINDOW,
    )


# ------------------ 6) LOCAL RUN ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
