import os
import json
from datetime import datetime

from flask import Flask, render_template, request

# 建立 Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

# 資料檔路徑設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FILE_PATH = os.path.join(DATA_DIR, "applications.json")


@app.route("/")
def index():
    """首頁：說明 + 按鈕連到 /apply"""
    return render_template("index.html")


@app.route("/apply", methods=["GET"])
def apply_get():
    """顯示保單填寫表單"""
    return render_template("form.html")


@app.route("/apply", methods=["POST"])
def apply_post():
    """接收保單表單資料，寫入 JSON 檔，顯示成功頁"""
    form = request.form

    # 必填欄位檢查
    required_fields = ["name", "idNumber", "phone", "crop", "area", "location"]
    missing = [field for field in required_fields if not form.get(field, "").strip()]
    if missing:
        return f"以下欄位為必填：{', '.join(missing)}", 400

    # 確保 data 資料夾存在
    os.makedirs(DATA_DIR, exist_ok=True)

    # 讀舊資料
    current = []
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if raw:
                current = json.loads(raw)

    # 把表單資料變成 dict
    data = {k: v for k, v in form.items()}
    data["createdAt"] = datetime.utcnow().isoformat()

    current.append(data)

    # 寫回 JSON
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    # 顯示成功頁，帶名字進去
    return render_template("success.html", name=form.get("name"))


if __name__ == "__main__":
    # 本機沒設定 PORT 時用 3000，Zeabur 會塞環境變數 PORT
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
