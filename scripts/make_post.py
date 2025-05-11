#!/usr/bin/env python3
import os, json, hashlib, datetime, re, pathlib, subprocess
import feedparser, frontmatter
from slugify import slugify
from huggingface_hub import InferenceClient
import tweepy

FEEDS = [
    "https://variety.com/v/film/news/feed/",
    "https://feeds.feedburner.com/DeadlineHollywood"
]
OUT_DIR   = pathlib.Path("content/posts")
STATE_FILE = ".seen.json"
HF_MODEL  = "mistralai/Mistral-7B-Instruct"
TWEET_FMT = "🎬 {title}\n\nRead more: {url}\n#Movies #TVNews #Hollywood"

def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def load_state():
    try: return json.load(open(STATE_FILE))
    except FileNotFoundError: return {}
def save_state(d):
    json.dump(d, open(STATE_FILE,"w"), indent=2)

def ask_llm(title, summary):
    client = InferenceClient(os.environ["HF_TOKEN"])
    prompt = f"""Write a neutral-tone entertainment news update (4 short paragraphs, ≤150 words)
about “{title}”. Base it on: “{summary}”."""
    resp = client.chat.completions.create(
        model=HF_MODEL,
        messages=[{"role":"user","content":prompt}],
        temperature=0.7, max_tokens=280)
    return resp.choices[0].message.content.strip()

def write_post(entry, body):
    slug = slugify(re.sub(r"[:?!]","", entry.title))[:60]
    fm = frontmatter.Post(body,
        title = entry.title,
        date  = datetime.datetime.utcnow().isoformat()+"Z",
        tags  = ["movies","tv","hollywood"]
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{slug}.md"
    path.write_text(frontmatter.dumps(fm), encoding="utf-8")
    return path, f"/posts/{slug}.html"

def tweet(title, url):
    auth = tweepy.OAuth1UserHandler(
        os.environ["X_CONSUMER_KEY"], os.environ["X_CONSUMER_SECRET"],
        os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    tweepy.API(auth).update_status(TWEET_FMT.format(title=title, url=url))

def main():
    seen = load_state()
    new_items = []
    for feed in FEEDS:
        for e in feedparser.parse(feed).entries:
            gid = sha(e.link)
            if gid not in seen:
                new_items.append(e);  seen[gid]=True
    if not new_items:
        return
    for e in new_items:
        body = ask_llm(e.title, getattr(e,"summary",""))
        md, url = write_post(e, body)
        subprocess.run(["git","add",str(md)], check=True)
        subprocess.run(["git","commit","-m",f"Add {md.name}"], check=True)
        if all(k in os.environ for k in ["X_CONSUMER_KEY","X_CONSUMER_SECRET","X_ACCESS_TOKEN","X_ACCESS_SECRET"]):
            tweet(e.title, f"https://{os.environ['SITE_DOMAIN']}{url}")
    save_state(seen)

if __name__=="__main__":
    main()
