# controller/controller.py
import os
import sys
from datetime import datetime
import pandas as pd
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.model import (
    Claim, LowIncomeClaim, HighIncomeClaim,
    get_all_claimants_as_objects, 
    get_claimant_by_id_as_object
)


class ClaimController:
    """Controller หลักสำหรับจัดการคำขอเยียวยา"""
    
    def __init__(self):
        self.claims_file = os.path.join('model', 'data', 'claims.csv')
        self.compensations_file = os.path.join('model', 'data', 'compensations.csv')
        self._ensure_data_files()
    
    def _ensure_data_files(self):
        """สร้างไฟล์ข้อมูลถ้ายังไม่มี"""
        data_dir = os.path.join('model', 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # สร้างไฟล์ claims.csv ถ้ายังไม่มี
        if not os.path.exists(self.claims_file) or os.path.getsize(self.claims_file) == 0:
            df = pd.DataFrame(columns=['id', 'claimant_id', 'request_date', 'status'])
            df.to_csv(self.claims_file, index=False)
        
        # สร้างไฟล์ compensations.csv ถ้ายังไม่มี
        if not os.path.exists(self.compensations_file) or os.path.getsize(self.compensations_file) == 0:
            df = pd.DataFrame(columns=['claim_id', 'amount'])
            df.to_csv(self.compensations_file, index=False)
        
    def get_all_claims(self):
        """ดึงรายการคำขอทั้งหมด"""
        try:
            # ตรวจสอบว่าไฟล์มีอยู่และไม่ว่าง
            if not os.path.exists(self.claims_file) or os.path.getsize(self.claims_file) == 0:
                return []
            
            claims_df = pd.read_csv(self.claims_file)
            
            # ตรวจสอบว่า DataFrame ว่างหรือไม่
            if claims_df.empty:
                return []
            
            # อ่านข้อมูลค่าชดเชย
            compensations = {}
            if os.path.exists(self.compensations_file) and os.path.getsize(self.compensations_file) > 0:
                try:
                    comp_df = pd.read_csv(self.compensations_file)
                    print(f"📊 Compensations file loaded: {len(comp_df)} records")
                    
                    if not comp_df.empty:
                        compensations = dict(zip(comp_df['claim_id'].astype(str), comp_df['amount']))
                        print(f"💰 Compensations dict: {compensations}")
                except pd.errors.EmptyDataError:
                    print("⚠️ Compensations file is empty")
            else:
                print("⚠️ Compensations file not found or empty")
            
            # สร้างรายการผลลัพธ์
            result = []
            for _, row in claims_df.iterrows():
                claimant = get_claimant_by_id_as_object(str(row['claimant_id']))
                claim_id_str = str(row['id'])
                compensation_amount = compensations.get(claim_id_str, 0)
                
                print(f"🔍 Claim ID: {claim_id_str}, Compensation: {compensation_amount}")
                
                claim_info = {
                    'claim_id': claim_id_str,
                    'claimant_id': row['claimant_id'],
                    'claimant_name': claimant.get_full_name() if claimant else 'Unknown',
                    'claimant_type': claimant.type if claimant else 'Unknown',
                    'request_date': row['request_date'],
                    'status': row['status'],
                    'compensation': compensation_amount
                }
                result.append(claim_info)
            
            return result
            
        except pd.errors.EmptyDataError:
            return []
        except Exception as e:
            print(f"❌ Error in get_all_claims: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def create_new_claim(self, claimant_id: str):
        """สร้างคำขอเยียวยาใหม่"""
        try:
            claimant = get_claimant_by_id_as_object(claimant_id)
            if not claimant:
                return {
                    'success': False,
                    'claim_id': None,
                    'amount': 0,
                    'message': f'ไม่พบผู้ขอเยียวยารหัส {claimant_id}'
                }
            
            claim_id = self._generate_claim_id()
            model = self._get_claim_model(claimant)
            amount = model.calculate_compen()
            
            print(f"🎯 Creating claim - ID: {claim_id}, Claimant: {claimant_id}, Amount: {amount}")
            
            # บันทึกข้อมูล
            model.save_claim(claim_id, int(claimant_id))
            print(f"✅ Saved claim to claims.csv")
            
            model.save_compensation(claim_id, amount)
            print(f"✅ Saved compensation to compensations.csv")
            
            return {
                'success': True,
                'claim_id': claim_id,
                'amount': amount,
                'claimant_name': claimant.get_full_name(),
                'claimant_type': claimant.type,
                'message': f'สร้างคำขอสำเร็จ รหัส {claim_id}'
            }
        except Exception as e:
            print(f"❌ Error in create_new_claim: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'claim_id': None,
                'amount': 0,
                'message': f'เกิดข้อผิดพลาด: {str(e)}'
            }
    
    def _get_claim_model(self, claimant):
        """เลือก Model ตามประเภท"""
        if claimant.type == 'รายได้น้อย':
            return LowIncomeClaim(claimant.income)
        elif claimant.type == 'รายได้สูง':
            return HighIncomeClaim(claimant.income)
        else:
            return Claim(claimant.income)
    
    def _generate_claim_id(self):
        """สร้างรหัสคำขอ 8 หลัก (เริ่มต้นด้วย 8)"""
        # เริ่มต้นด้วย 8 เสมอ + ตามด้วยเลข 7 หลักสุ่ม
        remaining = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        claim_id = '8' + remaining
        
        try:
            if os.path.exists(self.claims_file) and os.path.getsize(self.claims_file) > 0:
                df = pd.read_csv(self.claims_file)
                # ถ้า ID ซ้ำ ให้สุ่มใหม่
                while claim_id in df['id'].astype(str).values:
                    remaining = ''.join([str(random.randint(0, 9)) for _ in range(7)])
                    claim_id = '8' + remaining
        except Exception:
            pass
        
        return claim_id


class ClaimantController:
    """Controller สำหรับจัดการผู้ขอเยียวยา"""
    
    def get_all_claimants(self):
        """ดึงรายชื่อทั้งหมด"""
        try:
            claimants = get_all_claimants_as_objects()
            return [
                {
                    'id': c.id,
                    'name': c.get_full_name(),
                    'income': c.income,
                    'type': c.type
                }
                for c in claimants
            ]
        except Exception as e:
            print(f"❌ Error in get_all_claimants: {e}")
            return []
    
    def get_claimant(self, claimant_id: str):
        """ดึงข้อมูลผู้ขอคนเดียว"""
        try:
            claimant = get_claimant_by_id_as_object(claimant_id)
            if claimant:
                return {
                    'id': claimant.id,
                    'name': claimant.get_full_name(),
                    'income': claimant.income,
                    'type': claimant.type
                }
            return None
        except Exception as e:
            print(f"❌ Error in get_claimant: {e}")
            return None


class AuthController:
    """Controller สำหรับ Login"""
    
    def __init__(self):
        self.admin_users = {
            'admin': {'password': '1234', 'role': 'เจ้าหน้าที่'}
        }
    
    def login(self, username: str, password: str):
        """ตรวจสอบ Login"""
        try:
            # ตรวจสอบ admin
            if username in self.admin_users:
                if self.admin_users[username]['password'] == password:
                    return {
                        'success': True,
                        'role': self.admin_users[username]['role'],
                        'username': username,
                        'claimant_id': None,
                        'message': f'เข้าสู่ระบบสำเร็จ'
                    }
                else:
                    return {
                        'success': False,
                        'role': None,
                        'username': None,
                        'claimant_id': None,
                        'message': 'รหัสผ่านไม่ถูกต้อง'
                    }
            
            # ตรวจสอบประชาชน
            claimant = get_claimant_by_id_as_object(username)
            
            if claimant:
                if password == username:
                    return {
                        'success': True,
                        'role': 'ประชาชน',
                        'username': claimant.get_full_name(),
                        'claimant_id': claimant.id,
                        'claimant_data': {
                            'id': claimant.id,
                            'name': claimant.get_full_name(),
                            'income': claimant.income,
                            'type': claimant.type
                        },
                        'message': f'เข้าสู่ระบบสำเร็จ'
                    }
            
            return {
                'success': False,
                'role': None,
                'username': None,
                'claimant_id': None,
                'message': 'รหัสผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'
            }
        except Exception as e:
            print(f"❌ Error in login: {e}")
            return {
                'success': False,
                'role': None,
                'username': None,
                'claimant_id': None,
                'message': f'เกิดข้อผิดพลาด: {str(e)}'
            }