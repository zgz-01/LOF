"""
Flask 网页应用 — 部署到 Railway

这个应用不直接计算溢价率，而是从本机API服务获取数据并展示。
"""
import os
import json
import urllib.request
import urllib.error
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# 本机API地址（由环境变量配置）
API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8080")


def fetch_api(path: str) -> dict:
    """从本机API服务获取数据"""
    url = f"{API_BASE}{path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LOF-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def premium_marker(pct):
    """溢价率标记"""
    if pct is None:
        return ("⚪", "gray")
    if pct > 5:
        return ("🔴", "red")  # 高溢价，风险
    if pct > 3:
        return ("🟠", "orange")
    if pct > 1:
        return ("🟡", "gold")
    if pct > 0:
        return ("🟢", "green")
    if pct > -1:
        return ("🔵", "blue")
    return ("🟣", "purple")  # 折价


# ============================================================
# 页面路由
# ============================================================

@app.route("/")
def index():
    """首页: 溢价排行"""
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    """API: 获取溢价排行数据（前端Ajax调用）"""
    data = fetch_api("/api/premium")
    if "error" in data:
        return jsonify(data)
    return jsonify(data)


@app.route("/fund/<code>")
def fund_detail(code):
    """基金详情页"""
    return render_template("detail.html", code=code)


@app.route("/api/fund/<code>")
def api_fund_detail(code):
    """API: 获取单只基金详情"""
    data = fetch_api(f"/api/fund/{code}")
    if "error" in data:
        return jsonify(data)
    return jsonify(data)


@app.route("/status")
def status():
    """服务状态页"""
    api_status = fetch_api("/api/status")
    return render_template("status.html", status=api_status)


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
