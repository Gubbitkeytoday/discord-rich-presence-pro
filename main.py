"""
Discord Rich Presence Pro
==========================
โชว์เพลง/คลิปที่กำลังเล่น (YouTube, Facebook, Netflix, Twitch, TikTok, Spotify, SoundCloud ฯลฯ)
และแอปพลิเคชันที่ใช้งาน (VS Code, Figma, Blender, GitHub, Notion, ChatGPT, Postman)
บนโปรไฟล์ Discord แบบเรียลไทม์ ครบถ้วน สวยงาม และกินทรัพยากรน้อยที่สุด

หลักการออกแบบ (Enterprise Quality):
- ซิงค์สื่อผ่าน Windows GSMTC Kernel แบบเรียลไทม์ ไม่ต้องลง Browser Extension
- คำนวณ Anchor Timestamp แบบ Sub-Second Precision หลอดเวลาตรง ไม่กระตุก ไม่รีเซ็ต
- ส่งข้อมูลให้ Discord เฉพาะตอน "เปลี่ยน" เท่านั้น (Deduplication) ไม่ชน Rate Limit
- ระบบ LRU In-Memory Cache ดึงภาพหน้าปกคมชัดระดับ MaxRes/HQ
- สแกนหน้าต่างและสถานะระบบแบบประหยัดพลังงาน (Efficiency Mode / EcoQoS)
- ตรวจจับเกม Fullscreen อัตโนมัติ เพื่อหลบทางให้สถานะเกม
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from collections import OrderedDict
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from typing import Optional

IS_WINDOWS = sys.platform == "win32"

# --------------------------------------------------------------------------- #
#  Optional Windows-only imports (guarded so the module can be unit-tested)   #
# --------------------------------------------------------------------------- #
if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    import psutil
    from pypresence import (ActivityType, DiscordNotFound, PipeClosed, Presence,
                            StatusDisplayType)

    # Windows Media API: รองรับทั้ง winrt (ตัวใหม่ ใช้ได้ถึง Python 3.13+) และ winsdk (ตัวเก่า ≤3.12)
    HAS_WINSDK = False
    MEDIA_BACKEND = "none"
    for _mod in ("winrt.windows.media.control", "winsdk.windows.media.control"):
        try:
            import importlib
            _mc = importlib.import_module(_mod)
            SessionManager = _mc.GlobalSystemMediaTransportControlsSessionManager
            PlaybackStatus = _mc.GlobalSystemMediaTransportControlsSessionPlaybackStatus
            HAS_WINSDK = True
            MEDIA_BACKEND = _mod.split(".")[0]
            break
        except Exception:  # pragma: no cover
            continue

    try:  # tray icon (ไม่บังคับ — ถ้าไม่มีก็รันแบบเงียบ)
        import pystray
        from PIL import Image, ImageDraw
        HAS_TRAY = True
    except Exception:  # pragma: no cover
        HAS_TRAY = False
else:  # pragma: no cover - test stubs
    HAS_WINSDK = False
    HAS_TRAY = False
    MEDIA_BACKEND = "none"

    class ActivityType:  # type: ignore
        PLAYING, LISTENING, WATCHING = 0, 2, 3

    class StatusDisplayType:  # type: ignore
        NAME, STATE, DETAILS = 0, 1, 2


# ถ้าถูก build เป็น .exe (PyInstaller) ให้ config/log อยู่ข้าง exe ไม่ใช่ใน temp
BASE_DIR = (os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.abspath(__file__)))
APP_VERSION = "2.1.0"
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOG_PATH = os.path.join(BASE_DIR, "rpc.log")

DEFAULT_CLIENT_ID = "1546386469353160804"

# Icons (PNG, transparent, high-res)
ICONS = {
    "youtube": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/youtube.png",
    "youtube_music": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/youtube-music.png",
    "spotify": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/spotify.png",
    "facebook": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/facebook.png",
    "messenger": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/facebook-messenger.png",
    "netflix": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/netflix.png",
    "twitch": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/twitch.png",
    "tiktok": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/tiktok.png",
    "soundcloud": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/soundcloud.png",
    "instagram": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/instagram.png",
    "twitter": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/twitter.png",
    "github": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/github.png",
    "figma": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/figma.png",
    "blender": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/blender.png",
    "chatgpt": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/chatgpt.png",
    "vscode": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/visual-studio-code.png",
    "claude": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/claude-ai.png",
    "gemini": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/google-gemini.png",
    "notion": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/notion.png",
    "postman": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/postman.png",
    "python": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/python.png",
    "windows": "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/windows.png",
}

BROWSERS = {"chrome.exe", "msedge.exe", "brave.exe", "firefox.exe", "opera.exe", "opera_gx.exe", "vivaldi.exe", "arc.exe"}
# โปรเซสที่ต่อให้ fullscreen ก็ "ไม่ใช่เกม"
NOT_A_GAME = BROWSERS | {
    "explorer.exe", "discord.exe", "code.exe", "claude.exe", "vlc.exe", "mpc-hc64.exe",
    "wwahost.exe", "applicationframehost.exe", "searchhost.exe", "startmenuexperiencehost.exe",
    "shellexperiencehost.exe", "lockapp.exe", "textinputhost.exe", "antigravity.exe",
    "figma.exe", "blender.exe", "notion.exe", "postman.exe", "githubdesktop.exe", "spotify.exe",
    "slack.exe", "telegram.exe", "messenger.exe"
}

# ข้อความ 2 ภาษา
STRINGS = {
    "th": {
        "paused": "หยุดชั่วคราว",
        "by": "โดย",
        "coding_in": "เขียนโค้ดใน",
        "editing": "กำลังแก้",
        "writing_code": "กำลังเขียนโค้ด",
        "workspace": "Workspace",
        "browsing": "กำลังค้นคว้า / ท่องเว็บ",
        "multitask": "ทำงานร่วมกับ AI",
        "standby": "Personal Workstation",
        "online": "ออนไลน์ • พร้อมทำงาน",
        "watch_btn": "▶ ดูคลิปนี้บน YouTube",
        "listen_btn": "▶ ฟังเพลงนี้",
        "channel": "ช่อง",
        "fb_watch": "รับชมวิดีโอบน Facebook",
        "fb_state": "Facebook Watch",
        "fb_btn": "▶ Facebook Watch",
        "fb_reel": "วิดีโอสั้น Facebook Reels",
        "fb_reel_state": "Facebook Reels • คลิปสั้น",
        "fb_reel_btn": "▶ Facebook Reels",
        "fb_feed": "กำลังท่องฟีด Facebook",
        "fb_feed_state": "News Feed • สังคมออนไลน์",
        "messenger": "Facebook Messenger",
        "chatting": "กำลังแชท / สนทนาข้อความ",
    },
    "en": {
        "paused": "Paused",
        "by": "by",
        "coding_in": "Coding in",
        "editing": "Editing",
        "writing_code": "Writing code",
        "workspace": "Workspace",
        "browsing": "Researching & Browsing",
        "multitask": "Multitasking with AI",
        "standby": "Personal Workstation",
        "online": "Online & Ready",
        "watch_btn": "▶ Watch on YouTube",
        "listen_btn": "▶ Listen",
        "channel": "Channel",
        "fb_watch": "Watching Video on Facebook",
        "fb_state": "Facebook Watch",
        "fb_btn": "▶ Facebook Watch",
        "fb_reel": "Short Video on Facebook Reels",
        "fb_reel_state": "Facebook Reels • Short Videos",
        "fb_reel_btn": "▶ Facebook Reels",
        "fb_feed": "Browsing Facebook Feed",
        "fb_feed_state": "News Feed • Social Network",
        "messenger": "Facebook Messenger",
        "chatting": "Chatting & Messaging",
    },
}

# --------------------------------------------------------------------------- #
#  Logging (ไฟล์หมุนเวียน 256 KB + console ถ้ามี)                              #
# --------------------------------------------------------------------------- #
log = logging.getLogger("rpc")


def setup_logging(verbose: bool) -> None:
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname).1s %(message)s", "%H:%M:%S")
    fh = RotatingFileHandler(LOG_PATH, maxBytes=256 * 1024, backupCount=1, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    if sys.stdout is not None:  # pythonw.exe ไม่มี console
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        log.addHandler(sh)


# --------------------------------------------------------------------------- #
#  Config (อ่านใหม่เฉพาะตอนไฟล์เปลี่ยน)                                          #
# --------------------------------------------------------------------------- #
DEFAULT_CONFIG = {
    "client_id": DEFAULT_CLIENT_ID,
    "language": "th",
    "update_interval_seconds": 5,
    "gaming_interval_seconds": 15,
    "show_cover_art": True,
    "pause_when_gaming": True,
    "game_processes": [],
    "custom_button": {"label": "⚡ Antigravity AI", "url": "https://github.com"},
    "buttons": [
        {"label": "📺 Open YouTube", "url": "https://www.youtube.com"},
        {"label": "⚡ Antigravity AI", "url": "https://github.com"},
    ],
}


class Config:
    def __init__(self, path: str):
        self.path = path
        self._mtime = -1.0
        self.data = dict(DEFAULT_CONFIG)
        self.reload()

    def reload(self) -> bool:
        if not os.path.exists(self.path):  # เครื่องใหม่ / คนอื่นเอาไปใช้ -> สร้างค่าเริ่มต้นให้
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
                log.info("created default config.json")
            except OSError as e:
                log.warning("cannot create config.json: %s", e)
        try:
            mtime = os.path.getmtime(self.path)
        except OSError:
            return False
        if mtime == self._mtime:
            return False
        self._mtime = mtime
        try:
            with open(self.path, "r", encoding="utf-8-sig") as f:
                user = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(user or {})
            self.data = merged
            log.info("config.json loaded")
            return True
        except Exception as e:
            log.warning("config.json invalid (%s) - keeping previous values", e)
            return False

    def __getitem__(self, k):
        return self.data.get(k, DEFAULT_CONFIG.get(k))

    @property
    def strings(self):
        return STRINGS.get(str(self["language"]).lower(), STRINGS["th"])


# --------------------------------------------------------------------------- #
#  Text helpers                                                               #
# --------------------------------------------------------------------------- #
_NOISE = re.compile(
    r"\s*[\(\[【]\s*(official\s*(music\s*)?(video|audio|mv|m/v|lyric\s*video)|lyrics?|"
    r"hd|hq|4k|8k|1080p|720p|visualizer|audio)\s*[\)\]】]\s*",
    re.IGNORECASE,
)


def clean_title(title: str) -> str:
    """ตัดคำรกที่ไม่ใช่ชื่อเพลง เช่น (Official MV) [4K] และชื่อเว็บเบราว์เซอร์"""
    t = (title or "").strip()
    t = re.sub(r"\s+-\s+YouTube(\s+Music)?$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+[-|]\s+Facebook$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^Watch\s+\|\s+Facebook$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+[-|]\s+Netflix$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+[-|]\s+Twitch$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+[-|]\s+SoundCloud$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^\(\d+\)\s*", "", t)          # "(3) title" = แจ้งเตือนของแท็บ
    t = _NOISE.sub(" ", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" -•|")
    return t or (title or "").strip()


def fit(text: Optional[str], max_len: int = 128) -> Optional[str]:
    """Discord: 2-128 chars. ตัดที่ขอบคำ ไม่ตัดกลางคำ"""
    if not text:
        return None
    s = str(text).strip()
    if len(s) < 2:
        s = s.ljust(2)
    if len(s) > max_len:
        cut = s[: max_len - 1]
        if " " in cut[max_len // 2:]:
            cut = cut[: cut.rfind(" ")]
        s = cut.rstrip() + "…"
    return s


def fit_button(label: str) -> str:
    return fit(label, 32) or "Open"


def _mmss(seconds: float) -> str:
    s = max(0, int(seconds))
    return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"


# --------------------------------------------------------------------------- #
#  Background YouTube resolver (ไม่ block main loop เด็ดขาด)                     #
# --------------------------------------------------------------------------- #
@dataclass
class VideoInfo:
    video_id: Optional[str] = None
    video_url: str = "https://www.youtube.com"
    channel_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    ready: bool = False
    expires: float = float("inf")  # ผลลัพธ์ที่หาไม่เจอจะหมดอายุ -> ลองใหม่ (กันเน็ตสะดุดชั่วคราว)


class YouTubeResolver:
    """หา video id + ปกจริง จากชื่อคลิป/ช่อง โดยทำงานใน thread แยก และ cache ผล (LRU 200 รายการ)"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
        "Cookie": "CONSENT=YES+1; SOCS=CAI",
    }

    def __init__(self, max_items: int = 200):
        self._cache: "OrderedDict[str, VideoInfo]" = OrderedDict()
        self._custom_cache: "OrderedDict[str, str]" = OrderedDict()
        self._pending: set[str] = set()
        self._lock = threading.Lock()
        self._max = max_items

    @staticmethod
    def key(title: str, artist: str) -> str:
        return f"{title.lower()}::{artist.lower()}".strip()

    def get_custom_cover(self, prefix: str, title: str, artist: str, thumb_bytes: Optional[bytes]) -> Optional[str]:
        """ดึงรูปหน้าปกของ Facebook Reels / Watch หรือบริการอื่นจาก GSMTC thumbnail โดยอัปโหลด background CDN"""
        if not thumb_bytes:
            return None
        k = f"{prefix}::{title.lower()}::{artist.lower()}".strip()
        with self._lock:
            if k in self._custom_cache:
                self._custom_cache.move_to_end(k)
                return self._custom_cache[k]
            if k in self._pending:
                return None
            self._pending.add(k)
        threading.Thread(target=self._custom_upload_worker, args=(k, thumb_bytes), daemon=True, name="cover-uploader").start()
        return None

    def _custom_upload_worker(self, k: str, data: bytes) -> None:
        url = None
        try:
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            body = io.BytesIO()
            body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"reqtype\"\r\n\r\nfileupload\r\n".encode())
            body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"fileToUpload\"; filename=\"cover.png\"\r\nContent-Type: image/png\r\n\r\n".encode())
            body.write(data)
            body.write(f"\r\n--{boundary}--\r\n".encode())

            req = urllib.request.Request("https://catbox.moe/user/api.php", data=body.getvalue(), headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "Mozilla/5.0"
            })
            with urllib.request.urlopen(req, timeout=8) as resp:
                res = resp.read().decode("utf-8").strip()
                if res.startswith("http"):
                    url = res
        except Exception as e:
            log.debug("custom cover upload error: %s", e)

        with self._lock:
            self._pending.discard(k)
            if url:
                self._custom_cache[k] = url
                while len(self._custom_cache) > self._max:
                    self._custom_cache.popitem(last=False)

    def get(self, title: str, artist: str) -> VideoInfo:
        k = self.key(title, artist)
        with self._lock:
            if k in self._cache:
                hit = self._cache[k]
                if hit.expires > time.monotonic():
                    self._cache.move_to_end(k)
                    return hit
                del self._cache[k]  # หมดอายุ -> หาใหม่
            if k in self._pending:
                return VideoInfo()
            self._pending.add(k)
        threading.Thread(target=self._worker, args=(k, title, artist), daemon=True, name="yt-resolver").start()
        return VideoInfo()

    def _store(self, k: str, info: VideoInfo) -> None:
        with self._lock:
            self._pending.discard(k)
            self._cache[k] = info
            while len(self._cache) > self._max:
                self._cache.popitem(last=False)

    def _worker(self, k: str, title: str, artist: str) -> None:
        info = VideoInfo(ready=True)
        try:
            q = urllib.parse.quote_plus(f"{title} {artist}".strip())
            # sp=EgIQAQ%3D%3D = filter "Video" only (ตัด Shorts/Playlist/Channel ออก)
            url = f"https://www.youtube.com/results?search_query={q}&sp=EgIQAQ%253D%253D&hl=en"
            html = self._fetch(url, 6)
            if html:
                m = re.search(r'"videoRenderer":\{"videoId":"([A-Za-z0-9_-]{11})"', html)
                if not m:
                    m = re.search(r'"videoId":"([A-Za-z0-9_-]{11})"', html)
                if m:
                    vid = m.group(1)
                    info.video_id = vid
                    info.video_url = f"https://www.youtube.com/watch?v={vid}"
                    tail = html[m.end(): m.end() + 12000]
                    ch = re.search(r'"canonicalBaseUrl":"(/@[^"]+|/channel/[^"]+)"', tail)
                    if ch:
                        info.channel_url = "https://www.youtube.com" + ch.group(1)
                    info.thumbnail_url = self._best_thumbnail(vid)
            if not info.video_id:
                info.video_url = f"https://www.youtube.com/results?search_query={q}"
                info.expires = time.monotonic() + 120  # ลองใหม่ใน 2 นาที
        except Exception as e:  # pragma: no cover
            log.debug("resolver error: %s", e)
        self._store(k, info)
        log.debug("resolved %s -> %s", title[:40], info.video_id)

    def _fetch(self, url: str, timeout: int) -> Optional[str]:
        req = urllib.request.Request(url, headers=self.HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(2_000_000).decode("utf-8", "ignore")
        except Exception as e:
            log.debug("fetch failed %s: %s", url[:60], e)
            return None

    def _best_thumbnail(self, vid: str) -> str:
        """maxresdefault (1280x720 ไม่มีแถบดำ) ถ้ามีจริง; ไม่งั้น mqdefault (320x180 ไม่มีแถบดำเช่นกัน)
        *หลีกเลี่ยง hqdefault เพราะเป็น 4:3 มีแถบดำบน-ล่าง*"""
        maxres = f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"
        req = urllib.request.Request(maxres, method="HEAD", headers=self.HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=4) as r:
                if r.status == 200:
                    return maxres
        except Exception:
            pass
        return f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg"


# --------------------------------------------------------------------------- #
#  Windows probes (media / processes / windows / fullscreen game)              #
# --------------------------------------------------------------------------- #
@dataclass
class MediaState:
    title: str
    artist: str
    position: float
    duration: float
    app: str
    playing: bool
    anchor: float = 0.0  # epoch (วินาที) ตอนที่ Windows วัดค่า position — ใช้คำนวณเวลาให้ตรงเสี้ยววินาที
    thumb_bytes: Optional[bytes] = None

    def position_at(self, now: float) -> float:
        """ตำแหน่งจริง ณ เวลา now (ถ้ากำลังเล่น เวลาเดินต่อจาก anchor)"""
        if self.playing and self.anchor > 0:
            return min(self.position + max(0.0, now - self.anchor), self.duration or 1e12)
        return self.position


@dataclass
class SystemSnapshot:
    procs: set = field(default_factory=set)
    titles: list = field(default_factory=list)
    taken_at: float = 0.0


class WindowsProbe:
    def __init__(self):
        self.loop = asyncio.new_event_loop() if HAS_WINSDK else None
        self._mgr = None
        self._snap = SystemSnapshot()
        if IS_WINDOWS:
            self.user32 = ctypes.windll.user32
            self.kernel32 = ctypes.windll.kernel32
            self._WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    # ---- process / window snapshot (cached) ----
    def snapshot(self, max_age: float = 10.0) -> SystemSnapshot:
        now = time.monotonic()
        if now - self._snap.taken_at < max_age:
            return self._snap
        procs = set()
        try:
            for p in psutil.process_iter(["name"]):
                n = p.info["name"]
                if n:
                    procs.add(n.lower())
        except Exception:
            pass
        titles: list[str] = []

        def cb(hwnd, _):
            if self.user32.IsWindowVisible(hwnd):
                n = self.user32.GetWindowTextLengthW(hwnd)
                if n > 0:
                    buf = ctypes.create_unicode_buffer(n + 1)
                    self.user32.GetWindowTextW(hwnd, buf, n + 1)
                    if buf.value.strip():
                        titles.append(buf.value.strip())
            return True

        try:
            self.user32.EnumWindows(self._WNDENUMPROC(cb), 0)
        except Exception:
            pass
        self._snap = SystemSnapshot(procs, titles, now)
        return self._snap

    # ---- foreground fullscreen game detection (cheap: 4 API calls) ----
    def foreground_game(self, extra_games: set[str]) -> Optional[str]:
        try:
            hwnd = self.user32.GetForegroundWindow()
            if not hwnd:
                return None
            pid = wintypes.DWORD()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if not pid.value:
                return None
            name = psutil.Process(pid.value).name().lower()
            if name in extra_games:
                return name
            if name in NOT_A_GAME or name.startswith("python"):
                return None
            rect = wintypes.RECT()
            self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            sw, sh = self.user32.GetSystemMetrics(0), self.user32.GetSystemMetrics(1)
            w, h = rect.right - rect.left, rect.bottom - rect.top
            if w >= sw and h >= sh:  # borderless / exclusive fullscreen
                return name
        except Exception:
            pass
        return None

    # ---- media via GSMTC, reusing one manager + one loop ----
    def media(self) -> Optional[MediaState]:
        if not HAS_WINSDK:
            return None
        try:
            return self.loop.run_until_complete(self._media_async())
        except Exception as e:
            log.debug("media probe error: %s", e)
            self._mgr = None
            return None

    async def _media_async(self) -> Optional[MediaState]:
        if self._mgr is None:
            self._mgr = await SessionManager.request_async()
        sessions = list(self._mgr.get_sessions())
        current = self._mgr.get_current_session()
        ordered = ([current] if current else []) + [s for s in sessions if s is not current]

        chosen, playing = None, False
        for s in ordered:  # เลือกตัวที่ PLAYING ก่อน
            pb = s.get_playback_info()
            if pb and pb.playback_status == PlaybackStatus.PLAYING:
                chosen, playing = s, True
                break
        if chosen is None:
            for s in ordered:  # ไม่มีที่เล่นอยู่ -> เอาตัวที่ PAUSED
                pb = s.get_playback_info()
                if pb and pb.playback_status == PlaybackStatus.PAUSED:
                    chosen = s
                    break
        if chosen is None:
            return None

        props = await chosen.try_get_media_properties_async()
        tl = chosen.get_timeline_properties()
        title = (props.title or "").strip() if props else ""
        if not title:
            return None
        anchor = 0.0
        try:
            if tl and tl.last_updated_time:
                anchor = tl.last_updated_time.timestamp()
        except Exception:
            anchor = 0.0

        thumb_bytes = None
        if props and props.thumbnail:
            try:
                stream = await props.thumbnail.open_read_async()
                if stream and 0 < stream.size < 5_000_000:
                    try:
                        import winsdk.windows.storage.streams as _ss
                    except ImportError:
                        import winrt.windows.storage.streams as _ss
                    reader = _ss.DataReader(stream)
                    await reader.load_async(stream.size)
                    buf = bytearray(stream.size)
                    reader.read_bytes(buf)
                    thumb_bytes = bytes(buf)
            except Exception as e:
                log.debug("thumbnail extraction skipped: %s", e)

        return MediaState(
            title=title,
            artist=(props.artist or "").strip(),
            position=tl.position.total_seconds() if tl and tl.position else 0.0,
            duration=tl.end_time.total_seconds() if tl and tl.end_time else 0.0,
            app=(chosen.source_app_user_model_id or "").lower(),
            playing=playing,
            anchor=anchor,
            thumb_bytes=thumb_bytes,
        )

    # ---- make ourselves a good neighbour to games ----
    def lower_priority(self) -> None:
        try:
            h = self.kernel32.GetCurrentProcess()
            self.kernel32.SetPriorityClass(h, 0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS

            class PPTS(ctypes.Structure):
                _fields_ = [("Version", wintypes.ULONG), ("ControlMask", wintypes.ULONG), ("StateMask", wintypes.ULONG)]

            st = PPTS(1, 0x1, 0x1)  # EXECUTION_SPEED throttling = EcoQoS / "Efficiency mode"
            self.kernel32.SetProcessInformation(h, 4, ctypes.byref(st), ctypes.sizeof(st))
            log.info("process priority: below-normal + efficiency mode")
        except Exception as e:
            log.debug("priority tweak skipped: %s", e)


# --------------------------------------------------------------------------- #
#  Presence builder (pure function -> easy to test)                            #
# --------------------------------------------------------------------------- #
def classify_media(media: MediaState, titles: list[str]) -> str:
    """
    Returns one of:
    'youtube_music' | 'spotify' | 'youtube' | 'facebook_reel' | 'facebook_watch' |
    'netflix' | 'twitch' | 'tiktok' | 'soundcloud' | 'other'
    """
    app = media.app.lower()
    m_title = media.title.lower()
    m_artist = media.artist.lower()

    if "spotify" in app:
        return "spotify"
    if "netflix" in app:
        return "netflix"

    # 1) ตรวจสอบจากชื่อคลิป/ศิลปินที่ GSMTC ส่งมาโดยตรง
    if "youtube music" in m_title or "youtube music" in m_artist:
        return "youtube_music"
    if "soundcloud" in m_title or "soundcloud" in m_artist:
        return "soundcloud"
    if "twitch" in m_title or "twitch" in m_artist:
        return "twitch"
    if "tiktok" in m_title or "tiktok" in m_artist:
        return "tiktok"
    if "facebook" in m_title or "facebook" in m_artist:
        if "reel" in m_title or "reel" in m_artist or (0 < media.duration <= 90):
            return "facebook_reel"
        return "facebook_watch"

    # 2) ตรวจสอบความสอดคล้องกับหัวหน้าต่าง (Content Matching)
    clean_t = clean_title(media.title).lower()
    keywords = [w for w in re.split(r"[\s\-_|()\[\]]+", clean_t) if len(w) >= 3]

    matching_window = None
    for t in titles:
        lt = t.lower()
        if clean_t and (clean_t in lt or (len(keywords) >= 2 and sum(1 for k in keywords if k in lt) >= max(2, len(keywords) // 2))):
            matching_window = lt
            break
        if m_artist and len(m_artist) >= 3 and m_artist in lt:
            matching_window = lt
            break

    if matching_window:
        if "youtube music" in matching_window:
            return "youtube_music"
        if "youtube" in matching_window:
            return "youtube"
        if "reel" in matching_window:
            return "facebook_reel"
        if "facebook" in matching_window or "fb.watch" in matching_window:
            if "reel" in matching_window or (0 < media.duration <= 90):
                return "facebook_reel"
            return "facebook_watch"
        if "netflix" in matching_window:
            return "netflix"
        if "twitch" in matching_window:
            return "twitch"
        if "tiktok" in matching_window:
            return "tiktok"
        if "soundcloud" in matching_window:
            return "soundcloud"

    # 3) กรณีเป็นแท็บเบื้องหลัง หรือไม่พบชื่อตรงๆ ในหัวหน้าต่าง
    lower_titles = [t.lower() for t in titles]

    # ถ้าหัวหน้าต่างระบุชัดเจนว่าเปิดหน้า Reels หรือ Watch โดยเฉพาะ
    if any("reels | facebook" in t or " - reels" in t for t in lower_titles):
        if media.duration <= 180 or media.duration == 0:
            return "facebook_reel"
    if any("watch | facebook" in t or "facebook watch" in t for t in lower_titles):
        return "facebook_watch"

    if any("youtube music" in t for t in lower_titles):
        return "youtube_music"
    if any(" - youtube" in t or "youtube.com" in t for t in lower_titles) or "youtube" in m_title:
        return "youtube"
    if any("netflix" in t for t in lower_titles):
        return "netflix"
    if any("twitch.tv" in t or " - twitch" in t for t in lower_titles):
        return "twitch"
    if any("tiktok" in t for t in lower_titles):
        return "tiktok"
    if any("soundcloud" in t for t in lower_titles):
        return "soundcloud"

    # สำหรับ Browser media ทั่วไปที่เล่นคลิป/เพลงอยู่
    if any(b.split(".")[0] in app for b in BROWSERS):
        return "youtube"
    return "other"


def vscode_context(titles: list[str]) -> tuple[Optional[str], Optional[str]]:
    for t in titles:
        if "Visual Studio Code" in t:
            parts = [p.strip() for p in t.split(" - ")]
            f = parts[0].replace("●", "").strip() if len(parts) >= 2 else None
            ws = parts[1] if len(parts) >= 3 else None
            return f, ws
    return None, None


def build_payload(cfg: Config, media: Optional[MediaState], snap: SystemSnapshot,
                  session_start: int, resolver: YouTubeResolver, now: Optional[int] = None) -> dict:
    S = cfg.strings
    now = int(now if now is not None else time.time())
    procs, titles = snap.procs, snap.titles
    has_vscode = "code.exe" in procs
    has_browser = bool(procs & BROWSERS)
    custom_btn = cfg["custom_button"] or {}
    custom = {"label": fit_button(custom_btn.get("label", "⚡ Antigravity AI")),
              "url": custom_btn.get("url", "https://github.com")}
    vs_file, vs_ws = vscode_context(titles)

    # ======================= A) MEDIA ======================= #
    if media:
        kind = classify_media(media, titles)
        title = clean_title(media.title)
        artist = media.artist or ""
        listening = kind in ("youtube_music", "spotify", "soundcloud")

        info = VideoInfo()
        if kind in ("youtube", "youtube_music"):
            info = resolver.get(title, artist)

        cover = None
        if kind == "facebook_reel":
            app_name = "Facebook Reels"
            icon = ICONS["facebook"]
            fb_cover = resolver.get_custom_cover("fb_reel", title, artist, media.thumb_bytes)
            cover = fb_cover if (cfg["show_cover_art"] and fb_cover) else None
            display_title = title if (title and title.lower() not in ("facebook", "watch", "reels", "video")) else S.get("fb_reel", "วิดีโอสั้น Facebook Reels")
            display_state = f"{artist} • Facebook Reels" if artist else S.get("fb_reel_state", "Facebook Reels • คลิปสั้น")
            btn_primary = {"label": fit_button(S.get("fb_reel_btn", "▶ Facebook Reels")), "url": "https://www.facebook.com/reels"}
        elif kind == "facebook_watch":
            app_name = "Facebook Watch"
            icon = ICONS["facebook"]
            fb_cover = resolver.get_custom_cover("fb_watch", title, artist, media.thumb_bytes)
            cover = fb_cover if (cfg["show_cover_art"] and fb_cover) else None
            display_title = title if (title and title.lower() not in ("facebook", "watch", "reels", "video")) else S.get("fb_watch", "รับชมวิดีโอบน Facebook")
            display_state = f"{artist} • Facebook Watch" if artist else S.get("fb_state", "Facebook Watch")
            btn_primary = {"label": fit_button(S.get("fb_btn", "▶ Facebook Watch")), "url": "https://www.facebook.com/watch"}
        elif kind == "netflix":
            app_name = "Netflix"
            icon = ICONS["netflix"]
            display_title = title or "รับชมภาพยนตร์ / ซีรีส์"
            display_state = artist if artist else "Netflix Original / Series"
            btn_primary = {"label": "▶ Netflix", "url": "https://www.netflix.com"}
        elif kind == "twitch":
            app_name = "Twitch"
            icon = ICONS["twitch"]
            display_title = title or "รับชม Live Stream"
            display_state = f"Streamer: {artist}" if artist else "Twitch Live Stream"
            btn_primary = {"label": "▶ Twitch", "url": "https://www.twitch.tv"}
        elif kind == "tiktok":
            app_name = "TikTok"
            icon = ICONS["tiktok"]
            display_title = title or "TikTok Trends • FYP"
            display_state = artist if artist else "TikTok Trends • FYP"
            btn_primary = {"label": "▶ TikTok", "url": "https://www.tiktok.com"}
        elif kind == "soundcloud":
            app_name = "SoundCloud"
            icon = ICONS["soundcloud"]
            display_title = title
            display_state = artist if artist else "SoundCloud Audio"
            btn_primary = {"label": "▶ SoundCloud", "url": "https://soundcloud.com"}
        elif kind == "spotify":
            app_name = "Spotify"
            icon = ICONS["spotify"]
            display_title = title
            display_state = artist if artist else "Spotify Music"
            btn_primary = {"label": "▶ Spotify", "url": "https://open.spotify.com"}
        else:  # youtube / youtube_music
            app_name = "YouTube Music" if kind == "youtube_music" else "YouTube"
            icon = ICONS["youtube_music"] if kind == "youtube_music" else ICONS["youtube"]
            cover = info.thumbnail_url if (cfg["show_cover_art"] and info.thumbnail_url) else None
            display_title = title
            display_state = artist if artist else app_name
            btn_label = S["listen_btn"] if listening else S["watch_btn"]
            btn_primary = {"label": fit_button(btn_label), "url": info.video_url}

        p = {
            "name": app_name,
            "activity_type": ActivityType.LISTENING if listening else ActivityType.WATCHING,
            "status_display_type": StatusDisplayType.DETAILS,
            "details": fit(display_title),
            "large_image": cover or icon,
            "large_text": fit(display_title),
            "small_image": icon,
            "small_text": app_name,
        }
        if info.video_id:
            p["details_url"] = info.video_url
            p["large_url"] = info.video_url
        if info.channel_url:
            p["state_url"] = info.channel_url

        if has_vscode:
            ws = f"{S['coding_in']} {vs_ws}" if vs_ws else f"{S['coding_in']} VS Code"
            p["state"] = fit(f"{ws} • {display_state}" if display_state else ws)
            p["small_image"] = ICONS["vscode"]
            p["small_text"] = "Visual Studio Code"
        else:
            p["state"] = fit(display_state)

        pos = media.position_at(now)
        if media.playing:
            if media.duration > 0 and media.duration >= pos:
                p["start"] = int(round(now - pos))
                p["end"] = p["start"] + int(round(media.duration))
            else:
                p["start"] = int(round(now - pos)) if pos > 0 else session_start
        else:
            frozen = f" {_mmss(pos)} / {_mmss(media.duration)}" if media.duration > 0 else ""
            p["state"] = fit(f"⏸ {S['paused']}{frozen} • {p['state']}")

        p["buttons"] = [btn_primary, custom]
        return p

    # ======================= B) VS CODE ===================== #
    if has_vscode:
        claude_on = "claude.exe" in procs or any("claude" in t.lower() for t in titles)
        editing = f"{S['editing']} {vs_file}" if vs_file else S["writing_code"]
        ws = f"{S['workspace']}: {vs_ws}" if vs_ws else "Visual Studio Code"
        return {
            "name": "Visual Studio Code",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit(editing),
            "state": fit(f"{ws} • {'Claude AI' if claude_on else 'Antigravity'}"),
            "large_image": ICONS["vscode"],
            "large_text": "Visual Studio Code",
            "small_image": ICONS["claude"] if claude_on else ICONS["gemini"],
            "small_text": "AI Pair Programming",
            "start": session_start,
            "buttons": [{"label": "💻 My Workspace", "url": custom["url"]}, custom],
        }

    # ======================= C) APPS & SOCIAL / CREATIVE ===================== #
    lower_titles = [t.lower() for t in titles]

    # 1. Messenger
    if "messenger.exe" in procs or any("messenger" in t for t in lower_titles):
        return {
            "name": "Facebook Messenger",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit(S.get("chatting", "กำลังแชท / สนทนาข้อความ")),
            "state": fit(S.get("messenger", "Facebook Messenger")),
            "large_image": ICONS["messenger"],
            "large_text": "Facebook Messenger",
            "small_image": ICONS["facebook"],
            "small_text": "Facebook",
            "start": session_start,
            "buttons": [{"label": "💬 Messenger", "url": "https://www.messenger.com"}, custom],
        }

    # 2. Facebook
    if any("facebook" in t and "messenger" not in t for t in lower_titles):
        return {
            "name": "Facebook",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit(S.get("fb_feed", "กำลังท่องฟีด Facebook")),
            "state": fit(S.get("fb_feed_state", "News Feed • สังคมออนไลน์")),
            "large_image": ICONS["facebook"],
            "large_text": "Facebook",
            "small_image": ICONS["windows"],
            "small_text": "Online",
            "start": session_start,
            "buttons": [{"label": "🌐 Facebook", "url": "https://www.facebook.com"}, custom],
        }

    # 3. Figma
    if "figma.exe" in procs or any("figma" in t for t in lower_titles):
        return {
            "name": "Figma",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit("กำลังออกแบบ UI/UX บน Figma"),
            "state": fit("Product Design & Prototyping"),
            "large_image": ICONS["figma"],
            "large_text": "Figma Design",
            "small_image": ICONS["windows"],
            "small_text": "Designing",
            "start": session_start,
            "buttons": [{"label": "🎨 Open Figma", "url": "https://www.figma.com"}, custom],
        }

    # 4. Blender
    if "blender.exe" in procs or any("blender" in t for t in lower_titles):
        return {
            "name": "Blender",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit("กำลังสร้าง 3D Model / เรนเดอร์งาน"),
            "state": fit("3D Creation Suite"),
            "large_image": ICONS["blender"],
            "large_text": "Blender 3D",
            "small_image": ICONS["windows"],
            "small_text": "Rendering",
            "start": session_start,
            "buttons": [{"label": "🧊 Blender", "url": "https://www.blender.org"}, custom],
        }

    # 5. GitHub Desktop / GitHub
    if "githubdesktop.exe" in procs or any("github" in t and ("repository" in t or "commit" in t or "pull request" in t) for t in lower_titles):
        return {
            "name": "GitHub",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit("กำลังจัดการ Repository & Review Code"),
            "state": fit("GitHub Developer Platform"),
            "large_image": ICONS["github"],
            "large_text": "GitHub",
            "small_image": ICONS["windows"],
            "small_text": "Coding",
            "start": session_start,
            "buttons": [{"label": "🐙 GitHub", "url": "https://github.com"}, custom],
        }

    # 6. ChatGPT / Claude AI
    if any("chatgpt" in t or "openai" in t for t in lower_titles):
        return {
            "name": "ChatGPT",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit("กำลังสนทนาและระดมความคิดกับ AI"),
            "state": fit("OpenAI ChatGPT"),
            "large_image": ICONS["chatgpt"],
            "large_text": "ChatGPT",
            "small_image": ICONS["windows"],
            "small_text": "AI Assistant",
            "start": session_start,
            "buttons": [{"label": "🤖 ChatGPT", "url": "https://chatgpt.com"}, custom],
        }
    if "claude.exe" in procs or any("claude" in t for t in lower_titles):
        return {
            "name": "Claude AI",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit("กำลังทำงานร่วมกับ Claude AI"),
            "state": fit("Anthropic Claude Assistant"),
            "large_image": ICONS["claude"],
            "large_text": "Claude AI",
            "small_image": ICONS["windows"],
            "small_text": "AI Assistant",
            "start": session_start,
            "buttons": [{"label": "✨ Claude AI", "url": "https://claude.ai"}, custom],
        }

    # 7. Notion
    if "notion.exe" in procs or any("notion" in t for t in lower_titles):
        return {
            "name": "Notion",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit("กำลังบันทึกและจัดระเบียบงานบน Notion"),
            "state": fit("Notion Connected Workspace"),
            "large_image": ICONS["notion"],
            "large_text": "Notion",
            "small_image": ICONS["windows"],
            "small_text": "Workspace",
            "start": session_start,
            "buttons": [{"label": "📝 Notion", "url": "https://www.notion.so"}, custom],
        }

    # 8. Postman
    if "postman.exe" in procs or any("postman" in t for t in lower_titles):
        return {
            "name": "Postman",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit("กำลังทดสอบและพัฒนา API บน Postman"),
            "state": fit("API Development Platform"),
            "large_image": ICONS["postman"],
            "large_text": "Postman",
            "small_image": ICONS["windows"],
            "small_text": "Testing APIs",
            "start": session_start,
            "buttons": [{"label": "🚀 Postman", "url": "https://www.postman.com"}, custom],
        }

    # 9. Twitter / X
    if any("twitter" in t or " / x" in t for t in lower_titles):
        return {
            "name": "X (Twitter)",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit("กำลังอัปเดตข่าวสารบน X (Twitter)"),
            "state": fit("Trending News & Feed"),
            "large_image": ICONS["twitter"],
            "large_text": "X (Twitter)",
            "small_image": ICONS["windows"],
            "small_text": "Social",
            "start": session_start,
            "buttons": [{"label": "𝕏 Open X", "url": "https://x.com"}, custom],
        }

    # 10. Instagram
    if any("instagram" in t for t in lower_titles):
        return {
            "name": "Instagram",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit("กำลังท่อง Instagram Feed & Stories"),
            "state": fit("Photos & Reels"),
            "large_image": ICONS["instagram"],
            "large_text": "Instagram",
            "small_image": ICONS["windows"],
            "small_text": "Social",
            "start": session_start,
            "buttons": [{"label": "📸 Instagram", "url": "https://www.instagram.com"}, custom],
        }

    # ======================= D) BROWSING ==================== #
    buttons = [{"label": fit_button(b.get("label", "Open")), "url": b.get("url", "https://www.youtube.com")}
               for b in (cfg["buttons"] or [])][:2] or [custom]
    if has_browser:
        return {
            "name": "Antigravity",
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "details": fit(S["browsing"]),
            "state": fit(S["multitask"]),
            "large_image": ICONS["gemini"],
            "large_text": "Antigravity Workspace",
            "small_image": ICONS["python"],
            "small_text": "Python 3.11",
            "start": session_start,
            "buttons": buttons,
        }

    # ======================= E) STANDBY ===================== #
    return {
        "name": "Antigravity",
        "activity_type": ActivityType.PLAYING,
        "status_display_type": StatusDisplayType.NAME,
        "details": fit(S["standby"]),
        "state": fit(S["online"]),
        "large_image": ICONS["gemini"],
        "large_text": "Antigravity Station",
        "small_image": ICONS["python"],
        "small_text": "Online",
        "start": session_start,
        "buttons": buttons,
    }



def signature(payload: dict) -> str:
    """ลายเซ็นของ payload โดยไม่รวม timestamp (ใช้ตัดสินว่า 'เปลี่ยน' จริงไหม)"""
    return json.dumps({k: v for k, v in payload.items() if k not in ("start", "end")},
                      sort_keys=True, ensure_ascii=False, default=str)


def should_send(payload: dict, last_sig: Optional[str], last_start: Optional[int],
                last_sent_at: float, now: float, drift_tolerance: int = 3, heartbeat: float = 900) -> bool:
    """ส่งเมื่อ (1) เนื้อหาเปลี่ยน (2) มีการ seek/pause จน start เลื่อน >3 วิ (3) heartbeat ทุก 15 นาที"""
    sig = signature(payload)
    if sig != last_sig:
        return True
    if "start" in payload and last_start is not None and abs(payload["start"] - last_start) > drift_tolerance:
        return True
    return (now - last_sent_at) > heartbeat


# --------------------------------------------------------------------------- #
#  Main loop (ควบคุมได้จาก tray: pause / quit)                                 #
# --------------------------------------------------------------------------- #
class Controller:
    """สถานะร่วมระหว่าง main loop กับ tray icon"""

    def __init__(self):
        self.stop = threading.Event()
        self.paused = threading.Event()   # set = ผู้ใช้กด "หยุดชั่วคราว" จาก tray
        self.status = "starting"          # ข้อความสั้น ๆ โชว์ใน tray
        self.wake = threading.Event()     # ปลุก loop ทันทีเมื่อกดปุ่มใน tray

    def sleep(self, seconds: float) -> None:
        self.wake.wait(timeout=seconds)
        self.wake.clear()


def banner(client_id: str) -> None:
    log.info("=" * 60)
    log.info("  DISCORD RICH PRESENCE PRO v%s", APP_VERSION)
    log.info("  client id : %s", client_id)
    log.info("  media     : %s", f"Windows GSMTC via {MEDIA_BACKEND}" if HAS_WINSDK
             else "DISABLED - pip install winrt-Windows.Media.Control (or winsdk)")
    log.info("  tray icon : %s", "yes" if HAS_TRAY else "no (pip install pystray pillow)")
    log.info("  folder    : %s", BASE_DIR)
    log.info("=" * 60)


def run(ctl: Controller) -> None:
    cfg = Config(CONFIG_PATH)
    client_id = str(cfg["client_id"] or DEFAULT_CLIENT_ID)
    banner(client_id)

    probe = WindowsProbe()
    probe.lower_priority()
    resolver = YouTubeResolver()

    rpc = None
    session_start = int(time.time())
    last_sig: Optional[str] = None
    last_start: Optional[int] = None
    last_sent_at = 0.0
    hidden = False  # presence ถูก clear อยู่ (เพราะเกม หรือผู้ใช้กดหยุด)

    def clear_presence(reason: str) -> bool:
        nonlocal rpc, last_sig, hidden
        if rpc is None or hidden:
            return True
        try:
            rpc.clear()
            hidden, last_sig = True, None
            log.info("presence hidden (%s)", reason)
            return True
        except Exception:
            rpc = None
            return False

    while not ctl.stop.is_set():
        # 1) connect
        if rpc is None:
            try:
                rpc = Presence(client_id)
                rpc.connect()
                last_sig, last_start, hidden = None, None, False
                ctl.status = "เชื่อมต่อ Discord แล้ว"
                log.info("connected to Discord")
            except (DiscordNotFound, ConnectionRefusedError, FileNotFoundError):
                ctl.status = "รอ Discord เปิด..."
                log.info("Discord not running - retry in 10s")
                rpc = None
                ctl.sleep(10)
                continue
            except Exception as e:
                ctl.status = "เชื่อมต่อไม่ได้ - กำลังลองใหม่"
                log.warning("connect error: %s - retry in 10s", e)
                rpc = None
                ctl.sleep(10)
                continue

        cfg.reload()
        interval = float(cfg["update_interval_seconds"] or 5)

        # 2) user paused from tray
        if ctl.paused.is_set():
            clear_presence("paused by user")
            ctl.status = "หยุดชั่วคราว (กดเริ่มใน tray)"
            ctl.sleep(interval)
            continue

        # 3) gaming? -> hide presence, back off
        game = probe.foreground_game({g.lower() for g in (cfg["game_processes"] or [])})
        if game and cfg["pause_when_gaming"]:
            if not hidden:
                if not clear_presence(f"game {game}"):
                    continue
            ctl.status = f"เล่นเกมอยู่ ({game}) - ซ่อนสถานะ"
            ctl.sleep(float(cfg["gaming_interval_seconds"] or 15))
            continue
        if hidden:
            hidden = False
            log.info("presence resumed")

        # 4) probe + build
        snap = probe.snapshot()
        media = probe.media()
        payload = build_payload(cfg, media, snap, session_start, resolver)

        # 5) send only on change
        now = time.time()
        if should_send(payload, last_sig, last_start, last_sent_at, now):
            try:
                rpc.update(**payload)
                last_sig, last_start, last_sent_at = signature(payload), payload.get("start"), now
                tl = ""
                if "end" in payload:
                    cur, tot = int(now) - payload["start"], payload["end"] - payload["start"]
                    tl = f" [{cur // 60:02d}:{cur % 60:02d}/{tot // 60:02d}:{tot % 60:02d}]"
                log.info("update  %s | %s%s | cover=%s",
                         payload.get("details"), payload.get("state"), tl,
                         "thumb" if "ytimg" in str(payload.get("large_image")) else "icon")
                ctl.status = f"{payload.get('details')}"[:60]
            except (PipeClosed, BrokenPipeError):
                log.info("Discord pipe closed - reconnecting")
                rpc = None
                ctl.sleep(3)
                continue
            except Exception as e:
                log.warning("update error: %s", e)
                rpc = None
                ctl.sleep(3)
                continue

        ctl.sleep(interval)

    # graceful exit: ลบสถานะออกจากโปรไฟล์ก่อนปิด
    if rpc is not None:
        try:
            rpc.clear()
            rpc.close()
        except Exception:
            pass
    log.info("stopped")


# --------------------------------------------------------------------------- #
#  Tray icon (ให้คนทั่วไปรู้ว่ามันรันอยู่ และปิดได้โดยไม่ต้องใช้ Task Manager)   #
# --------------------------------------------------------------------------- #
def _tray_image(active: bool):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = (88, 101, 242, 255) if active else (128, 132, 142, 255)  # Discord blurple / เทาเมื่อหยุด
    d.rounded_rectangle((4, 4, size - 4, size - 4), radius=16, fill=color)
    # สัญลักษณ์ "เล่น" สีขาว
    d.polygon([(24, 18), (24, 46), (46, 32)], fill=(255, 255, 255, 255))
    return img


def _open(path: str) -> None:
    try:
        os.startfile(path)  # type: ignore[attr-defined]
    except Exception as e:
        log.warning("cannot open %s: %s", path, e)


def run_with_tray(ctl: Controller) -> None:
    worker = threading.Thread(target=run, args=(ctl,), daemon=True, name="rpc-loop")
    worker.start()

    def toggle(icon, _item):
        if ctl.paused.is_set():
            ctl.paused.clear()
        else:
            ctl.paused.set()
        ctl.wake.set()
        icon.icon = _tray_image(not ctl.paused.is_set())

    def quit_app(icon, _item):
        ctl.stop.set()
        ctl.wake.set()
        worker.join(timeout=5)
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(lambda _: f"สถานะ: {ctl.status}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(lambda _: "▶ เริ่มแสดงสถานะ" if ctl.paused.is_set() else "⏸ หยุดแสดงสถานะ", toggle),
        pystray.MenuItem("แก้ไข config.json", lambda *_: _open(CONFIG_PATH)),
        pystray.MenuItem("เปิดไฟล์ log", lambda *_: _open(LOG_PATH)),
        pystray.MenuItem("เปิดโฟลเดอร์โปรแกรม", lambda *_: _open(BASE_DIR)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(f"เวอร์ชัน {APP_VERSION}", None, enabled=False),
        pystray.MenuItem("ออกจากโปรแกรม", quit_app),
    )
    icon = pystray.Icon("discord-rpc", _tray_image(True), "Discord Rich Presence", menu)
    icon.run()  # block จนกด "ออก"


def main() -> None:
    setup_logging(verbose="--verbose" in sys.argv or "-v" in sys.argv)
    if not IS_WINDOWS:
        log.error("This program requires Windows (uses Discord IPC + Windows media APIs).")
        return
    ctl = Controller()
    try:
        if HAS_TRAY and "--no-tray" not in sys.argv:
            run_with_tray(ctl)
        else:
            run(ctl)
    except KeyboardInterrupt:
        ctl.stop.set()
        log.info("stopped by user")


if __name__ == "__main__":
    main()
