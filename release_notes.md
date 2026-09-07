# ⚡ Discord Rich Presence Pro — v2.2.0 Official Release

🎉 ยินดีต้อนรับสู่ **Discord Rich Presence Pro v2.2.0** อัปเดตครั้งสำคัญด้านความแม่นยำและการสตรีมภาพหน้าปก รองรับ **Facebook Reels จริง (Real Cover Art)** และ **Smart Window-Media Content Isolation** แยกแยะเพลงและวิดีโออย่างเฉียบขาด!

> **ทุกคนสามารถดาวน์โหลดไฟล์ `.exe` สำเร็จรูปไปเปิดใช้งานได้ทันที 100% โดยไม่ต้องติดตั้ง Python หรือโปรแกรมเสริมใดๆ ทั้งสิ้น!**

---

## 📦 ลิงก์ดาวน์โหลด (Download Assets v2.2.0)

* **[ดาวน์โหลดแบบไฟล์ ZIP แนะนำ]**: [`DiscordRichPresence-windows-x64.zip`](https://github.com/Gubbitkeytoday/discord-rich-presence-pro/releases/download/v2.2.0/DiscordRichPresence-windows-x64.zip) *(มีทั้ง .exe และ config.json พร้อมใช้งาน)*
* **[ดาวน์โหลดเฉพาะตัว .exe]**: [`DiscordRichPresence.exe`](https://github.com/Gubbitkeytoday/discord-rich-presence-pro/releases/download/v2.2.0/DiscordRichPresence.exe)

---

## 🚀 วิธีใช้งานใน 3 ขั้นตอน (สำหรับทุกคน)

1. ดาวน์โหลดไฟล์ **`DiscordRichPresence-windows-x64.zip`** ด้านบน
2. แตกไฟล์ (Extract ZIP) ไว้ที่โฟลเดอร์ใดก็ได้บนคอมพิวเตอร์ของคุณ
3. ดับเบิลคลิกเปิด **`DiscordRichPresence.exe`** ได้ทันที!
   * *จะมีไอคอนโผล่ขึ้นมาที่ System Tray (มุมขวาล่างของหน้าจอ ข้างนาฬิกา Windows) แสดงว่าโปรแกรมกำลังทำงานอยู่*
   * *คุณสามารถคลิกขวาที่ไอคอนเพื่อ หยุดชั่วคราว, แก้ไขการตั้งค่า หรือปิดโปรแกรมได้ตลอดเวลา*

---

## 🌟 อะไรใหม่ในเวอร์ชัน 2.2.0 (What's New in v2.2.0)

### 1. 🎯 Smart Background Tab Isolation (หมดปัญหาแท็บเบื้องหลังแย่งสถานะ)
- **Content Matching Engine**: แก้ไขปัญหาเมื่อผู้ใช้เปิดแท็บ Facebook ทิ้งไว้ในพื้นหลัง (เช่น ฟีดข่าว) แต่เปิดฟังเพลงหรือดูคลิปบน YouTube ในอีกแท็บหนึ่ง ระบบรุ่นก่อนหน้าอาจเข้าใจผิดและนำชื่อเพลง YouTube ไปแสดงผลเป็นการ์ด Facebook
- **1-to-1 Window Title Verification**: ระบบจะตรวจสอบเนื้อหาและชื่อคลิปเทียบกับชื่อแท็บเบราว์เซอร์อย่างเข้มงวด หากเปิดเพลงบน YouTube ระบบจะล็อคสถานะเข้ากับ YouTube 100% และไม่ถูกแท็บ Facebook รบกวนอีกต่อไป

### 2. 📱 Real Facebook Reels & Watch Cover Art (ดึงภาพหน้าปกคลิปจริง)
- **GSMTC Native Stream Extraction**: เชื่อมโยงเข้ากับ `IRandomAccessStreamReference` ของ Windows Kernel เพื่อดึงไบต์ภาพโปสเตอร์ของคลิป Reel จากหน่วยความจำของ Chrome/Edge โดยตรง (<3ms)
- **Non-blocking CDN Sync**: ระบบประมวลผลและอัปโหลดภาพขึ้น CDN ความเร็วสูงในเธรดเบื้องหลัง (Background Daemon Thread) ทำให้การ์ดบน Discord โชว์ภาพหน้าปกคลิป Reels แท้ๆ ชัดเจน สวยงาม โดยไม่ทำให้ลูปหลักกระตุก
- **In-Memory LRU Caching**: จัดเก็บ URL หน้าปกคลิปไว้ในแคช ทำให้การเลื่อนดูคลิปถัดไปหรือเล่นซ้ำประหยัดเน็ตและแสดงผลทันทีแบบ 0-latency
- **Reels Branding & Button**: แยกการ์ด Facebook Reels ออกมาชัดเจน แสดงข้อความ `[ชื่อครีเอเตอร์] • Facebook Reels` และปุ่ม Interactive `▶ Facebook Reels`

### 3. 🎬 Streaming & Creative Ecosystem
- **YouTube & YouTube Music**: ซิงค์ภาพหน้าปกคลิปจริงระดับ MaxRes/HQ, หลอดเวลาสด Sub-Second Precision
- **Facebook Watch**: แสดงวิดีโอยาวพร้อมปกจริงและปุ่ม `▶ Facebook Watch`
- **Facebook Messenger & News Feed**: แสดงสถานะการสนทนาข้อความและท่องฟีดแยกจากกัน
- **Netflix, Twitch, TikTok, Spotify, SoundCloud**: ครบครันทุกความบันเทิง
- **VS Code, Figma, Blender, GitHub, Notion, ChatGPT, Claude AI, Postman**: ตรวจจับอัตโนมัติสำหรับสาย Dev & Creator

### 4. ⚡ ประสิทธิภาพระดับ Enterprise
- **100% Logic Test Coverage**: ผ่านการทดสอบ Unit Tests ทุกเงื่อนไข ป้องกัน Regression 100%
- **Zero CPU Spikes**: รันที่สิทธิ Below-Normal Priority + Windows Efficiency Mode ใช้ CPU แทบเป็น 0%
- **Automatic Game Suppression**: ซ่อนสถานะทันทีเมื่อเปิดเกมเต็มจอ เพื่อไม่รบกวน FPS ของเกม
