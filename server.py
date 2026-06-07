"""
API 服务 — 在本机运行，定时抓取数据并缓存，供 Railway 网页调用

启动: python3 server.py
默认端口: 8080
"""
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta

from fetcher import fetch_all_data, fetch_palmmicro_lof_data, fetch_yahoo_quote, fetch_yahoo_future
from config import ALL_FUNDS, INDEX_MAP, YAHOO_SYMBOLS, FUTURE_YAHOO_SYMBOLS

BJ_TZ = timezone(timedelta(hours=8))

# ============================================================
# 缓存
# ============================================================
cache = {
    "data": None,
    "timestamp": None,
    "updating": False,
}


def update_cache():
    """刷新缓存"""
    if cache["updating"]:
        print("[Server] 已在更新中，跳过")
        return
    
    cache["updating"] = True
    try:
        print(f"[Server] 开始刷新数据...")
        data = fetch_all_data()
        
        # 补充Yahoo Finance数据 (只抓关键指数)
        yahoo_results = {}
        for name, symbol in YAHOO_SYMBOLS.items():
            try:
                quote = fetch_yahoo_quote(symbol)
                if quote:
                    yahoo_results[name] = quote
                    print(f"  Yahoo {name}: {quote['price']} ({quote['change_pct']}%)")
                time.sleep(0.5)  # 限速
            except Exception as e:
                print(f"  Yahoo {name} 失败: {e}")
        
        # 抓期货数据
        future_results = {}
        for name, symbol in FUTURE_YAHOO_SYMBOLS.items():
            try:
                quote = fetch_yahoo_future(symbol)
                if quote:
                    future_results[name] = quote
                    print(f"  期货 {name}: {quote['price']} ({quote['change_pct']}%)")
                time.sleep(0.5)
            except Exception as e:
                print(f"  期货 {name} 失败: {e}")
        
        data["yahoo_quotes"] = yahoo_results
        data["future_quotes"] = future_results
        
        cache["data"] = data
        cache["timestamp"] = datetime.now(BJ_TZ).isoformat()
        print(f"[Server] 刷新完成, {len(data.get('lof_data', {}) or {})} 只基金")
    except Exception as e:
        print(f"[Server] 刷新失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cache["updating"] = False


def cache_updater():
    """定时更新线程"""
    while True:
        update_cache()
        # 交易时段每5分钟更新一次，非交易时段每30分钟
        now = datetime.now(BJ_TZ)
        is_trading = 9 <= now.hour <= 15 and now.weekday() < 5
        sleep_sec = 300 if is_trading else 1800
        print(f"[Server] 下次更新: {sleep_sec//60} 分钟后")
        time.sleep(sleep_sec)


# ============================================================
# HTTP API
# ============================================================

class APIHandler(BaseHTTPRequestHandler):
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    
    def do_OPTIONS(self):
        self._send_json({})
    
    def do_GET(self):
        path = self.path
        
        if path == "/api/premium":
            # 返回所有基金的溢价排行
            self._handle_premium()
        elif path == "/api/funds":
            # 返回基金列表
            funds = [{"code": f.code, "name": f.name, "index": f.index_name} for f in ALL_FUNDS]
            self._send_json({"funds": funds})
        elif path.startswith("/api/fund/"):
            # 单只基金详情
            code = path.replace("/api/fund/", "")
            self._handle_fund_detail(code)
        elif path == "/api/status":
            # 服务状态
            self._send_json({
                "status": "ok",
                "cached_at": cache.get("timestamp"),
                "funds_count": len(cache.get("data", {}).get("lof_data", {}) or {}) if cache.get("data") else 0,
                "updating": cache["updating"],
            })
        elif path == "/api/refresh":
            # 手动触发刷新
            threading.Thread(target=update_cache, daemon=True).start()
            self._send_json({"message": "刷新已触发"})
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def _handle_premium(self):
        if not cache["data"]:
            self._send_json({"error": "数据未就绪", "premium_list": []})
            return
        
        data = cache["data"]
        lof_data = data.get("lof_data", {}) or {}
        yahoo = data.get("yahoo_quotes", {})
        futures = data.get("future_quotes", {})
        cny_rate = data.get("cny_rate")
        
        premium_list = []
        for code, info in lof_data.items():
            if info.get("premium_official") is None and info.get("premium_fair") is None:
                continue
            
            premium_list.append({
                "code": code,
                "name": info.get("name", ""),
                "official_premium": info.get("premium_official"),
                "fair_premium": info.get("premium_fair"),
                "realtime_premium": info.get("premium_realtime"),
                "official_nav": info.get("official_nav"),
                "nav_date": info.get("nav_date"),
            })
        
        # 按实时溢价排序（优先），无实时则按参考溢价
        def sort_key(f):
            return f.get("realtime_premium") or f.get("fair_premium") or f.get("official_premium") or 0
        
        premium_list.sort(key=sort_key, reverse=True)
        
        self._send_json({
            "timestamp": data.get("timestamp"),
            "cached_at": cache.get("timestamp"),
            "cny_rate": cny_rate,
            "yahoo": yahoo,
            "futures": futures,
            "count": len(premium_list),
            "premium_list": premium_list,
        })
    
    def _handle_fund_detail(self, code: str):
        if not cache["data"]:
            self._send_json({"error": "数据未就绪"})
            return
        
        lof_data = (cache["data"].get("lof_data", {}) or {})
        info = lof_data.get(code)
        if not info:
            self._send_json({"error": f"基金 {code} 未找到"})
            return
        
        fund_config = INDEX_MAP.get(code)
        
        self._send_json({
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
            "yahoo": cache["data"].get("yahoo_quotes", {}).get(
                fund_config.index_code if fund_config else None),
            "future": cache["data"].get("future_quotes", {}).get(
                fund_config.pair_future if fund_config else None),
            "cny_rate": cache["data"].get("cny_rate"),
        })
    
    def log_message(self, format, *args):
        print(f"[HTTP] {args[0]} {args[1]} {args[2]}")


def main():
    PORT = 8080
    
    # 先更新一次缓存
    print(f"[Server] 启动中，首次刷新数据...")
    update_cache()
    
    # 启动定时更新线程
    updater = threading.Thread(target=cache_updater, daemon=True)
    updater.start()
    
    # 启动HTTP服务
    server = HTTPServer(("0.0.0.0", PORT), APIHandler)
    print(f"[Server] API服务运行中 http://0.0.0.0:{PORT}")
    print(f"[Server] 接口:")
    print(f"  GET /api/premium    - 溢价排行")
    print(f"  GET /api/fund/<code> - 单只基金详情")
    print(f"  GET /api/status     - 服务状态")
    print(f"  GET /api/refresh    - 手动刷新")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] 关闭")
        server.shutdown()


if __name__ == "__main__":
    main()
