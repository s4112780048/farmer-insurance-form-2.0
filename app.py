import os
import json
from datetime import datetime
from io import BytesIO

from flask import Flask, render_template, request, send_file, abort
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

DATA_DIR = os.path.join(BASE_DIR, "data")
FILE_PATH = os.path.join(DATA_DIR, "applications.json")

import os
import json
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, abort
from authlib.integrations.flask_client import OAuth

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

# ✅ Session 需要
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

DATA_DIR = os.path.join(BASE_DIR, "data")
FILE_PATH = os.path.join(DATA_DIR, "applications.json")

# ✅ Google OAuth
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/login")
def login():
    # 送去 Google 登入
    redirect_uri = url_for("auth_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.get("/auth/callback")
def auth_callback():
    # Google 回來的 callback
    token = google.authorize_access_token()
    userinfo = google.parse_id_token(token)

    # userinfo 裡會有 email / name / picture
    session["user"] = {
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    }
    return redirect(url_for("dashboard"))

@app.get("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.get("/dashboard")
@login_required
def dashboard():
    user = session["user"]
    email = user["email"]

    records = []
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if raw:
                all_data = json.loads(raw)
                # ✅ 只顯示自己 email 的投保資料
                records = [r for r in all_data if r.get("userEmail") == email]

    return render_template("dashboard.html", user=user, records=records)

@app.get("/apply")
def apply_get():
    return render_template("form.html", user=session.get("user"))

@app.post("/apply")
@login_required
def apply_post():
    form = request.form
    required_fields = ["name", "idNumber", "phone", "crop", "area", "location"]
    missing = [f for f in required_fields if not form.get(f, "").strip()]
    if missing:
        return f"以下欄位為必填：{', '.join(missing)}", 400

    os.makedirs(DATA_DIR, exist_ok=True)

    current = []
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if raw:
                current = json.loads(raw)

    data = {k: v for k, v in form.items()}
    data["createdAt"] = datetime.utcnow().isoformat()

    # ✅ 關鍵：把登入者 email 綁進這筆投保紀錄
    data["userEmail"] = session["user"]["email"]

    current.append(data)

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    return render_template("success.html", name=form.get("name"))

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/apply", methods=["GET"])
def apply_get():
    return render_template("form.html")


@app.route("/apply", methods=["POST"])
def apply_post():
    form = request.form

    # 必填欄位不要放 walletAddress，讓它是選填
    required_fields = ["name", "idNumber", "phone", "crop", "area", "location"]
    missing = [field for field in required_fields if not form.get(field, "").strip()]
    if missing:
        return f"以下欄位為必填：{', '.join(missing)}", 400

    os.makedirs(DATA_DIR, exist_ok=True)

    current = []
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if raw:
                current = json.loads(raw)

    data = {k: v for k, v in form.items()}
    data["createdAt"] = datetime.utcnow().isoformat()
    current.append(data)

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    return render_template("success.html", name=form.get("name"))


# 如果你有做匯出 Excel，可以保留這個：
@app.route("/admin/export")
def export_excel():
    if not os.path.exists(FILE_PATH):
        abort(404, description="目前沒有申請資料可匯出。")

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        raw = f.read().strip()
        if not raw:
            abort(404, description="目前沒有申請資料可匯出。")
        data = json.loads(raw)

    if not data:
        abort(404, description="目前沒有申請資料可匯出。")

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Applications")
    output.seek(0)

    filename = "applications_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
