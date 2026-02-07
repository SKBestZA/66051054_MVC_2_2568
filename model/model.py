import pandas as pd
import os
from datetime import datetime

class Claimant:
    def __init__(self, id: str, firstname: str, lastname: str, income: float, c_type: str):
        # ใส่ __ นำหน้าให้หมด (Private Attributes)
        self.__id = id
        self.__firstname = firstname
        self.__lastname = lastname
        self.__income = float(income)
        self.__c_type = c_type

    # --- Property (Getter) : เปิดให้คนภายนอก "อ่าน" ได้ แต่ "แก้ไข" ไม่ได้ ---
    
    @property
    def id(self):
        return self.__id

    @property
    def firstname(self):
        return self.__firstname

    @property
    def lastname(self):
        return self.__lastname

    @property
    def income(self):
        return self.__income

    @property
    def type(self):
        return self.__c_type

    # --- Method เสริม ---
    def get_full_name(self):
        return f"{self.__firstname} {self.__lastname}"

    def __str__(self):
        return f"{self.get_full_name()} ({self.__type})"

def get_claimant_by_id_as_object(cid: str):
    """ค้นหาผู้ขอเยียวยาจาก ID"""
    try:
        filepath = os.path.join('model', 'data', 'claimants.csv')
        
        # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        df = pd.read_csv(filepath)
        
        # ตรวจสอบว่า cid เป็นตัวเลขหรือไม่
        if not cid.isdigit():
            print(f"❌ Invalid ID (not numeric): {cid}")
            return None
        
        # แปลงเป็น int เพื่อเปรียบเทียบ
        cid_int = int(cid)
        row = df[df['id'] == cid_int]
        
        if not row.empty:
            r = row.iloc[0]
            claimant = Claimant(
                id=str(r['id']),
                firstname=r['firstname'],
                lastname=r['lastname'],
                income=r['income'],
                c_type=r['type']
            )
            print(f"✅ Found claimant: {claimant.get_full_name()}")
            return claimant
        else:
            print(f"❌ No claimant found with ID: {cid}")
            return None
            
    except Exception as e:
        print(f"❌ Error in get_claimant_by_id_as_object: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_all_claimants_as_objects():
    """ดึงรายชื่อผู้ขอเยียวยาทั้งหมด"""
    try:
        filepath = os.path.join('model', 'data', 'claimants.csv')
        
        # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return []
        
        df = pd.read_csv(filepath)
        claimants_list = []
        
        for _, row in df.iterrows():
            person = Claimant(
                id=str(row['id']),
                firstname=row['firstname'],
                lastname=row['lastname'],
                income=row['income'],
                c_type=row['type']
            )
            claimants_list.append(person)
        
        print(f"✅ Loaded {len(claimants_list)} claimants")
        return claimants_list
        
    except Exception as e:
        print(f"❌ Error in get_all_claimants_as_objects: {e}")
        import traceback
        traceback.print_exc()
        return []

class BaseModel:
    def save_compensation(self, claim_id: str, amount: float):
        """
        บันทึกผลการคำนวณลงไฟล์ compensations.csv
        """
        # 1. ตรวจสอบและสร้างโฟลเดอร์ก่อนเสมอ (กันเหนียว)
        directory = os.path.join('model', 'data')
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        filepath = os.path.join(directory, 'compensations.csv')

        # 2. เตรียมข้อมูล (ตัด calc_date ออกก่อน เพื่อให้ตรงกับ Controller ที่เขียนไว้ตอนแรก)
        # หรือถ้าจะใส่ calc_date ต้องไปแก้ตอนอ่านไฟล์ (read_csv) ด้วย
        new_data = {
            'claim_id': [str(claim_id)],  # แปลงเป็น str ให้ชัวร์
            'amount': [float(amount)]     # แปลงเป็น float ให้ชัวร์
        }
        df = pd.DataFrame(new_data)
        
        try:
            # 3. เช็คละเอียด: ถ้าไฟล์ไม่มี OR ไฟล์มีแต่ขนาดเป็น 0 (ไฟล์เปล่า)
            if not os.path.exists(filepath) or os.stat(filepath).st_size == 0:
                # เขียนใหม่ + มี Header
                df.to_csv(filepath, index=False, encoding='utf-8')
                print(f"✅ Created new compensation file and saved claim {claim_id}")
            else:
                # มีไฟล์และมีข้อมูลแล้ว -> ต่อท้าย + ไม่มี Header
                df.to_csv(filepath, mode='a', header=False, index=False, encoding='utf-8')
                print(f"✅ Appended claim {claim_id} to existing file")
                
        except Exception as e:
            print(f"❌ Error saving compensation: {e}")
            # ปริ้น traceback เพื่อดูบรรทัดที่ผิด
            import traceback
            traceback.print_exc()

    def save_claim(self, claim_id: str, claimant_id: int):
        directory = os.path.join('model', 'data')
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        filepath = os.path.join(directory, 'claims.csv')
        
        # ใช้ datetime ปัจจุบัน
        new_data = {
            'id': [str(claim_id)], 
            'claimant_id': [int(claimant_id)], 
            'request_date': [datetime.now().strftime("%Y-%m-%d")], 
            'status': ['Approved']
        }
        df = pd.DataFrame(new_data)
        
        try:
            if not os.path.exists(filepath) or os.stat(filepath).st_size == 0:
                df.to_csv(filepath, index=False, encoding='utf-8')
            else:
                df.to_csv(filepath, mode='a', header=False, index=False, encoding='utf-8')
        except Exception as e:
             print(f"❌ Error saving claim: {e}")

class Claim(BaseModel):
    def __init__(self,income:float):
        self.__income=income
    def calculate_compen(self):
        amount=self.__income
        return min(amount, 20000)


class LowIncomeClaim(BaseModel):
    def __init__(self,income:float):
        self.__income=income
    def calculate_compen(self):
        return 6500.0

class HighIncomeClaim(BaseModel):
    def __init__(self,income:float):
        self.__income=income
    def calculate_compen(self):
        amount=self.__income/5
        return min(amount, 20000)