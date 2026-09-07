# ⚡ Discord Rich Presence Pro — v2.1.0 Official Release

🎉 ยินดีต้อนรับสู่ **Discord Rich Presence Pro v2.1.0** อัปเดตครั้งใหญ่เพื่อรองรับ **Facebook Ecosystem** เต็มรูปแบบ และแอปพลิเคชัน/สตรีมมิ่งยอดนิยมอีกมากมาย!

> **ทุกคนสามารถดาวน์โหลดไฟล์ `.exe` สำเร็จรูปไปเปิดใช้งานได้ทันที 100% โดยไม่ต้องติดตั้ง Python หรือโปรแกรมเสริมใดๆ ทั้งสิ้น!**

---

## 📦 ลิงก์ดาวน์โหลด (Download Assets)

* **[ดาวน์โหลดแบบไฟล์ ZIP แนะนำ]**: [`DiscordRichPresence-windows-x64.zip`](https://github.com/Gubbitkeytoday/discord-rich-presence-pro/releases/download/v2.1.0/DiscordRichPresence-windows-x64.zip) *(มีทั้ง .exe และ config.json พร้อมใช้งาน)*
* **[ดาวน์โหลดเฉพาะตัว .exe]**: [`DiscordRichPresence.exe`](https://github.com/Gubbitkeytoday/discord-rich-presence-pro/releases/download/v2.1.0/DiscordRichPresence.exe)

---

## 🚀 วิธีใช้งานใน 3 ขั้นตอน (สำหรับทุกคน)

1. ดาวน์โหลดไฟล์ **`DiscordRichPresence-windows-x64.zip`** ด้านบน
2. แตกไฟล์ (Extract ZIP) ไว้ที่โฟลเดอร์ใดก็ได้บนคอมพิวเตอร์ของคุณ
3. ดับเบิลคลิกเปิด **`DiscordRichPresence.exe`** ได้ทันที!
   * *จะมีไอคอนโผล่ขึ้นมาที่ System Tray (มุมขวาล่างของหน้าจอ ข้างนาฬิกา Windows) แสดงว่าโปรแกรมกำลังทำงานอยู่*
   * *คุณสามารถคลิกขวาที่ไอคอนเพื่อ หยุดชั่วคราว, แก้ไขการตั้งค่า หรือปิดโปรแกรมได้ตลอดเวลา*

---

## 🌟 อะไรใหม่ในเวอร์ชัน 2.1.0 (What's New in v2.1.0)

### 1. 🌐 Facebook Ecosystem Support (ครอบคลุมครบทั้งระบบ)
- **Facebook Watch & Reels**: ตรวจจับการรับชมคลิปวิดีโอและ Reels บน Facebook อัตโนมัติ แสดงชื่อคลิป/เพจ พร้อมโลโก้ Facebook ความละเอียดสูง และปุ่มกดตรงเข้าสู่ `▶ Facebook Watch`
- **Facebook Feed Browsing**: เมื่อเปิดอ่านฟีด Facebook บนเบราว์เซอร์ แสดงสถานะ `กำลังท่องฟีด Facebook` (News Feed • สังคมออนไลน์)
- **Facebook Messenger**: ตรวจจับการเปิดใช้งานแชท แสดงไอคอน Messenger และสถานะ `กำลังแชท / สนทนาข้อความ`

### 2. 🎬 Streaming & Entertainment Platforms
- **Netflix**: แสดงสถานะการรับชมภาพยนตร์/ซีรีส์บน Netflix พร้อมโลโก้คมชัด
- **Twitch**: ตรวจจับ Live Stream บน Twitch แสดงชื่อช่อง/สตรีมเมอร์ พร้อมปุ่มรับชม
- **TikTok**: แสดงสถานะการรับชมวิดีโอสั้นและเทรนด์บน TikTok
- **SoundCloud**: รองรับโหมดฟังเพลง (Listening Mode) แสดงชื่อเพลงและศิลปิน
- **YouTube & YouTube Music**: ซิงค์ภาพหน้าปกคลิปจริงระดับ MaxRes/HQ และหลอดเวลาแบบเรียลไทม์

### 3. 🛠️ Creative & Developer Apps Detection
- **Visual Studio Code**: โหมด Multitasking โชว์ชื่อไฟล์และ Workspace ที่กำลังเขียนโค้ด
- **Figma**: แสดงสถานะการออกแบบ UI/UX และ Prototyping
- **Blender**: แสดงสถานะการปั้นโมเดล 3D และ Render งาน
- **GitHub**: แสดงสถานะการ Review Code และจัดการ Repository
- **ChatGPT & Claude AI**: แสดงสถานะการระดมความคิดและทำงานร่วมกับ AI
- **Notion**: แสดงสถานะการจัดระเบียบงานและจดบันทึก
- **Postman**: แสดงสถานะการทดสอบและพัฒนา API
- **X (Twitter) & Instagram**: แสดงสถานะการอัปเดตข่าวสารและภาพถ่าย

### 4. ⚡ Core Improvements
- **100% Logic Test Coverage**: ผ่านการทดสอบ Unit Tests ทุกแพลตฟอร์ม
- **Efficiency Mode (EcoQoS)**: รันที่สิทธิ Below-Normal กิน CPU แทบเป็น 0% และไม่หน่วงเครื่อง
- **Automatic Game Suppression**: ซ่อนสถานะอัตโนมัติเมื่อเปิดเกมเต็มจอ เพื่อไม่รบกวน FPS ของเกม
