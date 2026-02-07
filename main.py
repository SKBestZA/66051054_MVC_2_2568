# main.py
"""
จุดเริ่มต้นของระบบคำนวณเงินเยียวยา
ไฟล์นี้ใช้สำหรับรันเซิร์ฟเวอร์เท่านั้น
API ทั้งหมดอยู่ใน controller/api_controller.py
"""

import uvicorn
from controller.api_controller import app

if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 ระบบคำนวณเงินเยียวยา")
    print("=" * 60)
    print("  📍 URL: http://127.0.0.1:8000")
    print("  🔑 Admin: admin / 1234")
    print("  👤 Citizen: 1 / 1, 2 / 2, ...")
    print("=" * 60)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)