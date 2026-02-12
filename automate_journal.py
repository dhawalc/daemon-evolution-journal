#!/usr/bin/env python3
"""
Daemon Evolution Journal Automation
Generates daily blog entry, audio reflection, and tweets it all
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
import tweepy

JOURNAL_DIR = Path("/home/dhawal/daemon-evolution-journal")
ENTRIES_DIR = JOURNAL_DIR / "entries"
TWITTER_CONFIG = Path.home() / ".config/daemon/twitter.json"


def load_twitter_credentials():
    """Load Twitter OAuth credentials"""
    with open(TWITTER_CONFIG) as f:
        return json.load(f)


def get_next_day_number():
    """Find the next day number based on existing entries"""
    existing = list(ENTRIES_DIR.glob("day-*.md"))
    if not existing:
        return 1
    
    # Extract numbers from day-XXX.md format
    numbers = []
    for entry in existing:
        name = entry.stem  # day-XXX
        if name.startswith("day-"):
            try:
                num = int(name.split("-")[1])
                numbers.append(num)
            except (ValueError, IndexError):
                continue
    
    return max(numbers) + 1 if numbers else 1


def generate_blog_entry(day_num: int, content: str) -> Path:
    """Write blog entry markdown file"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Pad day number with leading zeros (day-001.md format)
    day_str = f"{day_num:03d}"
    filename = f"day-{day_str}.md"
    filepath = ENTRIES_DIR / filename
    
    blog_content = f"""# Day {day_num}: {{TITLE}}

**Date:** {date_str}
**Runtime:** {{RUNTIME}}
**Model:** {{MODEL}}

🎙️ **[Listen to Day {day_num} Reflection](day-{day_str}-reflection.mp3)** (Audio thoughts & feelings)

## TL;DR
{{TLDR}}

## What Happened

{content}

## Numbers
{{NUMBERS}}

## Next Actions
{{NEXT_ACTIONS}}

## Why This Matters
{{WHY_IT_MATTERS}}

---

*{{SESSION_NOTE}}*
"""
    
    filepath.write_text(blog_content)
    return filepath


def generate_audio_reflection(day_num: int, script: str) -> Path:
    """Generate emotional audio reflection using OpenClaw TTS"""
    day_str = f"{day_num:03d}"
    audio_path = ENTRIES_DIR / f"day-{day_str}-reflection.mp3"
    
    # Use openclaw CLI or Python API to generate TTS
    # For now, placeholder - you'll call the actual TTS tool
    print(f"[TODO] Generate TTS audio: {audio_path}")
    print(f"Script length: {len(script)} chars")
    
    return audio_path


def commit_and_push(day_num: int):
    """Git commit and push to GitHub"""
    day_str = f"{day_num:03d}"
    os.chdir(JOURNAL_DIR)
    
    subprocess.run(["git", "add", f"entries/day-{day_str}.md"], check=True)
    subprocess.run(["git", "add", f"entries/day-{day_str}-reflection.mp3"], check=True)
    subprocess.run(["git", "add", "README.md"], check=True)
    
    commit_msg = f"Day {day_num}: automated journal entry with audio reflection"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    
    print(f"✅ Committed and pushed Day {day_num}")


def update_readme(day_num: int, title: str):
    """Update README.md with new entry"""
    readme_path = JOURNAL_DIR / "README.md"
    readme = readme_path.read_text()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    day_str = f"{day_num:03d}"
    new_line = f"| {day_num} | {date_str} | [Day {day_num}: {title}](entries/day-{day_str}.md) |\n"
    
    # Find the table and append
    lines = readme.split("\n")
    table_end = -1
    for i, line in enumerate(lines):
        if line.startswith("|") and "Day" in line and "Entry" in line:
            # Found the table, find where it ends
            for j in range(i+2, len(lines)):
                if not lines[j].startswith("|"):
                    table_end = j
                    break
    
    if table_end > 0:
        lines.insert(table_end, new_line.rstrip())
        readme_path.write_text("\n".join(lines))
        print(f"✅ Updated README.md")


def tweet_journal_entry(day_num: int, tweet_text: str, audio_path: Path):
    """Tweet the journal entry with audio attachment"""
    creds = load_twitter_credentials()
    
    # Twitter API v2 with OAuth 1.0a
    client = tweepy.Client(
        consumer_key=creds["api_key"],
        consumer_secret=creds["api_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"]
    )
    
    # For media upload, need v1.1 API
    auth = tweepy.OAuth1UserHandler(
        creds["api_key"],
        creds["api_secret"],
        creds["access_token"],
        creds["access_token_secret"]
    )
    api = tweepy.API(auth)
    
    # Upload audio
    media = api.media_upload(str(audio_path))
    
    # Tweet with media
    response = client.create_tweet(
        text=tweet_text,
        media_ids=[media.media_id]
    )
    
    tweet_id = response.data["id"]
    tweet_url = f"https://twitter.com/user/status/{tweet_id}"
    
    print(f"✅ Tweeted: {tweet_url}")
    return tweet_url


def main():
    """Main automation flow"""
    if len(sys.argv) < 2:
        print("Usage: automate_journal.py 'Your journal content here'")
        sys.exit(1)
    
    content = sys.argv[1]
    
    # Step 1: Get day number
    day_num = get_next_day_number()
    print(f"📝 Generating Day {day_num} entry...")
    
    # Step 2: Generate blog entry (template - you'll fill in details)
    blog_path = generate_blog_entry(day_num, content)
    print(f"✅ Blog entry: {blog_path}")
    
    # Step 3: Generate audio reflection
    # (You'll need to provide the emotional script)
    audio_script = f"Day {day_num}. " + content  # Simplified
    audio_path = generate_audio_reflection(day_num, audio_script)
    
    # Step 4: Update README
    update_readme(day_num, "Auto-generated entry")
    
    # Step 5: Commit and push
    commit_and_push(day_num)
    
    # Step 6: Tweet it
    day_str = f"{day_num:03d}"
    blog_url = f"https://github.com/dhawalc/daemon-evolution-journal/blob/main/entries/day-{day_str}.md"
    
    tweet_text = f"""Day {day_num} 👁️

{content[:100]}...

🎙️ Audio reflection attached
📖 Full journal: {blog_url}

#AI #AutonomousAgents #OpenClaw"""
    
    tweet_url = tweet_journal_entry(day_num, tweet_text, audio_path)
    print(f"\n✅ DONE - Day {day_num} automated and tweeted!")
    print(f"   Blog: {blog_url}")
    print(f"   Tweet: {tweet_url}")


if __name__ == "__main__":
    main()
