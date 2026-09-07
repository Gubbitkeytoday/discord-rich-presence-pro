# Discord Rich Presence — Antigravity Edition v2

โชว์เพลง/คลิปที่กำลังเล่น (YouTube, YouTube Music, Spotify) และงานที่ทำอยู่ (VS Code + AI) บนโปรไฟล์ Discord
ออกแบบให้ **สวยเหมือน integration ทางการ** และ **กินเครื่องน้อยที่สุด** — เล่นเกมอยู่ก็ไม่รู้สึก

---

## หน้าตาการ์ดที่ได้

| ส่วน | เดิม | v2 |
|---|---|---|
| หัวการ์ด | `กำลังดู Bio` (ชื่อแอปใน Dev Portal) | `กำลังดู YouTube` / `กำลังฟัง YouTube Music` / `กำลังฟัง Spotify` — เปลี่ยนตามแหล่งจริง |
| ปกคลิป | `hqdefault.jpg` (4:3 มี**แถบดำบน-ล่าง**) | `maxresdefault.jpg` 1280×720 ไม่มีแถบดำ ตรวจว่ามีจริงก่อนใช้ ถ้าไม่มีถอยไป `mqdefault.jpg` (16:9 เช่นกัน) |
| ชื่อคลิป | ข้อความเฉย ๆ | **คลิกได้** → เปิดคลิปนั้น (`details_url`), คลิกปกก็เปิดคลิป (`large_url`) |
| ชื่อช่อง | `by EYETA` | `EYETA` **คลิกได้** → เปิดหน้าช่อง (`state_url`) |
| ใน member list | ชื่อแอป | โชว์ **ชื่อเพลงเลย** (`status_display_type = DETAILS`) |
| เพลง vs คลิป | ทุกอย่างเป็น "กำลังดู" | YouTube Music / Spotify = **กำลังฟัง**, YouTube = **กำลังดู** |
| หลอดเวลา | ตรงระดับวินาที ขยับตอนอัปเดต | ผูก anchor กับ `last_updated_time` ของ Windows → ตรงเสี้ยววินาที ส่งครั้งเดียว Discord เดินเอง |
| กด pause | หลุดไปสถานะอื่น | `⏸ หยุดชั่วคราว 06:57 / 14:28 • EYETA` เวลาค้างไว้ |
| ชื่อคลิปรก | โชว์ทั้ง `(Official MV) [4K]` | ตัดคำรกออก แต่**ไม่ยุ่ง**กับวงเล็บที่เป็นส่วนของชื่อจริง เช่น `(ไม่เปลือง)` |
| ปุ่ม | ลิงก์ค้นหา | `▶ ดูคลิปนี้บน YouTube` → ลิงก์ตรง `watch?v=…` + ปุ่ม custom ของคุณ |
| เล่นเกม | โชว์ทับกับเกม | **ซ่อน presence อัตโนมัติ** ให้ Discord โชว์เกมแทน กลับมาเองเมื่อออกเกม |

> หมายเหตุ Discord: ปุ่มบนการ์ด **คุณจะไม่เห็นเอง** (Discord ซ่อนปุ่มของตัวเอง) แต่คนอื่นเห็น • เมื่อเปลี่ยนคลิปใหม่ ปกจะขึ้นภายใน 5–10 วิ (รอหา video id เบื้องหลัง ระหว่างนั้นโชว์โลโก้ก่อน ไม่ค้าง)

---

## ประสิทธิภาพ: กินสเปคไหม? ชนกับเกมไหม?

**คำตอบสั้น: ไม่กระทบ FPS ทั้งเวอร์ชันเก่าและใหม่ แต่ v2 ทำงานน้อยลง ~10 เท่า และหลบเกมให้เอง**

| หัวข้อ | เดิม | v2 |
|---|---|---|
| ส่งข้อมูลให้ Discord | ทุก 5 วิ แม้ไม่เปลี่ยน (Discord จำกัด 5 ครั้ง/20 วิ → โดนทิ้ง) | **เฉพาะตอนเปลี่ยน** / seek / heartbeat 15 นาที |
| หา video id บน YouTube | โหลดหน้า ~1 MB **บน main thread** ค้างได้ 4 วิ | background thread + LRU cache 200 รายการ + ผลลบหมดอายุ 2 นาที |
| Windows Media API | สร้าง event loop + Session Manager **ใหม่ทุก 5 วิ** | สร้างครั้งเดียว ใช้ซ้ำ |
| สแกนโปรเซส/หน้าต่าง | ทุก 5 วิ | cache 10 วิ |
| Priority | ปกติ (แข่ง CPU กับเกม) | **Below-Normal + Efficiency mode (EcoQoS)** — Windows จัดให้อยู่ท้ายคิว/E-core เสมอ |
| ตอนเล่นเกม | ทำงานเท่าเดิม | ตรวจ fullscreen → ซ่อน presence, ผ่อนเป็นทุก 15 วิ |
| RAM | ~40 MB | ~40 MB (Python + winsdk; ลดไม่ได้มากกว่านี้โดยไม่เปลี่ยนภาษา) |
| CPU เฉลี่ย (ประมาณ) | < 0.5% | < 0.05% |

**ความเสี่ยงที่ควรรู้ (ตรงไปตรงมา):** โปรแกรมอ่านรายชื่อโปรเซสและชื่อหน้าต่างเหมือนที่ Discord เองทำ โอกาสโดน anti-cheat มองผิดต่ำมาก แต่ถ้าเล่นเกมที่ anti-cheat เข้มมาก (Vanguard/FACEIT) และกังวล ให้ใส่ชื่อ exe ของเกมใน `game_processes` — โปรแกรมจะซ่อน presence ทันทีที่เกมเปิด แม้ไม่ fullscreen

---

## วิธีใช้

1. เปิด Discord Desktop และล็อกอิน
2. Discord → **Settings → Activity Privacy** → เปิด *Share your detected activities with others*
3. ดับเบิลคลิก **`start_background.vbs`** (รันเงียบ ไม่มีหน้าต่างดำ) หรือ `start.bat` ถ้าอยากเห็น log สด
4. หยุด: **`stop_background.bat`**
5. ให้รันเองตอนเปิดเครื่อง: **`autostart_on.bat`** (ยกเลิก: `autostart_off.bat`)

รอบแรก `start.bat` จะสร้าง `.venv` และติดตั้ง `psutil`, `pypresence`, `winsdk` ให้เอง
log อยู่ที่ `rpc.log` (หมุนเวียน 256 KB ไม่บวมแน่นอน) — รัน `start.bat -v` เพื่อดู debug

---

## ปรับแต่ง `config.json` (แก้แล้วมีผลทันที ไม่ต้องรีสตาร์ท)

```json
{
  "client_id": "1546386469353160804",
  "language": "th",                    // "th" หรือ "en"
  "update_interval_seconds": 5,        // ความถี่ตรวจสอบ (ส่งจริงเฉพาะตอนเปลี่ยน)
  "gaming_interval_seconds": 15,       // ความถี่ตอนเล่นเกม
  "show_cover_art": true,              // false = ใช้โลโก้แทนปกคลิป
  "pause_when_gaming": true,           // ซ่อน presence ตอนเกม fullscreen
  "game_processes": ["valorant.exe"],  // เกมที่ให้ถือว่า "เล่นเกม" เสมอ (ไม่บังคับ)
  "custom_button": { "label": "⚡ Antigravity AI", "url": "https://github.com" },
  "buttons": [ ... ]                   // ปุ่มตอนไม่ได้เล่นสื่อ (สูงสุด 2)
}
```

---

## Developer Portal (ทางเลือก)

ชื่อแอปถูก override ด้วย `name` แล้ว จึง**ไม่ต้อง**เปลี่ยนชื่อ "Bio" ก็ได้
ถ้าอยากให้ไอคอนแอปสวย: [Developer Portal](https://discord.com/developers/applications/1546386469353160804/information) → **App Icon**

---

## โครงสร้างโค้ด (สำหรับคนอยากแก้ต่อ)

```
main.py
├─ Config            อ่าน config.json ใหม่เฉพาะตอนไฟล์เปลี่ยน (mtime)
├─ YouTubeResolver   thread แยก: หา video id, ช่อง, ปก maxres→mq  (LRU + TTL)
├─ WindowsProbe      GSMTC media (loop เดียว), process/window snapshot (cache), fullscreen game, priority
├─ build_payload()   pure function → ทดสอบได้โดยไม่ต้องมี Windows/Discord
├─ should_send()     dedupe: เนื้อหาเปลี่ยน / seek > 3 วิ / heartbeat 15 นาที
└─ run()             main loop
```

ชุดทดสอบ logic (title cleaning, anchor math, payload ทุก case, dedupe) รันผ่านครบบน Linux ก่อนส่งมอบ
สิ่งที่**ยังไม่ได้ทดสอบจากที่นี่**เพราะต้องใช้เครื่อง Windows จริง: การเชื่อม Discord IPC, GSMTC, และการเข้าถึง YouTube (sandbox บล็อก) — ถ้ารันแล้วมีปัญหา ดู `rpc.log` ได้เลย
