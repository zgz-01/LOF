"""
Flask 网页应用 — 部署到 Railway

独立运行：自己抓数据、自己缓存、自己展示
不依赖外部API服务
"""
import os
import json
import time
import threading
from flask import Flask, render_template, jsonify

from fetcher import fetch_palmmicro_lof_data, fetch_usd_cny_rate, fetch_yahoo_quote
from config import INDEX_MAP, YAHOO_SYMBOLS, FUTURE_YAHOO_SYMBOLS

app = Flask(__name__)

# ============================================================
# 内存缓存
# ============================================================
cache = {
    "data": None,
    "timestamp": None,
    "updating": False,
}


def update_cache():
    """刷新数据缓存"""
    if cache["updating"]:
        return
    
    cache["updating"] = True
    try:
        print("[Cache] 开始刷新数据...")
        
        # 1. 从无敌哥抓LOF数据
        lof_data = fetch_palmmicro_lof_data()
        
        # 2. 获取汇率
        cny_rate = fetch_usd_cny_rate()
        
        # 3. 获取Yahoo指数数据
        yahoo_quotes = {}
        for name, symbol in YAHOO_SYMBOLS.items():
            try:
                quote = fetch_yahoo_quote(symbol)
                if quote:
                    yahoo_quotes[name] = quote
                time.sleep(0.3)
            except Exception:
                pass
        
        # 4. 获取期货数据
        future_quotes = {}
        for name, symbol in FUTURE_YAHOO_SYMBOLS.items():
            try:
                quote = fetch_yahoo_quote(symbol)
                if quote:
                    future_quotes[name] = quote
                time.sleep(0.3)
            except Exception:
                pass
        
        cache["data"] = {
            "lof_data": lof_data or {},
            "cny_rate": cny_rate,
            "yahoo_quotes": yahoo_quotes,
            "future_quotes": future_quotes,
        }
        cache["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00",
                                            time.localtime(time.time() + 8*3600))
        print(f"[Cache] 刷新完成: {len(lof_data or {})} 只基金, {len(yahoo_quotes)} 指数, {len(future_quotes)} 期货")
    except Exception as e:
        print(f"[Cache] 刷新失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cache["updating"] = False


def cache_updater():
    """后台定时更新"""
    while True:
        update_cache()
        # 交易时段5分钟，非交易时段30分钟
        now = time.localtime(time.time() + 8*3600)
        is_trading = 9 <= now.tm_hour <= 15 and now.tm_wday < 5
        sleep_sec = 300 if is_trading else 1800
        time.sleep(sleep_sec)


# ============================================================
# API 路由
# ============================================================

@app.route("/api/data")
def api_data():
    """溢价排行数据"""
    if not cache["data"]:
        # 首次访问，先刷新
        update_cache()
    
    data = cache["data"]
    if not data:
        return jsonify({"error": "数据未就绪", "premium_list": []})
    
    lof_data = data.get("lof_data", {})
    yahoo = data.get("yahoo_quotes", {})
    futures = data.get("future_quotes", {})
    cny_rate = data.get("cny_rate")
    
    premium_list = []
    for code, info in lof_data.items():
        premium_list.append({
            "code": code,
            "name": info.get("name", ""),
            "official_premium": info.get("premium_official"),
            "fair_premium": info.get("premium_fair"),
            "realtime_premium": info.get("premium_realtime"),
            "official_nav": info.get("official_nav"),
            "nav_date": info.get("nav_date"),
        })
    
    def sort_key(f):
        return f.get("realtime_premium") or f.get("fair_premium") or f.get("official_premium") or 0
    
    premium_list.sort(key=sort_key, reverse=True)
    
    return jsonify({
        "timestamp": cache["timestamp"],
        "cny_rate": cny_rate,
        "yahoo": {k: v for k, v in yahoo.items()},
        "futures": {k: v for k, v in futures.items()},
        "count": len(premium_list),
        "premium_list": premium_list,
    })


@app.route("/api/fund/<code>")
def api_fund_detail(code):
    """单只基金详情"""
    if not cache["data"]:
        update_cache()
    
    data = cache["data"]
    if not data:
        return jsonify({"error": "数据未就绪"})
    
    lof_data = data.get("lof_data", {})
    info = lof_data.get(code)
    if not info:
        return jsonify({"error": f"基金 {code} 未找到"})
    
    fund_config = INDEX_MAP.get(code)
    
    # 找到对应指数和期货的Yahoo数据
    yahoo_data = None
    future_data = None
    if fund_config:
        idx_code = fund_config.index_code
        if idx_code:
            yahoo_data = data.get("yahoo_quotes", {}).get(idx_code)
        fut_code = fund_config.pair_future
        if fut_code:
            future_data = data.get("future_quotes", {}).get(fut_code)

    return jsonify({
        "code": code,
        "name": info.get("name", ""),
        "config": {
            "index_code": fund_config.index_code if fund_config else None,
            "index_name": fund_config.index_name if fund_config else None,
            "region": fund_config.region if fund_config else None,
            "position_ratio": fund_config.position_ratio if fund_config else None,
            "pair_future": fund_config.pair_future if fund_config else None,
        } if fund_config else None,
        "premium": {
            "official": info.get("premium_official"),
            "fair": info.get("premium_fair"),
            "realtime": info.get("premium_realtime"),
        },
        "nav": {
            "official": info.get("official_nav"),
            "date": info.get("nav_date"),
        },
        "yahoo": yahoo_data,
        "future": future_data,
        "cny_rate": data.get("cny_rate"),
    })


@app.route("/api/status")
def api_status():
    """服务状态"""
    return jsonify({
        "status": "ok",
        "cached_at": cache["timestamp"],
        "funds_count": len(cache.get("data", {}).get("lof_data", {}) or {}) if cache["data"] else 0,
        "updating": cache["updating"],
    })


# ============================================================
# 页面路由
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/fund/<code>")
def fund_detail(code):
    return render_template("detail.html", code=code)


@app.route("/status")
def status():
    api_status_data = api_status().get_json()
    return render_template("status.html", status=api_status_data)


# ============================================================
# 启动
# ============================================================

# 启动时立即刷新一次
update_cache()

# 启动后台定时更新
t = threading.Thread(target=cache_updater, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
