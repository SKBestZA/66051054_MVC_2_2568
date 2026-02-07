from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sys
import os
from urllib.parse import quote, unquote

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.controller import ClaimController, ClaimantController, AuthController

# สร้าง FastAPI app
app = FastAPI(title="ระบบคำนวณเงินเยียวยา")
templates = Jinja2Templates(directory="view")

# สร้าง Controllers
auth_ctrl = AuthController()
claim_ctrl = ClaimController()
claimant_ctrl = ClaimantController()

# Session storage
sessions = {}


# ===== Helper Functions =====
def get_current_user(request: Request):
    """ดึงข้อมูล user จาก cookie"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None


def get_flash_message(request: Request):
    """ดึงข้อความแจ้งเตือนจาก query parameter"""
    flash_type = request.query_params.get("flash_type")
    flash_title = request.query_params.get("flash_title")
    flash_text = request.query_params.get("flash_text")
    
    if flash_type and flash_title and flash_text:
        return {
            'type': unquote(flash_type),
            'title': unquote(flash_title),
            'text': unquote(flash_text)
        }
    return None


# ===== Routes =====

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """หน้าแรก - redirect ตาม role"""
    user = get_current_user(request)
    if user:
        if user['role'] == 'เจ้าหน้าที่':
            return RedirectResponse(url="/dashboard", status_code=302)
        else:
            return RedirectResponse(url="/my-claims", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """หน้า Login"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request
    })


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """ประมวลผล Login"""
    result = auth_ctrl.login(username, password)
    
    if result['success']:
        import secrets
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = result
        
        # Redirect ตาม role
        if result['role'] == 'เจ้าหน้าที่':
            redirect_url = "/dashboard"
        else:
            redirect_url = "/my-claims"
        
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": result['message']
        })


@app.get("/logout")
async def logout(request: Request):
    """ออกจากระบบ"""
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]
    
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_id")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """หน้า Dashboard สำหรับเจ้าหน้าที่"""
    user = get_current_user(request)
    if not user or user['role'] != 'เจ้าหน้าที่':
        return RedirectResponse(url="/login", status_code=302)
    
    claimants_list = claimant_ctrl.get_all_claimants()
    claims = claim_ctrl.get_all_claims()
    flash = get_flash_message(request)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user['username'],
        "role": user['role'],
        "claimants_list": claimants_list,
        "claims": claims,
        "flash": flash
    })


@app.get("/my-claims", response_class=HTMLResponse)
async def my_claims(request: Request):
    """หน้าสำหรับประชาชน"""
    user = get_current_user(request)
    if not user or user['role'] != 'ประชาชน':
        return RedirectResponse(url="/login", status_code=302)
    
    all_claims = claim_ctrl.get_all_claims()
    my_claims = [c for c in all_claims if str(c['claimant_id']) == str(user['claimant_id'])]
    flash = get_flash_message(request)
    
    return templates.TemplateResponse("my_claims.html", {
        "request": request,
        "username": user['username'],
        "role": user['role'],
        "claimant_data": user.get('claimant_data'),
        "claims": my_claims,
        "flash": flash
    })


@app.post("/create_claim")
async def create_claim(
    request: Request,
    claimant_id: str = Form(...)
):
    """สร้างคำขอใหม่ (เจ้าหน้าที่)"""
    user = get_current_user(request)
    if not user or user['role'] != 'เจ้าหน้าที่':
        return RedirectResponse(url="/login", status_code=302)
    
    result = claim_ctrl.create_new_claim(claimant_id)
    
    if result['success']:
        message = f"สร้างคำขอ {result['claim_id']} สำหรับ {result['claimant_name']} จำนวน {result['amount']:,.2f} บาท"
        flash_params = (
            f"?flash_type={quote('success')}"
            f"&flash_title={quote('สำเร็จ')}"
            f"&flash_text={quote(message)}"
        )
    else:
        flash_params = (
            f"?flash_type={quote('danger')}"
            f"&flash_title={quote('ผิดพลาด')}"
            f"&flash_text={quote(result['message'])}"
        )
    
    return RedirectResponse(url=f"/dashboard{flash_params}", status_code=302)


@app.post("/submit-my-claim")
async def submit_my_claim(request: Request):
    """ประชาชนยื่นคำขอ"""
    session_id = request.cookies.get("session_id")
    print(f"🔐 Session ID: {session_id}")
    print(f"📋 Available sessions: {list(sessions.keys())}")
    
    user = get_current_user(request)
    print(f"👤 User from session: {user}")
    
    if not user or user['role'] != 'ประชาชน':
        print(f"❌ Access denied - redirecting to login")
        return RedirectResponse(url="/login", status_code=302)
    
    print(f"✅ User authenticated: {user['username']}")
    result = claim_ctrl.create_new_claim(user['claimant_id'])
    
    if result['success']:
        message = f"ยื่นคำขอสำเร็จ คุณจะได้รับเงิน {result['amount']:,.2f} บาท"
        flash_params = (
            f"?flash_type={quote('success')}"
            f"&flash_title={quote('สำเร็จ')}"
            f"&flash_text={quote(message)}"
        )
    else:
        flash_params = (
            f"?flash_type={quote('danger')}"
            f"&flash_title={quote('ผิดพลาด')}"
            f"&flash_text={quote(result['message'])}"
        )
    
    return RedirectResponse(url=f"/my-claims{flash_params}", status_code=302)
