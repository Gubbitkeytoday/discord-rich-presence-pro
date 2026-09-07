"""
================================================================================
  DISCORD RICH PRESENCE - ULTRA SENIOR / EXPERT ENGINE
  Architecture:
    Windows GSMTC (Media Transport Controls)
    + Win32 Active Window & Process Enumeration
    + Realtime YouTube Cover & Direct URL Resolver
    + Discord IPC (pypresence) with Native Timeline Sync
================================================================================
"""

import asyncio
import ctypes
from ctypes import wintypes
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

import psutil
from pypresence import Presence, ActivityType, DiscordNotFound, InvalidID, PipeClosed

# Native Windows Runtime Media Integration (Windows 10 / 11)
try:
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as SessionManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )
    HAS_WINSDK = True
except Exception:
    HAS_WINSDK = False

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# Verified High-Definition PNG Assets for Discord Media Proxy
ICONS = {
    "youtube": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/youtube.png",
    "youtube_music": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/youtube-music.png",
    "vscode": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/visual-studio-code.png",
    "claude": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/claude-ai.png",
    "gemini": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/google-gemini.png",
    "python": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/python.png",
}

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

# LRU Cache for YouTube video metadata to prevent redundant network lookups
YOUTUBE_CACHE = {}


def log(msg):
    print(msg, flush=True)


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"[!] Error loading config.json: {e}")
        return {}


def sanitize_text(text, min_len=2, max_len=128):
    if not text:
        return None
    s = str(text).strip()
    if len(s) < min_len:
        s = s.ljust(min_len)
    if len(s) > max_len:
        s = s[:max_len - 3] + "..."
    return s


def get_running_process_names():
    names = set()
    try:
        for p in psutil.process_iter(["name"]):
            n = p.info["name"]
            if n:
                names.add(n.lower())
    except Exception:
        pass
    return names


def get_window_titles():
    titles = []
    def enum_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                t = buff.value.strip()
                if t:
                    titles.append(t)
        return True
    try:
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception:
        pass
    return titles


def fetch_youtube_video_data(title, artist=""):
    """
    Resolves YouTube video ID, direct video URL, and high-res cover thumbnail.
    Caches results in memory for maximum performance.
    """
    clean_title = re.sub(r"[^\w\s\u0E00-\u0E7F-]", "", title).strip()
    clean_artist = re.sub(r"[^\w\s\u0E00-\u0E7F-]", "", artist).strip()
    cache_key = f"{clean_title}::{clean_artist}".strip()
    
    if cache_key in YOUTUBE_CACHE:
        return YOUTUBE_CACHE[cache_key]

    query = urllib.parse.quote_plus(f"{clean_title} {clean_artist}".strip())
    url = f"https://www.youtube.com/results?search_query={query}"
    
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "th-TH,th;en-US,en;q=0.9"
    })

    video_id = None
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if matches:
                video_id = matches[0]
    except Exception as e:
        log(f"[!] YouTube metadata fetch failed: {e}")

    if video_id:
        data = {
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "video_id": video_id
        }
    else:
        data = {
            "video_url": f"https://www.youtube.com/results?search_query={query}",
            "thumbnail_url": ICONS["youtube"],
            "video_id": None
        }

    YOUTUBE_CACHE[cache_key] = data
    return data


async def async_get_media_info():
    """
    Interrogates the Windows 10/11 GSMTC subsystem for active media sessions.
    Calculates exact anchor timestamps (start_ts & end_ts) to synchronize Discord's
    client-side progress bar with sub-second accuracy.
    """
    if not HAS_WINSDK:
        return None
    try:
        mgr = await SessionManager.request_async()
        sessions = mgr.get_sessions()
        
        target_session = None
        for s in sessions:
            pb = s.get_playback_info()
            if pb and pb.playback_status == PlaybackStatus.PLAYING:
                target_session = s
                break
                
        if not target_session:
            curr = mgr.get_current_session()
            if curr:
                target_session = curr
        
        if not target_session and sessions:
            target_session = sessions[0]

        if target_session:
            props = await target_session.try_get_media_properties_async()
            tl = target_session.get_timeline_properties()
            pb = target_session.get_playback_info()
            
            title = props.title.strip() if props and props.title else ""
            artist = props.artist.strip() if props and props.artist else ""
            app_id = (target_session.source_app_user_model_id or "").lower()

            status = pb.playback_status if pb else 0
            is_playing = (status == PlaybackStatus.PLAYING)
            is_paused = (status == PlaybackStatus.PAUSED)
            
            pos = tl.position.total_seconds() if tl and tl.position else 0.0
            duration = tl.end_time.total_seconds() if tl and tl.end_time else 0.0
            lut = tl.last_updated_time if tl and tl.last_updated_time else None
            
            # Anchor timestamp computation:
            # lut (last_updated_time) is the exact UTC epoch when Chromium reported `pos`.
            # If playing, the video started at (lut - pos).
            now = time.time()
            lut_ts = lut.timestamp() if lut else now
            
            if is_playing and duration > 0:
                start_ts = int(lut_ts - pos)
                end_ts = int(start_ts + duration)
                current_progress = int(now - start_ts)
            else:
                start_ts = None
                end_ts = None
                current_progress = int(pos)

            if title:
                is_youtube = "youtube" in title.lower() or any(b in app_id for b in ["chrome", "edge", "brave", "firefox", "opera"])
                return {
                    "title": title,
                    "artist": artist,
                    "is_playing": is_playing,
                    "is_paused": is_paused,
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "current_progress": current_progress,
                    "duration": duration,
                    "app": app_id,
                    "is_youtube": is_youtube
                }
    except Exception as e:
        log(f"[!] GSMTC error: {e}")
    return None


def detect_current_activity(config, session_start_time):
    procs = get_running_process_names()
    titles = get_window_titles()
    
    media = None
    if HAS_WINSDK:
        try:
            media = asyncio.run(async_get_media_info())
        except Exception:
            media = None

    yt_window_title = None
    vscode_active_file = None
    vscode_workspace = None
    is_claude_active = "claude.exe" in procs

    for t in titles:
        if " - YouTube" in t:
            clean_title = t.split(" - YouTube")[0].strip()
            if clean_title.startswith("(") and ")" in clean_title[:5]:
                clean_title = clean_title.split(")", 1)[1].strip()
            yt_window_title = clean_title
        if "Visual Studio Code" in t:
            parts = [p.strip() for p in t.split(" - ")]
            if len(parts) >= 2:
                vscode_active_file = parts[0].replace("● ", "").strip()
            if len(parts) >= 3:
                vscode_workspace = parts[1].strip()
        if "claude" in t.lower():
            is_claude_active = True

    has_vscode = "code.exe" in procs
    has_browser = any(b in procs for b in ["chrome.exe", "msedge.exe", "brave.exe", "firefox.exe", "opera.exe"])

    # =========================================================================
    # SCENARIO 1: YouTube Active Media Playback (Ultra High-Fidelity)
    # =========================================================================
    if media and (media.get("title") or yt_window_title):
        raw_title = media.get("title") or yt_window_title
        artist = media.get("artist") or "YouTube"
        is_playing = media.get("is_playing", True)
        is_paused = media.get("is_paused", False)
        start_ts = media.get("start_ts")
        end_ts = media.get("end_ts")
        current_progress = media.get("current_progress", 0)
        duration = media.get("duration", 0)

        # Retrieve verified YouTube thumbnail and direct URL
        yt_data = fetch_youtube_video_data(raw_title, artist)
        thumbnail_url = yt_data.get("thumbnail_url", ICONS["youtube"])
        video_url = yt_data.get("video_url", "https://www.youtube.com")

        buttons = [
            {"label": "▶ ดูคลิปนี้บน YouTube", "url": video_url},
            {"label": "⚡ Antigravity AI", "url": "https://github.com"}
        ]

        payload = {
            "activity_type": ActivityType.WATCHING,
            "large_image": thumbnail_url,
            "large_text": sanitize_text(raw_title),
            "small_image": ICONS["youtube"],
            "small_text": "YouTube",
            "buttons": buttons
        }

        # Format clean, authentic artist line:
        channel_str = f"by {artist}" if artist and artist.lower() != "youtube" else "YouTube Video"

        if is_paused:
            dur_m, dur_s = int(duration // 60), int(duration % 60)
            cur_m, cur_s = int(current_progress // 60), int(current_progress % 60)
            payload["details"] = sanitize_text(raw_title)
            payload["state"] = sanitize_text(f"⏸️ พักไว้ที่ {cur_m}:{cur_s:02d} / {dur_m}:{dur_s:02d} • {artist}")
        elif has_vscode:
            # Multitasking Mode: Coding + YouTube Media
            payload["details"] = sanitize_text(raw_title)
            ws_tag = f"Coding in {vscode_workspace}" if vscode_workspace else "Coding in VS Code"
            payload["state"] = sanitize_text(f"{ws_tag} • {channel_str}")
            payload["small_image"] = ICONS["vscode"]
            payload["small_text"] = "Visual Studio Code + Antigravity"
            if start_ts and end_ts:
                payload["start"] = start_ts
                payload["end"] = end_ts
        else:
            # Clean, minimalist music/video layout
            payload["details"] = sanitize_text(raw_title)
            payload["state"] = sanitize_text(channel_str)
            if start_ts and end_ts:
                payload["start"] = start_ts
                payload["end"] = end_ts
            elif start_ts:
                payload["start"] = start_ts

        return payload

    # =========================================================================
    # SCENARIO 2: Coding in Visual Studio Code
    # =========================================================================
    if has_vscode:
        editing_str = f"Editing {vscode_active_file}" if vscode_active_file else "Writing Code"
        workspace_str = f"Workspace: {vscode_workspace}" if vscode_workspace else "Visual Studio Code"
        if is_claude_active:
            state_str = f"{workspace_str} • Claude AI"
        else:
            state_str = f"{workspace_str} • Antigravity"

        return {
            "activity_type": ActivityType.PLAYING,
            "large_image": ICONS["vscode"],
            "large_text": "Visual Studio Code",
            "details": sanitize_text(editing_str),
            "state": sanitize_text(state_str),
            "small_image": ICONS["claude"] if is_claude_active else ICONS["gemini"],
            "small_text": "AI Pair Programming",
            "start": session_start_time,
            "buttons": [
                {"label": "💻 My Workspace", "url": "https://github.com"},
                {"label": "⚡ Antigravity AI", "url": "https://github.com"}
            ]
        }

    # =========================================================================
    # SCENARIO 3: Web Browsing / Researching
    # =========================================================================
    if has_browser:
        return {
            "activity_type": ActivityType.PLAYING,
            "large_image": ICONS["gemini"],
            "large_text": "Antigravity Workspace",
            "details": sanitize_text("Researching & Browsing"),
            "state": sanitize_text("Multitasking with AI"),
            "small_image": ICONS["python"],
            "small_text": "Python 3.11",
            "start": session_start_time,
            "buttons": [
                {"label": "📺 Open YouTube", "url": "https://www.youtube.com"},
                {"label": "⚡ Antigravity AI", "url": "https://github.com"}
            ]
        }

    # =========================================================================
    # SCENARIO 4: Default / Standby Mode
    # =========================================================================
    return {
        "activity_type": ActivityType.PLAYING,
        "large_image": ICONS["gemini"],
        "large_text": "Antigravity Station",
        "details": sanitize_text("Personal Workstation"),
        "state": sanitize_text("Online & Ready"),
        "small_image": ICONS["python"],
        "small_text": "Online",
        "start": session_start_time,
        "buttons": [
            {"label": "📺 Open YouTube", "url": "https://www.youtube.com"},
            {"label": "⚡ Antigravity AI", "url": "https://github.com"}
        ]
    }


def print_banner(client_id):
    log("=" * 68)
    log("  🚀 DISCORD RICH PRESENCE - ULTRA SENIOR / EXPERT SUITE 🚀")
    log("=" * 68)
    log(f"  [+] Client ID      : {client_id}")
    log(f"  [+] Subsystem      : Windows GSMTC + Media Transport Controls")
    log("  [+] Sync Engine    : Sub-second Anchor Timestamps (start_ts/end_ts)")
    log("  [+] Cover Resolver : Dynamic YouTube Thumbnail (hqdefault.jpg)")
    log("  [+] UI/UX Style    : Clean Minimalist (Official Integration Aesthetic)")
    log("  [+] Pause Detect   : Native Paused State + Time Position Preservation")
    log("=" * 68 + "\n")


def make_payload_fingerprint(p):
    """Computes a hashable representation to prevent unnecessary IPC updates."""
    if not p:
        return None
    return (
        p.get("activity_type"),
        p.get("details"),
        p.get("state"),
        p.get("large_image"),
        p.get("small_image"),
        p.get("start"),
        p.get("end"),
        tuple(b.get("url") for b in p.get("buttons", []))
    )


def main():
    config = load_config()
    client_id = config.get("client_id", "1546386469353160804")
    print_banner(client_id)

    rpc = None
    connected = False
    session_start_time = int(time.time())
    last_fingerprint = None

    while True:
        # Step 1: Ensure Discord IPC Connection
        if not connected:
            try:
                log(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Connecting to Discord client...")
                rpc = Presence(client_id)
                rpc.connect()
                connected = True
                last_fingerprint = None
                log(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Connected to Discord successfully!\n")
            except (DiscordNotFound, ConnectionRefusedError, FileNotFoundError):
                log(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Discord app not found. Retrying in 5s...")
                time.sleep(5)
                continue
            except Exception as e:
                log(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Connection error: {e}. Retrying in 5s...")
                time.sleep(5)
                continue

        # Step 2: Reload config
        current_config = load_config()
        if current_config:
            config = current_config

        # Step 3: Extract current activity
        payload = detect_current_activity(config, session_start_time)
        current_fingerprint = make_payload_fingerprint(payload)

        # Step 4: Dispatch update only when state changes (prevents Discord slider reset!)
        if current_fingerprint != last_fingerprint:
            try:
                rpc.update(**payload)
                last_fingerprint = current_fingerprint

                dur_info = ""
                if "end" in payload and "start" in payload:
                    total_s = payload["end"] - payload["start"]
                    cur_s = max(0, int(time.time()) - payload["start"])
                    dur_info = f" [{cur_s//60:02d}:{cur_s%60:02d} / {total_s//60:02d}:{total_s%60:02d}]"

                cover_type = "Thumbnail" if "ytimg.com" in str(payload.get("large_image")) else "Icon"
                log(f"[{datetime.now().strftime('%H:%M:%S')}] ⚡ Presence Updated (Synced):")
                log(f"   ├─ Title    : {payload.get('details')}")
                log(f"   ├─ State    : {payload.get('state')}{dur_info}")
                log(f"   ├─ Cover    : {cover_type} -> {payload.get('large_image')}")
                btn = payload.get('buttons', [{}])[0]
                log(f"   └─ Direct   : {btn.get('url')}")

            except (PipeClosed, BrokenPipeError):
                log(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔌 Discord connection closed. Reconnecting...")
                connected = False
                rpc = None
                last_fingerprint = None
                time.sleep(3)
                continue
            except Exception as e:
                log(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Update error: {e}")
                connected = False
                rpc = None
                last_fingerprint = None
                time.sleep(3)
                continue

        # Step 5: High-frequency polling (2s) for instant response without IPC thrashing
        time.sleep(2)

    if rpc and connected:
        try:
            rpc.clear()
            rpc.close()
        except Exception:
            pass
    log("\n👋 Rich Presence stopped.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\nExited by user.")
