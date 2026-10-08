from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
import sqlite3
import hashlib
import jwt
import datetime
from typing import List, Optional
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Alex Crimson DevStore API", version="2.0.0")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# HTML 템플릿 연결 (templates 폴더 안에 Crimson UI html을 index.html로 넣어두면 됨)
templates = Jinja2Templates(directory="templates")

# ==========================================
# 🗄️ 데이터베이스 스키마 초기화 (정규화 및 소유권 테이블 포함)
# ==========================================
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # 1. users 테이블 (이메일 인증 여부 추가)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user'
        )
    """)
    #TODO: 기존 DB에 role컬럼이 없으면 ALTER TABLE로 추가
    cursor.execute(""" PRAGMA table_info(users)""")
    has_role = False
    for t in cursor.fetchall():
        if t[1] == 'role':
            has_role = True
    
    if not has_role:
        cursor.execute(""" ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user' """)
    
    # 2. projects 테이블 (상품 기본 정보)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            price_formatted TEXT NOT NULL,
            badge TEXT NOT NULL,
            description TEXT NOT NULL,
            downloads_count INTEGER DEFAULT 0,
            rating REAL DEFAULT 5.0,
            download_url TEXT,
            demo_url TEXT,
            image_gradient TEXT
        )
    """)
    
    # 3. project_tech_stacks 테이블 (정규화: 1:N 기술 스택)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_tech_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            tech_name TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        )
    """)

    # 4. payment_history 테이블 (결제 및 멱등성 보장을 위한 order_id UNIQUE)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            project_id INTEGER NOT NULL,
            order_id TEXT UNIQUE NOT NULL,
            method TEXT NOT NULL,
            amount TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # 5. entitlements 테이블 (소유권 및 다운로드/링크 접근 권한 핵심 테이블)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entitlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            project_id INTEGER NOT NULL,
            granted_at TEXT NOT NULL,
            UNIQUE(user_email, project_id)
        )
    """)
    
    conn.commit()
    conn.close()
    
# 서버 기동 시 DB 초기화 및 기본 샘플 데이터 주입
@app.on_event("startup")
def startup_event():
    init_db()
    seed_default_projects()
    

def seed_default_projects():
    """서버 최초 기동 시 프론트엔드가 요구하는 기본 프로젝트 데이터가 없으면 주입"""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        defaults = [
            (1, "PsyStore 포트폴리오 & 마켓플레이스", "link", 0, "Free", "라이브 데모", "지금 보고 있는 이 사이트. FastAPI + SQLite 백엔드에 JWT 로그인, 토스페이먼츠 모의 결제, 보유 자산·결제 내역 관리까지 직접 구현한 포트폴리오 겸 마켓플레이스.", 0, 5.0, "", "/", "from-crimson-900 via-rose-950 to-black"),
            (2, "FastAPI 회원가입·로그인 API", "download", 9900, "₩9,900", "소스 코드 (.zip)", "PsyStore 웹용 인증 API. FastAPI + SQLite로 사용자 테이블을 만들고, 비밀번호를 SHA-256 해시로 저장하는 회원가입·로그인 서버.", 0, 5.0, "#", "", "from-rose-900 via-crimson-950 to-black"),
            (3, "리눅스 홈서버 구축기 (HP Victus 15)", "link", 0, "Free", "학습 기록", "노트북을 리눅스 서버로 바꿔 Uvicorn으로 서비스를 직접 운영 중. crontab 스케줄링, 프로세스·시그널, 파일 권한을 실습했고 Nginx 리버스 프록시와 로드밸런서 구성을 준비하고 있음.", 0, 5.0, "", "#", "from-red-950 via-burgundy-900 to-black"),
            (4, "Agar.io 클론게임", "link", 1000, "₩1,000", "실시간 게임", "agar.io 스타일 멀티플레이 게임. 룸 10개 × 룸당 최대 100명", 0, 5.0, "", "https://agario.psyrod.dev/", "from-red-950 via-burgundy-900 to-black")
        ]
        tech_stacks = {
            1: ["FastAPI", "SQLite", "JWT", "Tailwind CSS"],
            2: ["FastAPI", "SQLite", "Pydantic"],
            3: ["Ubuntu", "Uvicorn", "crontab", "Nginx"],
            4: ["C#", ".NET", ""]

        }
        for p in defaults:
            cursor.execute("""
                INSERT OR IGNORE INTO projects (id, title, category, price, price_formatted, badge, description, downloads_count, rating, download_url, demo_url, image_gradient)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, p)
        for project_id, techs in tech_stacks.items():
            cursor.executemany("INSERT INTO project_tech_stacks (project_id, tech_name) VALUES (?, ?)", [(project_id, t) for t in techs])
        conn.commit()
    conn.close()

# ==========================================
# ✉️ 모의 이메일 전송 함수 (콘솔 로깅 처리)
# ==========================================
def send_mock_email(to_email: str, subject: str, content: str):
    print(f"\n[EMAIL SEND MOCK] ----------------------------------------")
    print(f"TO: {to_email}")
    print(f"SUBJECT: {subject}")
    print(f"BODY:\n{content}")
    print(f"----------------------------------------------------------\n")

# ==========================================
# 🔒 인증 관련 헬퍼 (JWT 검증 의존성)
# ==========================================
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 누락되었거나 올바르지 않습니다.")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub") # user_email 반환
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="만료된 토큰입니다. 다시 로그인해주세요.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

# ==========================================
# 📡 1. 사용자 인증 및 세션 관리 API (/api/auth)
# ==========================================
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/api/signup")
def signup(req: SignupRequest):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    hashed_pw = hash_password(req.password)
    try:
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (req.name, req.email, hashed_pw))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일 주소입니다.")
    finally:
        conn.close()
    
    # 회원가입 성공 시 모의 이메일 발송
    send_mock_email(req.email, "[Alex.Crimson] 회원가입을 환영합니다!", f"{req.name}님, DevStore & Portfolio 가입이 완료되었습니다.")
    return {"message": "회원가입이 완료되었습니다. 이메일 인증을 진행해주세요."}

@app.post("/api/login")
def login(req: LoginRequest):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    hashed_pw = hash_password(req.password)
    cursor.execute("SELECT name, email FROM users WHERE email = ? AND password = ?", (req.email, hashed_pw))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    # JWT 토큰 생성 (유효기간 24시간)
    payload = {
        "sub": user[1],
        "name": user[0],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "message": f"환영합니다, {user[0]}님 🚀",
        "token": token,
        "user": {"name": user[0], "email": user[1]}
    }

# ==========================================
# 🛍️ 2. 마켓플레이스 프로젝트 관리 API (/api/projects)
# ==========================================
@app.get("/api/projects")
def get_projects(category: Optional[str] = "all", search: Optional[str] = None, user_email: Optional[str] = None):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    query = "SELECT id, title, category, price, price_formatted, badge, description, downloads_count, rating, download_url, demo_url, image_gradient FROM projects WHERE 1=1"
    params = []

    if category and category != "all":
        query += " AND category = ?"
        params.append(category)
    
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    projects = []
    for row in rows:
        p_id = row[0]
        # 기술 스택 가져오기 (정규화된 테이블 조회)
        cursor.execute("SELECT tech_name FROM project_tech_stacks WHERE project_id = ?", (p_id,))
        techs = [t[0] for t in cursor.fetchall()]
        if not techs:
            techs = ["JavaScript", "Tailwind"] # 기본 샘플 스택

        # 유저가 로그인한 경우 소유권(entitlements) 여부 확인
        purchased = False
        if user_email:
            cursor.execute("SELECT 1 FROM entitlements WHERE user_email = ? AND project_id = ?", (user_email, p_id))
            purchased = cursor.fetchone() is not None or row[3] == 0
        else:
            purchased = (row[3] == 0) # 무료 상품은 기본 보유

        projects.append({
            "id": p_id,
            "title": row[1],
            "category": row[2],
            "price": row[3],
            "priceFormatted": row[4],
            "badge": row[5],
            "description": row[6],
            "techStack": techs,
            "downloadsCount": row[7],
            "rating": row[8],
            "downloadUrl": row[9],
            "demoUrl": row[10],
            "purchased": purchased,
            "imageGradient": row[11]
        })
    conn.close()
    return projects

@app.get("/api/projects/{project_id}")
def get_project_detail(project_id: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category, price, price_formatted, badge, description, downloads_count, rating, download_url, demo_url, image_gradient FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    return {"id": row[0], "title": row[1], "category": row[2], "price": row[3]}

# ==========================================
# 👤 3. 마이페이지 및 보유 자산 API (/api/user)
# ==========================================
@app.get("/api/user/assets")
def get_user_assets(current_user: str = Depends(get_current_user)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # entitlements 테이블을 조인해서 소유한 프로젝트 목록만 초고속 조회!
    cursor.execute("""
        SELECT p.id, p.title, p.category, p.download_url, p.demo_url, p.badge
        FROM entitlements e
        JOIN projects p ON e.project_id = p.id
        WHERE e.user_email = ?
    """, (current_user,))
    rows = cursor.fetchall()
    conn.close()

    assets = [{"id": r[0], "title": r[1], "category": r[2], "downloadUrl": r[3], "demoUrl": r[4], "badge": r[5]} for r in rows]
    return assets

@app.get("/api/user/history")
def get_payment_history(current_user: str = Depends(get_current_user)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, title, method, amount, date, status FROM payment_history ph JOIN projects p ON ph.project_id = p.id WHERE ph.user_email = ?", (current_user,))
    rows = cursor.fetchall()
    conn.close()

    history = [{"orderId": r[0], "title": r[1], "method": r[2], "amount": r[3], "date": r[4], "status": r[5]} for r in rows]
    return history

# ==========================================
# 💳 4. 토스페이먼츠 결제 연동 모의 & 멱등성 보장 (/api/payment)
# ==========================================
class CheckoutRequest(BaseModel):
    project_id: int
    order_id: str
    method: str
    amount: int

@app.post("/api/payment/checkout")
def checkout(req: CheckoutRequest, current_user: str = Depends(get_current_user)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # 1. 멱등성(Idempotency) 검증: 이미 처리된 order_id인지 확인
    cursor.execute("SELECT id FROM payment_history WHERE order_id = ?", (req.order_id,))
    if cursor.fetchone():
        conn.close()
        return {"message": "이미 처리된 결제 주문입니다.", "order_id": req.order_id}

    # 2. 상품 정보 확인
    cursor.execute("SELECT title, price, price_formatted FROM projects WHERE id = ?", (req.project_id,))
    proj = cursor.fetchone()
    if not proj:
        conn.close()
        raise HTTPException(status_code=404, detail="구매하려는 상품이 존재하지 않습니다.")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    #만약 들어온 price하고 안에 있는 price값이 다르다? 그러면 결제 취소 해야됨.
    
    if (proj[1] != req.amount):
        conn.close()
        raise HTTPException(status_code=400, detail="결제 값이 다릅니다!")
            
    try:
        
        
        # 4. 소유권(entitlements) 테이블에 권한 부여 (중복 방지 IGNORE)
        cursor.execute("""
            INSERT INTO entitlements (user_email, project_id, granted_at)
            VALUES (?, ?, ?)
        """, (current_user, req.project_id, now_str))

        # 3. 결제 이력 기록
        cursor.execute("""
            INSERT INTO payment_history (user_email, project_id, order_id, method, amount, date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (current_user, req.project_id, req.order_id, req.method, proj[2], now_str, "결제 완료"))
        

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise HTTPException(status_code=409, detail="이미 보유한 상품입니다!")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"결제 처리 중 오류 발생: {str(e)}")
    finally:
        conn.close()

    # 5. 결제 완료 모의 이메일 전송
    send_mock_email(
        current_user,
        f"[Alex.Crimson] 결제 및 소유권 승인 완료 ({req.order_id})",
        f"주문하신 [{proj[0]}] 상품의 결제({proj[2]})가 정상 승인되었습니다.\n마이페이지에서 소스코드를 다운로드하실 수 있습니다."
    )

    return {"message": "결제 승인 및 소유권 발급 완료!", "order_id": req.order_id}

# ==========================================
# 🌐 프론트엔드 HTML 서빙
# ==========================================
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h3>templates/index.html 파일이 없습니다. 프론트엔드 코드를 templates 폴더 안에 넣어주세요!</h3>"