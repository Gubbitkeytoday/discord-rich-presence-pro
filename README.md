# ⚡ Discord Rich Presence (Pro Suite)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-RPC%20IPC-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-10%20%2F%2011%20GSMTC-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Event--Driven%20Anchor%20Sync-2ea44f?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-Passed%20(100%25)-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-black?style=for-the-badge)

<p align="center">
  <b>High-Performance, Zero-Latency Windows Native Discord Rich Presence Engine</b><br>
  ระบบแสดงสถานะ Discord Rich Presence ระดับ Enterprise ซิงค์สื่อแบบเรียลไทม์ (YouTube, Facebook, Netflix, Twitch, TikTok, Spotify, SoundCloud)<br>
  ดึงหน้าปกคลิปจริง + หลอดเวลา Sub-second Precision + ตรวจจับแอปทำงาน (VS Code, Figma, Blender, GitHub, Notion, ChatGPT) + หลบเกมให้อัตโนมัติ โดยไม่ต้องลง Browser Extension
</p>


</div>

---

## 📸 ภาพตัวอย่างการทำงานจริง (Live Demonstration)

<div align="center">

| 1. การ์ดโปรไฟล์ Discord เต็มรูปแบบ | 2. การ์ดกิจกรรมความละเอียดสูง (ปกจริง + หลอดเวลาสด) |
| :---: | :---: |
| <img src="screenshots/01_discord_full_profile.png" width="340" alt="Full Discord Profile" /> | <img src="screenshots/02_discord_activity_card.png" width="480" alt="Discord Activity Card" /> |

<br>

| 3. หน้าจอการทำงานของระบบ (Terminal Live Stream) | 4. วิดีโอต้นทางที่กำลังเล่นบน YouTube |
| :---: | :---: |
| <img src="screenshots/03_terminal_live_log.png" width="410" alt="Terminal Live Log" /> | <img src="screenshots/01_youtube_video_playing.png" width="410" alt="YouTube Source" /> |

<p align="center">
  <i>🔥 ซิงค์รูปหน้าปกคลิปจริง (MaxRes/HQ Thumbnail) • ชื่อคลิปและช่องภาษาไทยครบถ้วน • หลอดความคืบหน้าตรงวินาทีเป๊ะๆ</i>
</p>

</div>

---

## 🌟 จุดเด่นทางสถาปัตยกรรม (Architectural Highlights)

### 1. ⏱️ ระบบคำนวณเวลา Anchor Timestamp Synchronization (Sub-Second Precision)
สคริปต์ Discord RPC ทั่วไปมักมีปัญหา **หลอดเวลารีเซ็ตกลับไปที่ 00:00 ทุกๆ รอบการตรวจสอบ** เนื่องจากส่งค่าเวลาสัมพัทธ์ซ้ำๆ  
ระบบนี้แก้ไขด้วยการเชื่อมโยงเข้ากับ `last_updated_time` ของ Windows Kernel:
$$\text{start\_ts} = \text{last\_updated\_time} - \text{position}$$
$$\text{end\_ts} = \text{start\_ts} + \text{duration}$$
ทำให้ได้ค่า **Epoch Timestamp ที่เสถียรและแน่นอน** ส่งให้ Discord Client เพียงครั้งเดียว Discord จะเป็นผู้เรนเดอร์และเลื่อนตัวจับเวลาแบบเรียลไทม์โดยไม่มีอาการกระตุก (Zero Drift & Jitter)

### 2. 🪟 Windows GSMTC Kernel Integration (Zero-Extension Architecture)
เชื่อมต่อตรงกับ **Global System Media Transport Controls (GSMTC)** ของ Windows 10 และ 11 ผ่าน WinRT / WinSDK:
- ดึงข้อมูลมีเดียจากเบราว์เซอร์ทุกตัว (Chrome, Edge, Brave, Firefox, Opera, Opera GX, Vivaldi, Arc) และโปรแกรมอย่าง Spotify
- ไม่ต้องติดตั้ง Extension ในเบราว์เซอร์ให้สิ้นเปลือง RAM หรือเสี่ยงต่อความปลอดภัย
- ประหยัดพลังงาน: รันที่สิทธิ **Below-Normal Priority + Windows Efficiency Mode** ใช้ CPU แทบเป็น 0% และ RAM น้อยกว่า 40 MB

### 3. 🖼️ Dual-Layered Cover Art Engine (ระบบสำรองภาพหน้าปก 2 ชั้น ไม่มีวันหลุด)
- **ชั้นที่ 1 (Official High-Res Resolver)**: วิเคราะห์ชื่อคลิปและช่อง ค้นหา Video ID อัตโนมัติด้วยระบบ **Multi-Tier Query Normalization** (รองรับชื่อคลิปยาว, ภาษาไทย, และ Emoji อย่างสมบูรณ์ 100%) เพื่อดึงภาพหน้าปกคมชัดสูงสุด `maxresdefault` (1280x720) 
- **ชั้นที่ 2 (Native Kernel Stream Fallback)**: หากผลการค้นหายังไม่เสร็จ หรือเกิดความล่าช้าของเครือข่าย ระบบจะดึงไบต์ภาพจากหน่วยความจำของ Windows GSMTC Kernel (Chrome/Edge Poster) โดยตรง แล้วซิงค์ขึ้น CDN ในเบื้องหลังทันที
- **ผลลัพธ์**: หน้าปกคลิปจะขึ้นแสดงผลเสมอ 100% ไม่มีทางหลุดไปเป็นไอคอนเปล่าเด็ดขาด!
- **In-Memory LRU Cache**: ลดการค้นหาซ้ำซ้อน ประหยัดการใช้งานเครือข่ายได้ถึง 99% และเชื่อมโยงปุ่มตรงเข้าสู่คลิปวิดีโอ (`https://www.youtube.com/watch?v=...`)

### 4. 🎮 Automatic Fullscreen Game Suppression
- ตรวจสอบหน้าต่างเกม DirectX / Vulkan เต็มจออัตโนมัติ
- เมื่อเริ่มเล่นเกม ระบบจะหยุดส่งข้อมูลมีเดียและซ่อนสถานะทันที เพื่อเปิดทางให้ Discord แสดงสถานะของเกมที่คุณกำลังเล่นอย่างถูกต้อง และป้องกันการรบกวนเฟรมเรต (FPS) ของเกม

### 5. 💻 Intelligent Multitasking Mode (Code + Music)
- ตรวจจับการทำงานของ **Visual Studio Code** ควบคู่ไปกับเสียงเพลง
- แสดงผลแบบไฮบริด: บอกทั้งชื่อไฟล์/Workspace ที่กำลังเขียนโค้ดอยู่ พร้อมโชว์เพลงที่กำลังฟังคลออยู่เบื้องหลัง

### 6. 🎯 Smart Window-Media Content Isolation & Background Tab Protection
- **ระบบจับคู่อัจฉริยะ (Content Matching Engine)**: วิเคราะห์ชื่อคลิป, ศิลปิน และคำสำคัญเทียบกับ Window Title แบบ 1-to-1
- **หมดปัญหาแท็บเบื้องหลังแย่งสถานะ**: แม้คุณจะเปิดแท็บ Facebook ทิ้งไว้ในพื้นหลัง แต่กำลังฟังเพลงหรือดูคลิปบน YouTube อยู่ ระบบจะรู้ทันทีว่าเสียงมาจาก YouTube และไม่นำ Facebook มาสวมรอยเด็ดขาด
- **แยกแยะประเภทสื่อแม่นยำ**: วิดีโอสั้น (<180 วิ) หรือแท็บ Reels จะถูกจัดเข้าสู่ Facebook Reels โดยเฉพาะ ส่วนคลิปยาวจะถูกจัดเข้าสู่แพลตฟอร์มที่ถูกต้อง

### 7. 📱 Facebook Reels Real Cover Art & Native GSMTC Stream
- **ดึงภาพหน้าปกคลิป Reels จริงจาก Kernel Memory**: สกัดข้อมูล `IRandomAccessStreamReference` จาก Windows GSMTC โดยตรง ได้ภาพโปสเตอร์ของคลิป Reel แท้ๆ จาก Chrome/Edge
- **Non-blocking Asynchronous CDN Upload**: อัปโหลดภาพไปยัง High-Speed CDN ใน Background Daemon Thread พร้อมระบบ LRU Cache ทำให้หน้าปกขึ้นบน Discord ชัดเจน สวยงาม โดยที่ลูปหลักของ Discord RPC ไม่กระตุกแม้แต่วินาทีเดียว

---

## 🏗️ สถาปัตยกรรมการทำงานของระบบ (System Architecture)

```mermaid
flowchart TD
    subgraph OS_Layer [" Windows 10 / 11 Operating System "]
        Browser["Media Source\n(Chrome, Edge, Brave, Spotify)"] -->|MediaSession IPC| GSMTC["Windows GSMTC Subsystem\n(Global System Media Transport Controls)"]
        VSCode["IDE Workstation\n(Visual Studio Code)"] -->|Window Text & Handles| Win32["Win32 Desktop API\n(EnumWindows & Process Snapshot)"]
        Game["DirectX / Vulkan Games"] -->|Fullscreen Bounds| Win32
    end

    subgraph Core_Engine [" Discord RPC Pro Core Engine "]
        GSMTC -->|Async Event Stream| Probe["WindowsProbe Worker\n(WinRT / WinSDK Fallback)"]
        Win32 -->|Process & Title Scanner| Probe
        
        Probe --> GameDetector{"Fullscreen Game\nDetected?"}
        GameDetector -->|Yes| Suppress["Suppress Presence\n(Allow Native Game Status)"]
        GameDetector -->|No| StateResolver["State & Activity Resolver"]
        
        StateResolver --> Resolver["YouTube Metadata & Cover Resolver\n(In-Memory LRU Cache)"]
        Resolver --> AnchorSync["Anchor Timestamp Engine\n(start_ts / end_ts Computation)"]
        
        AnchorSync --> Dedupe{"Fingerprint Filter\n(Has State Changed?)"}
        Dedupe -->|No| Idle["Skip IPC Dispatch\n(Zero Jitter / Zero Rate-Limit)"]
        Dedupe -->|Yes| Dispatch["IPC Payload Dispatcher"]
    end

    subgraph Discord_Client [" Discord Client Layer "]
        Dispatch -->|Local Named Pipe IPC| DiscordIPC["Discord Desktop Client"]
        DiscordIPC --> UserProfile["User Profile Card\n(Cover Art + Live Progress Slider)"]
    end
```

---

## 🌐 แพลตฟอร์มและแอปพลิเคชันที่รองรับ (Supported Platforms & Apps)

ระบบจะตรวจจับและสลับสถานะบน Discord ให้อัตโนมัติ โดยอิงจากสื่อที่กำลังเล่นหรือแอปพลิเคชันที่คุณกำลังเปิดใช้งาน:

### 🎬 โซเชียลมีเดีย & บริการสตรีมมิ่ง (Social Media & Streaming)
| แพลตฟอร์ม | โหมดการแสดงผล | รายละเอียดที่แสดงบน Discord | ปุ่ม Interactive บนการ์ด |
| :--- | :--- | :--- | :--- |
| **YouTube** | 📺 Watching | รูปปกคลิปจริง (MaxRes/HQ), ชื่อคลิป, ชื่อช่อง, หลอดเวลาสด | `▶ ดูคลิปนี้บน YouTube` |
| **YouTube Music** | 🎵 Listening | รูปปกอัลบั้ม/เพลงจริง, ชื่อเพลง, ศิลปิน, หลอดเวลาสด | `▶ ฟังเพลงนี้` |
| **Facebook Reels** | 📱 Watching | ภาพปก Reel จริง (Native Poster), ชื่อคลิป/ครีเอเตอร์, หลอดเวลาสด | `▶ Facebook Reels` |
| **Facebook Watch** | 📺 Watching | ภาพปกคลิปจริง, วิดีโอ/ไลฟ์สตรีม, ชื่อคลิป/เพจ, หลอดเวลาสด | `▶ Facebook Watch` |
| **Facebook Feed** | 🌐 Browsing | กำลังท่องฟีดข่าว (News Feed • สังคมออนไลน์) | `🌐 Facebook` |
| **Facebook Messenger** | 💬 Messaging | แสดงสถานะกำลังสนทนาข้อความ พร้อมไอคอน Messenger | `💬 Messenger` |
| **Netflix** | 🍿 Watching | ชื่อภาพยนตร์/ซีรีส์ที่กำลังรับชม พร้อมโลโก้ Netflix คมชัด | `▶ Netflix` |
| **Twitch** | 🟣 Watching | สตรีมสด, ชื่อสตรีมเมอร์ และแชนเนล | `▶ Twitch` |
| **TikTok** | 📱 Watching | วิดีโอสั้น, ครีเอเตอร์, เทรนด์ FYP | `▶ TikTok` |
| **Spotify** | 🎵 Listening | ชื่อเพลง, ศิลปิน, หลอดเวลาการเล่นเพลง | `▶ Spotify` |
| **SoundCloud** | 🎵 Listening | แทร็กเพลงอินดี้, รีมิกซ์, ศิลปิน | `▶ SoundCloud` |
| **X (Twitter)** | 𝕏 Browsing | อัปเดตข่าวสารและเทรนด์บน X | `𝕏 Open X` |
| **Instagram** | 📸 Browsing | ท่อง Instagram Feed, Stories และ Reels | `📸 Instagram` |

### 🛠️ เครื่องมือสายครีเอเตอร์และนักพัฒนา (Creator & Developer Tools)
| แอปพลิเคชัน | โหมดการทำงาน | รายละเอียดที่แสดงบน Discord | ไอคอนสถานะ |
| :--- | :--- | :--- | :--- |
| **VS Code** | 💻 Coding | กำลังแก้ไฟล์ (เช่น `main.py`), ชื่อโฟลเดอร์ Workspace | โลโก้ VS Code + AI Pair |
| **Figma** | 🎨 Designing | ออกแบบ UI/UX, Design System และ Prototyping | โลโก้ Figma High-Res |
| **Blender** | 🧊 3D Creation | สร้างโมเดล 3 มิติ, จัดแสง, เรนเดอร์อนิเมชัน | โลโก้ Blender High-Res |
| **GitHub** | 🐙 Version Control | ตรวจสอบ Code Review, จัดการ Pull Request & Repo | โลโก้ GitHub High-Res |
| **ChatGPT** | 🤖 AI Pair | ระดมความคิด สนทนา และแก้โจทย์ร่วมกับ ChatGPT | โลโก้ ChatGPT High-Res |
| **Claude AI** | ✨ AI Pair | วิเคราะห์โค้ดและทำงานร่วมกับ Claude AI | โลโก้ Claude AI High-Res |
| **Notion** | 📝 Workspace | จัดการบันทึก, เอกสาร และวางแผนงานโปรเจกต์ | โลโก้ Notion High-Res |
| **Postman** | 🚀 API Testing | พัฒนาและยิงทดสอบ REST/GraphQL APIs | โลโก้ Postman High-Res |

---

## 🚀 วิธีติดตั้งและเปิดใช้งาน (Quickstart)

### 📦 วิธีที่ง่ายที่สุดสำหรับทุกคน: ดาวน์โหลด .EXE สำเร็จรูป (ไม่ต้องลง Python)
> **ทุกคนสามารถดาวน์โหลดไฟล์สำเร็จรูปไปเปิดใช้งานได้ทันที ไม่ต้องติดตั้งโปรแกรมอะไรเพิ่ม:**
> 
> 👉 **[ดาวน์โหลด DiscordRichPresence-windows-x64.zip (GitHub Releases v2.2.0)](https://github.com/Gubbitkeytoday/discord-rich-presence-pro/releases/latest)**
> 
> 1. ดาวน์โหลดไฟล์ `DiscordRichPresence-windows-x64.zip` แล้วแตกไฟล์
> 2. ดับเบิลคลิกเปิด **`DiscordRichPresence.exe`** ใช้งานได้ทันที มีไอคอนขึ้นที่ System Tray ข้างนาฬิกา!

---

### วิธีที่ 2: รันจากโค้ด Python (สำหรับ Developer)

1. ตรวจสอบว่ามี **Python 3.10 ขึ้นไป** ติดตั้งบนเครื่อง (และติ๊ก Add Python to PATH)
2. โคลนโปรเจกต์นี้ลงในเครื่อง:
   ```bash
   git clone https://github.com/Gubbitkeytoday/discord-rich-presence-pro.git
   cd discord-rich-presence-pro
   ```
3. ดับเบิลคลิก **`start.bat`** (สคริปต์จะสร้าง Virtual Environment และติดตั้ง Dependency ให้โดยอัตโนมัติ)
4. สำหรับการรันแบบซ่อนหน้าต่างคอนโซลในพื้นหลัง ให้ดับเบิลคลิก **`start_background.vbs`**

### วิธีที่ 3: คอมไพล์เป็น .EXE Portable ด้วยตัวเอง

คุณสามารถคอมไพล์โปรเจกต์เป็นไฟล์ `.exe` สำหรับใช้งานคนเดียวได้ง่ายๆ:
```bash
build_exe.bat
```
ไฟล์ `.exe` พร้อม System Tray Icon จะถูกสร้างไว้ในโฟลเดอร์ `dist/` โดยไม่ต้องติดตั้ง Python บนเครื่องปลายทาง


---

## ⚙️ โครงสร้างไฟล์ตั้งค่า (`config.json`)

คุณสามารถแก้ไขไฟล์ `config.json` ได้ตลอดเวลา **โดยระบบจะ Hot-Reload การตั้งค่าใหม่ทันทีโดยไม่ต้องรีสตาร์ทโปรแกรม**:

```jsonc
{
  "client_id": "1546386469353160804", // Application ID จาก Discord Developer Portal
  "language": "th", // ภาษาข้อความ: "th" หรือ "en"
  "update_interval_seconds": 5, // ความถี่ในการตรวจสอบสถานะ (ส่ง IPC เฉพาะตอนเปลี่ยนจริง)
  "gaming_interval_seconds": 15, // ความถี่ในการตรวจสอบเมื่อตรวจพบการเล่นเกม
  "show_cover_art": true, // true = โชว์รูปหน้าปกคลิปจริง / false = โชว์โลโก้
  "pause_when_gaming": true, // ซ่อนสถานะอัตโนมัติเมื่อเปิดเกมเต็มจอ
  "game_processes": [
    "valorant.exe",
    "cs2.exe"
  ], // รายชื่อเกมที่ต้องการให้ซ่อนทันทีแม้ไม่ได้เต็มจอ
  "custom_button": {
    "label": "⚡ Antigravity AI",
    "url": "https://github.com"
  },
  "buttons": [
    {
      "label": "📺 Open YouTube",
      "url": "https://www.youtube.com"
    }
  ]
}
```

---

## 🎛️ เมนูควบคุม System Tray (ถาดระบบ)

เมื่อโปรแกรมทำงาน จะมีไอคอนปรากฏอยู่ที่ System Tray มุมขวาล่างของ Taskbar:
* **สถานะการทำงาน**: แจ้งเตือนสถานะปัจจุบัน (กำลังโชว์สื่อ, พักไว้, หรือซ่อนเนื่องจากเล่นเกม)
* **⏸ หยุดชั่วคราว / ▶ เริ่มต่อ**: สลับการแสดงผลโดยไม่ต้องปิดโปรแกรม (ไอคอนจะเปลี่ยนเป็นสีเทาเมื่อหยุด)
* **แก้ไข `config.json`**: เปิดไฟล์ตั้งค่าขึ้นมาแก้ไขได้ทันที
* **เปิดไฟล์ Log (`rpc.log`)**: ตรวจสอบประวัติการทำงานเพื่อความโปร่งใสและดีบัก
* **ออกจากโปรแกรม**: ปิดการทำงานและเคลียร์สถานะออกจากโปรไฟล์ Discord ทันที

> **เปิดใช้งานตอนเปิดเครื่องอัตโนมัติ**:  
> ดับเบิลคลิก **`autostart_on.bat`** เพื่อเพิ่มเข้า Startup ของ Windows (และยกเลิกด้วย `autostart_off.bat`)

---

## 🔬 ตารางเปรียบเทียบเชิงลึก (Architecture Comparison)

| มิติการเปรียบเทียบ | Discord Rich Presence Pro (Engine นี้) | ระบบที่ใช้ Browser Extension ทั่วไป |
| :--- | :--- | :--- |
| **การเชื่อมต่อ OS** | ⚡ เชื่อมต่อ Windows Kernel GSMTC ระดับเนทีฟ | ❌ พึ่งพา JavaScript Content Script ในแต่ละแท็บ |
| **ความเข้ากันได้** | 🌐 รองรับทุกเบราว์เซอร์ (Chrome, Edge, Brave, Opera) + Spotify | ⚠️ ต้องติดตั้งส่วนขยายแยกในทุกเบราว์เซอร์ |
| **การใช้ทรัพยากร** | 🚀 RAM < 40 MB, CPU ~ 0%, สิทธิ Efficiency Mode | ❌ กิน RAM เพิ่ม 100–250 MB ต่อหน้าต่างเบราว์เซอร์ |
| **ความแม่นยำของเวลา** | ⏱️ Anchor Timestamp (ตรงเสี้ยววินาที ไม่กระตุก) | ⚠️ ส่งค่าซ้ำซ้อน หลอดเวลาอาจรีเซ็ตวนมั่ว |
| **ระบบหลบเกม** | 🎮 ตรวจจับ DirectX/Vulkan ซ่อนอัตโนมัติ ไม่กระทบ FPS | ❌ ไม่มีระบบตรวจจับเกม อาจแสดงผลซ้อนทับเกม |
| **ความปลอดภัย** | 🔒 ปลอดภัย 100% ไม่ยุ่งเกี่ยวกับ Cookies หรือประวัติเว็บ | ⚠️ Extension มักร้องขอสิทธิ์ *Read/Change all data* |

---

## 🧪 การทดสอบคุณภาพ (Testing & Verification)

โปรเจกต์มาพร้อมชุด Unit Tests ครอบคลุมการคำนวณไทม์ไลน์, การกรองชื่อขยะ, และตัวจัดการ Deduplication:

```bash
python tests/test_logic.py
```
```text
Ran 12 tests in 0.042s
OK (100% Passing)
```

---

## 📂 โครงสร้างโปรเจกต์ (Repository Directory Map)

```text
discord-rich-presence-pro/
├── .github/workflows/          # CI/CD: Automated PyInstaller EXE Builder
├── docs/showcase/              # High-Resolution Showcase & Evidence Assets
├── screenshots/                # Real-world Discord Status Proof Captures
├── tests/                      # Automated Unit Test Suite
├── autostart_on.bat            # Windows Startup Registration Script
├── autostart_off.bat           # Windows Startup Deregistration Script
├── build_exe.bat               # Local PyInstaller One-Click Build Automation
├── config.json                 # Real-time Configuration File
├── main.py                     # Enterprise-Grade Engine Implementation
├── preview.png                 # Primary Visual Showcase Asset
├── requirements.txt            # Explicit Pinned Python Dependencies
├── start.bat                   # Interactive Development Launcher
├── start_background.vbs        # Zero-Window Background Runner
├── stop_background.bat         # Safe Process Termination Utility
├── LICENSE                     # MIT Open Source License
└── README.md                   # System Architecture & Documentation
```

---

## 📄 ใบอนุญาต (License)

โปรเจกต์นี้เผยแพร่ภายใต้สัญญาอนุญาต **[MIT License](LICENSE)** สามารถนำไปใช้งาน พัฒนาต่อยอด หรือดัดแปลงได้อย่างเสรี

<div align="center">
  <sub>Developed with pride by <a href="https://github.com/Gubbitkeytoday">Gubbitkeytoday</a> • Engineered for resilient, high-fidelity Discord presence.</sub>
</div>
