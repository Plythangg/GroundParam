# คำแนะนำการ Build Geotech.exe

## ข้อกำหนดเบื้องต้น

1. Python 3.8 หรือสูงกว่า
2. ติดตั้ง dependencies ทั้งหมด:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller pillow
   ```

## วิธีการ Build (แบบง่าย)

### วิธีที่ 1: ใช้ Batch File (แนะนำ)

1. Double-click ที่ไฟล์ `build_exe.bat`
2. รอให้ process เสร็จสิ้น
3. ไฟล์ `Geotech.exe` จะอยู่ในโฟลเดอร์ `dist\`

### วิธีที่ 2: Build ด้วย Command Line

```bash
# 1. Convert icon PNG to ICO
python convert_icon.py

# 2. Build with PyInstaller
pyinstaller --clean Geotech.spec
```

## โครงสร้างไฟล์

- `main.py` - Entry point ของโปรแกรม
- `App_Logo.png` - Logo ของโปรแกรม (ต้นฉบับ)
- `App_Logo.ico` - Icon ที่แปลงแล้ว (สร้างอัตโนมัติ)
- `Geotech.spec` - PyInstaller specification file
- `build_exe.bat` - Script สำหรับ build อัตโนมัติ
- `convert_icon.py` - Script แปลง PNG เป็น ICO

## คุณสมบัติของ Geotech.exe

✓ **ชื่อโปรแกรม**: Geotech.exe
✓ **Icon**: ใช้ App_Logo.png ทั้งไอคอนโปรแกรมและในหน้าต่าง
✓ **Single File**: Executable เดียวไม่ต้องพึ่ง DLL ภายนอก
✓ **No Console**: ไม่แสดงหน้าต่าง command prompt
✓ **รวม Dependencies**: รวม PyQt6, Matplotlib, ReportLab ทั้งหมด

## ขนาดไฟล์โดยประมาณ

- **Geotech.exe**: ~150-200 MB (รวม Python runtime และ libraries)

## การแก้ไขปัญหา

### ปัญหา: Import Error
**แก้ไข**: ตรวจสอบว่าติดตั้ง dependencies ครบถ้วน
```bash
pip install -r requirements.txt
```

### ปัญหา: Icon ไม่แสดง
**แก้ไข**: ตรวจสอบว่าไฟล์ App_Logo.png อยู่ในโฟลเดอร์เดียวกัน
```bash
python convert_icon.py
```

### ปัญหา: ModuleNotFoundError
**แก้ไข**: เพิ่ม hidden imports ใน Geotech.spec:
```python
hiddenimports=[
    'your_missing_module',
]
```

## การ Distribute

ไฟล์ `Geotech.exe` ใน `dist\` สามารถ copy ไปใช้ที่เครื่องอื่นได้เลย โดยไม่ต้องติดตั้ง Python

## หมายเหตุ

- ครั้งแรกที่ build อาจใช้เวลา 3-5 นาที
- UPX compression เปิดใช้งานเพื่อลดขนาดไฟล์
- รองรับ Windows 10/11 (64-bit)
