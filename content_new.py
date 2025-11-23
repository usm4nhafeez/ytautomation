#!/usr/bin/env python3
"""
content_new.py

Search YouTube (no API key) using yt-dlp,
then build and save content_plan_new.json from the top results.

Usage:
  pip install yt-dlp
  python content_new.py
"""

import json
import sys
from typing import List, Dict, Optional, Any

# --- require yt-dlp ---
try:
    import yt_dlp
except ImportError as exc:
    print("Missing required package 'yt-dlp'. Install with:\n\n    pip install yt-dlp\n")
    raise SystemExit(1) from exc


def search_youtube(topic: str, limit: int = 10) -> List[Dict[str, Optional[str]]]:
    """
    Use yt-dlp to search YouTube and get video results.
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
        
        search_query = f"ytsearch{limit}:{topic}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_query, download=False)
            
            if not result or 'entries' not in result:
                return []
            
            normalized = []
            for video in result['entries']:
                if not video:
                    continue
                
                # Extract video information
                video_id = video.get('id')
                title = video.get('title')
                
                # Build YouTube link
                link = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
                
                # Extract channel information
                channel = video.get('channel') or video.get('uploader')
                
                # Extract view count
                view_count = video.get('view_count')
                if view_count is not None:
                    view_count = f"{view_count:,} views"
                
                # Extract duration
                duration = video.get('duration')
                if duration:
                    mins, secs = divmod(int(duration), 60)
                    duration_str = f"{int(mins)}:{int(secs):02d}"
                else:
                    duration_str = None
                
                normalized.append({
                    "id": video_id,
                    "title": title,
                    "link": link,
                    "channel": channel,
                    "viewCount": view_count,
                    "duration": duration_str,
                    "publishedTime": None  # yt-dlp doesn't always provide this in search
                })
            
            # Keep only items with an id
            normalized = [n for n in normalized if n.get("id")]
            return normalized
            
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        import traceback
        traceback.print_exc()
        return []


def build_plan_from_videos(videos: List[Dict[str, Optional[str]]], target_count: int = None) -> Dict:
    """
    Build a content plan structure from the video list.
    Matches the format of the existing content_plan.json.
    Creates lessons with titles from search results but sets status as 'pending'
    and youtube_id as null by default, so you can update them later when you upload your videos.
    If target_count exceeds the number of videos found, creates generic pending lessons.
    """
    lessons = []
    actual_count = target_count if target_count else len(videos)
    
    for idx in range(actual_count):
        chapter = (idx // 2) + 1
        part = (idx % 2) + 1
        
        # Use video title if available, otherwise create generic title
        if idx < len(videos):
            v = videos[idx]
            title = v.get("title") or f"Lesson {idx+1}"
        else:
            title = f"Lesson {idx+1}"
        
        lesson = {
            "chapter": chapter,
            "part": part,
            "title": title,
            "status": "pending",
            "youtube_id": None
        }
        lessons.append(lesson)
    return {"lessons": lessons}


def save_plan(plan: Dict, filename: str = "content_plan_new.json"):
    """
    Save the content plan to a JSON file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"\nSaved new content plan to '{filename}' ({len(plan.get('lessons', []))} lessons).")


def prompt_int(prompt_msg: str, default: int) -> int:
    """
    Prompt user for an integer input with a default value.
    """
    try:
        raw = input(prompt_msg).strip()
        if raw == "":
            return default
        val = int(raw)
        return val if val > 0 else default
    except Exception:
        return default


def main():
    """
    Main function to create a new content plan from YouTube search.
    """
    print("Create a new content_plan_new.json from a YouTube search (no API key).")
    topic = input("Enter topic to search for: ").strip()
    if not topic:
        print("No topic provided — exiting.")
        return
    
    default_n = 10
    n = prompt_int(f"How many lessons to create? (default {default_n}): ", default_n)

    print(f"\nSearching YouTube for '{topic}' (attempting top {n} results)...")
    videos = search_youtube(topic, limit=n)
    
    if not videos:
        print("No videos found or unable to parse search results.")
        return

    plan = build_plan_from_videos(videos, target_count=n)
    save_plan(plan, "content_plan_new.json")

    print("\nSummary:")
    for i, lesson in enumerate(plan["lessons"], start=1):
        print(f" {i:2d}. Chapter {lesson['chapter']} Part {lesson['part']} | {lesson['title'][:80]}")
        print(f"     id: {lesson['youtube_id']}  | channel: {lesson.get('channel')}  | duration: {lesson.get('duration')}")
        print(f"     views: {lesson.get('viewCount')}  | link: {lesson.get('link')}\n")


if __name__ == "__main__":
    main()
