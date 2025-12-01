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
