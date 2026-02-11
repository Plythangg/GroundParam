# Geotech v3.0 - Release Notes

## ข้อมูลทั่วไป
- **ชื่อโปรแกรม**: Geotech
- **เวอร์ชัน**: 3.0
- **วันที่**: 2026-01-11
- **แพลตฟอร์ม**: Windows 10/11 (64-bit)

## คุณสมบัติหลัก

### Module 1: SPT Plot
- แสดงกราฟ SPT N-value สำหรับหลายหลุมเจาะ
- รองรับการเพิ่ม/ลบแถวข้อมูล
- กำหนด Ground Elevation และ Water Level ได้
- Export รูปภาพ (PNG, JPG) และข้อมูล (CSV)

### Module 2: Lab Data
- กรอกข้อมูล Laboratory Test (γsat, Su, ϕ')
- Sync ความลึกกับ Module 1 อัตโนมัติ
- Highlight ข้อมูลที่กรอกด้วยสีเขียว
- Export/Import CSV

### Module 3: Parameters Summary
- คำนวณพารามิเตอร์ทางวิศวกรรม อัตโนมัติ
- แสดงผล Consistency (Soft Clay, Dense Sand, etc.)
- Override ด้วยข้อมูล Lab (แสดง * และ highlight สีเขียว)
- Export PDF (All Boreholes หรือแยกรายหลุม)
- Export CSV พร้อม format สมบูรณ์

### Module 4: Design
- แสดงกราฟ Su, Phi, Sigma_v' และอื่นๆ
- เลือกดูแต่ละหลุมหรือทุกหลุมรวมกัน
- Export กราฟแยกหรือรวมกัน

## การใช้งาน

### การเริ่มต้น
1. เปิดโปรแกรม `Geotech.exe`
2. เริ่มต้นที่ Module 1 - กรอกข้อมูล SPT
3. ไปที่ Module 2 - กรอกข้อมูล Lab (optional)
4. คำนวณที่ Module 3 - ดูผลลัพธ์และ Export
5. ดูกราฟที่ Module 4

### การบันทึก/เปิดโปรเจค
- **Save Project**: `File > Save Project` (Ctrl+S)
- **Open Project**: `File > Open Project` (Ctrl+O)
- ไฟล์นามสกุล: `.geoproj`

### Keyboard Shortcuts
- `Ctrl+S`: Save Project
- `Ctrl+O`: Open Project
- `Ctrl+N`: New Project
- `Ctrl+W`: Close

## ข้อกำหนดระบบ

### ขั้นต่ำ
- Windows 10 (64-bit)
- RAM: 4 GB
- Disk Space: 500 MB
- Screen Resolution: 1280x720

### แนะนำ
- Windows 11 (64-bit)
- RAM: 8 GB
- Disk Space: 1 GB
- Screen Resolution: 1920x1080

## การแก้ไขปัญหา

### โปรแกรมไม่เปิด
1. ตรวจสอบว่าเป็น Windows 64-bit
2. ลองรันแบบ Administrator
3. ตรวจสอบ Antivirus (อาจ block ไฟล์)

### Export PDF ไม่ได้
- ตรวจสอบว่ามีสิทธิ์เขียนไฟล์ในโฟลเดอร์นั้น
- ปิดไฟล์ PDF ก่อนถ้าเปิดอยู่

### ข้อมูลหาย
- ตรวจสอบว่าบันทึก Project แล้ว (Ctrl+S)
- เปิดไฟล์ `.geoproj` ที่บันทึกไว้

## การติดต่อ

หากพบปัญหาหรือต้องการคำแนะนำ กรุณาติดต่อทีมพัฒนา

---

© 2026 Geotechnical Engineering. All rights reserved.
