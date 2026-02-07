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

def get_all_claimants_as_objects():
    filepath = os.path.join('model', 'data', 'claimants.csv')
    df = pd.read_csv(filepath)
    claimants_list = []
    
    for _, row in df.iterrows():
        person = Claimant(
            id=str(row['id']),
            firstname=row['firstname'],
            lastname=row['lastname'],
            income=row['income'],
            c_type=row['type']  # ✅ เปลี่ยนจาก type_=row['type']
        )
        claimants_list.append(person)
        
    return claimants_list


def get_claimant_by_id_as_object(cid: str):
    filepath = os.path.join('model', 'data', 'claimants.csv')
    df = pd.read_csv(filepath)
    row = df[df['id'] == int(cid)]
    
    if not row.empty:
        r = row.iloc[0]
        return Claimant(
            id=str(r['id']),
            firstname=r['firstname'],
            lastname=r['lastname'],
            income=r['income'],
            c_type=r['type']  # ✅ เปลี่ยนจาก type_=r['type']  (ถ้ายังใช้ type_ อยู่)
        )
    return None

class BaseModel:
    def save_compensation(self, claim_id:str, amount:float):
        """
        บันทึกผลการคำนวณลงไฟล์ compensations.csv
        """
        filepath = os.path.join('model', 'data', 'compensations.csv')

        # เตรียมข้อมูลที่จะบันทึก: [รหัสคำขอ, จำนวนเงิน, วันที่คำนวณ]
        new_data = {
            'claim_id': [claim_id], 
            'amount': [amount], 
            'calc_date': [datetime.now().strftime("%Y-%m-%d")]
        }
        df = pd.DataFrame(new_data)
        
        # เปิดไฟล์โหมด 'a' (append) เพื่อต่อท้ายข้อมูลเดิม
        try:
            if not os.path.exists(filepath):
                # ถ้ายังไม่มีไฟล์: สร้างใหม่ + เขียน Header
                df.to_csv(filepath, index=False, encoding='utf-8')
            else:
                # ถ้ามีไฟล์แล้ว: บันทึกต่อท้าย (mode='a') + ไม่เอา Header (header=False)
                df.to_csv(filepath, mode='a', header=False, index=False, encoding='utf-8')
        except Exception as e:
            print(f"Error saving compensation: {e}")

    def save_claim(self, claim_id: str, claimant_id: int):
        filepath =os.path.join('model', 'data', 'claims.csv')
        new_data = {'id': [claim_id], 'claimant_id': [claimant_id], 'request_date': [datetime.now().strftime("%Y-%m-%d")], 'status': ['Approved']}
        df = pd.DataFrame(new_data)
        if not os.path.exists(filepath):
            df.to_csv(filepath, index=False)
        else:
            df.to_csv(filepath, mode='a', header=False, index=False)

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