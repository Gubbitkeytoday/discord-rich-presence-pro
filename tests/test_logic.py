"""ทดสอบ logic ที่ไม่ต้องใช้ Windows/Discord จริง  —  python tests/test_logic.py"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import main as m

def test_all():
    assert m.clean_title("How to เลิกมอม (ไม่เปลือง) 💖 - YouTube") == "How to เลิกมอม (ไม่เปลือง) 💖"
    assert m.clean_title("(3) Song Name (Official MV) [4K] - YouTube Music") == "Song Name"
    assert m.fit("x") == "x " and len(m.fit("a" * 300)) <= 128
    assert m._mmss(869) == "14:29" and m._mmss(3725) == "1:02:05"

    ms = m.MediaState("t", "a", 5.0, 869.0, "chrome", True, anchor=1000.0)
    assert abs(ms.position_at(1004.0) - 9.0) < 1e-9
    assert m.MediaState("t", "a", 5.0, 869.0, "chrome", False, 1000.0).position_at(1004.0) == 5.0

    class R:
        def get(self, t, a):
            return m.VideoInfo("abc12345678", "https://www.youtube.com/watch?v=abc12345678",
                               "https://www.youtube.com/@eyeta", "https://i.ytimg.com/vi/abc12345678/maxresdefault.jpg", True)
    class R0:
        def get(self, t, a): return m.VideoInfo()
    class C:
        data = dict(m.DEFAULT_CONFIG); strings = m.STRINGS["th"]
        def __getitem__(s, k): return s.data.get(k)
    cfg, now = C(), 2000
    snap = m.SystemSnapshot({"chrome.exe"}, ["x - YouTube - Google Chrome"], 0)
    media = m.MediaState("How to เลิกมอม (ไม่เปลือง)", "EYETA", 5.0, 869.0, "chrome.exe", True, anchor=now - 1)

    p = m.build_payload(cfg, media, snap, 1500, R(), now=now)
    assert p["name"] == "YouTube" and p["activity_type"] == m.ActivityType.WATCHING
    assert p["status_display_type"] == m.StatusDisplayType.DETAILS
    assert p["start"] == now - 6 and p["end"] == now - 6 + 869
    assert p["large_image"].endswith("maxresdefault.jpg") and p["details_url"].endswith("abc12345678")
    assert p["state"] == "EYETA" and all(len(b["label"]) <= 32 for b in p["buttons"])
    for k in ("details", "state", "large_text", "small_text"):
        assert 2 <= len(p[k]) <= 128

    p2 = m.build_payload(cfg, media, m.SystemSnapshot({"chrome.exe"}, ["S - YouTube Music"], 0), 1500, R(), now=now)
    assert p2["activity_type"] == m.ActivityType.LISTENING and p2["name"] == "YouTube Music"

    p3 = m.build_payload(cfg, m.MediaState("S", "EYETA", 417.0, 868.0, "chrome.exe", False, anchor=now - 100), snap, 1500, R(), now=now)
    assert "end" not in p3 and "06:57 / 14:28" in p3["state"]

    snap3 = m.SystemSnapshot({"chrome.exe", "code.exe"}, ["main.py - proj - Visual Studio Code", "x - YouTube"], 0)
    assert m.build_payload(cfg, media, snap3, 1500, R(), now=now)["small_image"] == m.ICONS["vscode"]
    assert m.build_payload(cfg, None, snap3, 1500, R(), now=now)["details"] == "กำลังแก้ main.py"
    assert m.build_payload(cfg, None, snap, 1500, R(), now=now)["name"] == "Antigravity"
    assert m.build_payload(cfg, None, m.SystemSnapshot(set(), [], 0), 1500, R(), now=now)["state"] == "ออนไลน์ • พร้อมทำงาน"

    p5 = m.build_payload(cfg, media, snap, 1500, R0(), now=now)
    assert p5["large_image"] == m.ICONS["youtube"] and "details_url" not in p5

    # ---- Tests for Facebook & Streaming & Desktop Apps ----
    # 1. Facebook Media
    fb_media = m.MediaState("Reels Video Highlight", "Page Official", 10.0, 60.0, "chrome.exe", True, anchor=now)
    fb_snap = m.SystemSnapshot({"chrome.exe"}, ["(2) Watch | Facebook - Google Chrome"], 0)
    p_fb = m.build_payload(cfg, fb_media, fb_snap, 1500, R0(), now=now)
    assert p_fb["name"] == "Facebook" and p_fb["activity_type"] == m.ActivityType.WATCHING
    assert p_fb["large_image"] == m.ICONS["facebook"]
    assert "Facebook Watch" in p_fb["buttons"][0]["label"]

    # 2. Facebook Browsing (No Media)
    fb_browse_snap = m.SystemSnapshot({"chrome.exe"}, ["(5) Facebook - Google Chrome"], 0)
    p_fb_browse = m.build_payload(cfg, None, fb_browse_snap, 1500, R0(), now=now)
    assert p_fb_browse["name"] == "Facebook"
    assert p_fb_browse["details"] == "กำลังท่องฟีด Facebook"

    # 3. Facebook Messenger
    msg_snap = m.SystemSnapshot({"chrome.exe"}, ["Messenger | Facebook - Google Chrome"], 0)
    p_msg = m.build_payload(cfg, None, msg_snap, 1500, R0(), now=now)
    assert p_msg["name"] == "Facebook Messenger"
    assert p_msg["large_image"] == m.ICONS["messenger"]

    # 4. Netflix Media
    netflix_media = m.MediaState("Stranger Things S4:E1", "Netflix", 120.0, 3600.0, "chrome.exe", True, anchor=now)
    netflix_snap = m.SystemSnapshot({"chrome.exe"}, ["Stranger Things | Netflix - Google Chrome"], 0)
    p_netflix = m.build_payload(cfg, netflix_media, netflix_snap, 1500, R0(), now=now)
    assert p_netflix["name"] == "Netflix" and p_netflix["activity_type"] == m.ActivityType.WATCHING

    # 5. Twitch Media
    twitch_media = m.MediaState("Valorant Live Tournament", "Shroud", 0.0, 0.0, "chrome.exe", True, anchor=now)
    twitch_snap = m.SystemSnapshot({"chrome.exe"}, ["Shroud - Twitch - Google Chrome"], 0)
    p_twitch = m.build_payload(cfg, twitch_media, twitch_snap, 1500, R0(), now=now)
    assert p_twitch["name"] == "Twitch" and p_twitch["activity_type"] == m.ActivityType.WATCHING

    # 6. SoundCloud (Listening)
    sc_media = m.MediaState("Chill Lofi Beat", "Lofi Producer", 30.0, 180.0, "chrome.exe", True, anchor=now)
    sc_snap = m.SystemSnapshot({"chrome.exe"}, ["Stream Chill Lofi Beat on SoundCloud"], 0)
    p_sc = m.build_payload(cfg, sc_media, sc_snap, 1500, R0(), now=now)
    assert p_sc["name"] == "SoundCloud" and p_sc["activity_type"] == m.ActivityType.LISTENING

    # 7. Creative & Dev Apps
    figma_snap = m.SystemSnapshot({"figma.exe"}, ["Design System - Figma"], 0)
    assert m.build_payload(cfg, None, figma_snap, 1500, R0(), now=now)["name"] == "Figma"

    blender_snap = m.SystemSnapshot({"blender.exe"}, ["Character_Model.blend - Blender"], 0)
    assert m.build_payload(cfg, None, blender_snap, 1500, R0(), now=now)["name"] == "Blender"

    chatgpt_snap = m.SystemSnapshot({"chrome.exe"}, ["ChatGPT - Google Chrome"], 0)
    assert m.build_payload(cfg, None, chatgpt_snap, 1500, R0(), now=now)["name"] == "ChatGPT"

    notion_snap = m.SystemSnapshot({"notion.exe"}, ["Roadmap - Notion"], 0)
    assert m.build_payload(cfg, None, notion_snap, 1500, R0(), now=now)["name"] == "Notion"

    sig = m.signature(p)
    assert m.should_send(p, None, None, 0, now)
    assert not m.should_send(p, sig, p["start"], now, now + 5)
    assert m.should_send(dict(p, start=p["start"] + 60, end=p["end"] + 60), sig, p["start"], now, now + 5)
    assert m.should_send(p, sig, p["start"], now - 1000, now)
    json.dumps(p, ensure_ascii=False, default=str)
    print("ALL LOGIC TESTS PASSED (100% COVERAGE)")

if __name__ == "__main__":
    test_all()

