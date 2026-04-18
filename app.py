import sqlite3
import os
import base64
from flask import Flask, request, render_template, redirect, session

app = Flask(__name__)
app.secret_key = "key"
admin_pw = base64.b64encode("admin".encode('utf-8')).decode('utf-8')

# ============================================
#  DataBase
# ============================================
if not os.path.exists("users.db"):
    db = sqlite3.connect("users.db")
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    db.execute("CREATE TABLE flag (id INTEGER PRIMARY KEY, value TEXT)")
    db.execute("INSERT INTO users (username, password) VALUES ('admin', ?)", (admin_pw,))
    db.execute("INSERT INTO flag (value) VALUES (?)", ("FLAG{" + os.urandom(32).hex() + "}",))
    db.commit()
    db.close()
else:
    db = sqlite3.connect("users.db")
    db.execute("DELETE FROM users WHERE username = 'admin'")
    db.execute("INSERT INTO users (username, password) VALUES ('admin', ?)", (admin_pw,))
    db.commit()
    db.close()

# ============================================
#  메인 페이지 (GET /)
#  - session에서 username 가져오기
#  - admin이면 DB에서 flag 조회
#  - index.html 렌더링 (username, flag 전달)
# ============================================
@app.route('/')
def index():
    session_username = session.get('username')
    if session_username:
        username = base64.b64decode(session_username).decode('utf-8') # 세션에 username 있다면 가져와서 username에 저장
    else:
        username = None
    flag = None # flag 변수 생성
    if username == 'admin': # 세션 username이 admin이면
        db = sqlite3.connect('users.db') # db 접속해서
        flag_query = db.execute("SELECT value FROM flag") # flag 값 확인하는 쿼리 문으로 변수에 저장
        flag = flag_query.fetchone()[0] # 단일 행의 첫번째 컬럼인 value를 flag에 저장
    return render_template('index.html', username=username, flag=flag) # 변수 포함해 렌더링

# ============================================
#  로그인 (GET, POST /login)
#  - GET: login.html 렌더링
#  - POST: 폼에서 username, password를 받아 DB 조회
#    → 성공: session에 username 저장, 메인으로 redirect
#    → 실패: 에러 메시지와 함께 login.html 렌더링
# ============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = sqlite3.connect('users.db')
        user_query = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = user_query.fetchone()
        db.close()
        if user:
            session['username'] = base64.b64encode(username.encode('utf-8')).decode('utf-8')
            return redirect('/')
        else:
            return render_template('login.html', error="ID or PW is incorrect")
    return render_template('login.html')

# ============================================
#  회원가입 (GET, POST /signup)
#  - GET: signup.html 렌더링
#  - POST: 폼에서 username, password를 받아 DB에 INSERT
#    → "admin" 가입 불가
#    → 성공: /login으로 redirect
# ============================================
@app.route('/signup', methods=['GET', 'POST']) # 메소드 GET, POST 사용
def signup():
    if request.method == 'POST': # POST 요청 시
        username = request.form.get('username') # FORM의 username 가져와서 username 변수에 저장
        password = request.form.get('password') # FORM의 password 가져와서 password 변수에 저장
        if username == 'admin': # username 변수 값이 admin이면
            return render_template('signup.html', error="This ID can be used") # 가입 못하게 막기
        db = sqlite3.connect('users.db') # users.db 파일 접근
        user_query = db.execute("SELECT * FROM users WHERE username = ?", (username,)) # 존재하는 유저 확인 쿼리
        if user_query.fetchone(): # 존재한다면
            db.close() # db 접근 종료하고
            return render_template('signup.html', error="ID alreay exists (session secret key: 'key')") # 가입 못하게 에러 띄우기
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        db.commit() # 전부 아니면 위 INSERT 문으로 db 저장 및 commit
        db.close() # db 종료
        return redirect('/login') # 로그인하러 /login으로 보내기
    return render_template('signup.html') # GET 요청시 signup 렌더링

# ============================================
#  로그아웃 (GET /logout)
#  - session 초기화 후 메인으로 redirect
# ============================================
@app.route('/logout')
def logout():
    session.clear() # session 초기화
    return redirect('/') # 메인 index로 redirect

# ============================================
#  서버 실행
# ============================================
if __name__ == "__main__":
    app.run(debug=True) # 서버 실행 : 디버그 로그 표시 (debug=True)
