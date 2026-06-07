"""
数据抓取层 — 从多个源获取计算所需数据

数据源:
  1. 无敌哥网站 (palmmicro.com) → LOF基金场内价格、官方净值
  2. Yahoo Finance → 美股指数/期货实时价格
  3. 央行官网/无敌哥 → USCNY中间价
"""
import re
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Optional

BJ_TZ = timezone(timedelta(hours=8))
US_TZ = timezone(timedelta(hours=-4))  # EDT

# ============================================================
# 公用工具
# ============================================================

def fetch_url(url: str, timeout: int = 15) -> Optional[str]:
    """安全抓取URL"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[Fetcher] 抓取失败 {url[:60]}: {e}")
        return None


def safe_float(val) -> float:
    try:
        v = float(val)
        return v if v and v > 0 else 0.0
    except (ValueError, TypeError):
        return 0.0


# ============================================================
# 1. 从无敌哥网站抓取 LOF 基金基础数据
# ============================================================

PALMMICRO_LOF_URL = "https://www.palmmicro.com/woody/res/lofcn.php?sort=symbol"

def fetch_palmmicro_lof_data() -> Optional[dict]:
    """
    从无敌哥的LOF基金页面抓取数据
    返回: { code: { price, name, nav, nav_date, premium_official, premium_fair, premium_realtime }, ... }
    """
    html = fetch_url(PALMMICRO_LOF_URL)
    if not html:
        return None
    
    funds = {}
    
    # 找到EST表格
    est_start = html.find("id=\"estimationtable\"")
    if est_start == -1:
        print("[Fetcher] 未找到EST表格")
        return None
    
    tbody_start = html.find("<tbody>", est_start)
    tbody_end = html.find("</tbody>", tbody_start)
    if tbody_start == -1 or tbody_end == -1:
        return None
    
    tbody = html[tbody_start:tbody_end]
    
    for tr_match in re.finditer(r'<tr>(.*?)</tr>', tbody, re.DOTALL):
        tr_html = tr_match.group(1)
        
        # 基金名称
        name_match = re.search(r'title="([^"]*)"', tr_html)
        name = name_match.group(1) if name_match else ""
        
        # 基金代码
        code_match = re.search(r'>(SH\d{6}|SZ\d{6})<', tr_html)
        if not code_match:
            continue
        code = code_match.group(1)
        
        # 提取所有td
        tds = re.findall(r'<td[^>]*>(.*?)</td>', tr_html, re.DOTALL)
        
        def extract_text(td_html):
            return re.sub(r'<[^>]+>', '', td_html).strip()
        
        if len(tds) < 8:
            continue
        
        # 参考数据区（在EST表之前）也包含价格信息
        # 但EST表包含: code, name, official_nav, nav_date, premium_official, fair_nav, fair_premium, realtime_nav, realtime_premium
        official_nav_str = extract_text(tds[1]) if len(tds) > 1 else ""
        nav_date_str = extract_text(tds[2]) if len(tds) > 2 else ""
        premium_official_str = extract_text(tds[3]) if len(tds) > 3 else ""
        
        fair_nav_str = extract_text(tds[4]) if len(tds) > 4 else ""
        premium_fair_str = extract_text(tds[5]) if len(tds) > 5 else ""
        
        realtime_nav_str = extract_text(tds[6]) if len(tds) > 6 else ""
        premium_realtime_str = extract_text(tds[7]) if len(tds) > 7 else ""
        
        funds[code] = {
            "name": name,
            "official_nav": safe_float(official_nav_str),
            "nav_date": nav_date_str,
            "premium_official": safe_float(premium_official_str.replace("%", "")),
            "fair_nav": safe_float(fair_nav_str),
            "premium_fair": safe_float(premium_fair_str.replace("%", "")),
            "realtime_nav": safe_float(realtime_nav_str),
            "premium_realtime": safe_float(premium_realtime_str.replace("%", "")),
        }
    
    return funds


# ============================================================
# 2. 从无敌哥网站抓取单个基金的详细页面
# ============================================================

def fetch_fund_detail(code: str) -> Optional[dict]:
    """
    抓取单只基金详情页，获取价格、参考数据等
    如 https://www.palmmicro.com/woody/res/sh513100cn.php
    """
    url = f"https://www.palmmicro.com/woody/res/{code.lower()}cn.php"
    html = fetch_url(url, timeout=10)
    if not html:
        return None
    
    result = {
        "code": code,
        "price": None,
        "price_time": None,
        "ref_data": [],
    }
    
    # 在页面顶部的"参考数据"区域找价格
    ref_start = html.find("参考数据")
    if ref_start > 0:
        # 找到当前基金价格
        # 格式: <a href=...>code</a> 价格 涨幅 日期 时间 名称
        ref_section = html[ref_start:ref_start + 2000]
        # 找代码后面的数字
        price_match = re.search(rf'{code}[^<]*</a>(\d+\.\d+)([-\d.]+%)?(\d{{4}}-\d{{2}}-\d{{2}})(\d{{2}}:\d{{2}})', ref_section)
        if price_match:
            result["price"] = safe_float(price_match.group(1))
            result["price_time"] = f"{price_match.group(3)} {price_match.group(4)}"
    
    # 提取所有参考数据（指数、汇率等）
    ref_lines = re.findall(r'<a[^>]*>([^<]+)</a>\s*</td>\s*<td[^>]*>([^<]*)</td>', 
                          html[ref_start:ref_start + 3000])
    for name, val in ref_lines:
        result["ref_data"].append({"name": name.strip(), "value": val.strip()})
    
    return result


# ============================================================
# 3. 从Yahoo Finance抓取美股指数/期货数据
# ============================================================

YAHOO_QUERY = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

def fetch_yahoo_quote(symbol: str) -> Optional[dict]:
    """
    从Yahoo Finance获取实时报价
    返回: { price, change, change_pct, time }
    """
    url = YAHOO_QUERY.format(symbol=symbol)
    params = "?range=1d&interval=5m&includePrePost=true"
    
    data = fetch_url(url + params, timeout=10)
    if not data:
        return None
    
    try:
        j = json.loads(data)
        meta = j.get("chart", {}).get("result", [{}])[0].get("meta", {})
        regular_price = meta.get("regularMarketPrice")
        previous_close = meta.get("chartPreviousClose")
        trading_period = meta.get("currentTradingPeriod", {})
        
        if regular_price is None:
            return None
        
        change = (regular_price - previous_close) if previous_close else 0
        change_pct = (change / previous_close * 100) if previous_close else 0
        
        # 获取时间戳
        timestamp = meta.get("regularMarketTime")
        time_str = ""
        if timestamp:
            dt = datetime.fromtimestamp(timestamp, tz=US_TZ)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        
        return {
            "symbol": symbol,
            "price": regular_price,
            "previous_close": previous_close,
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "time": time_str,
        }
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"[Fetcher] Yahoo解析失败 {symbol}: {e}")
        return None


def fetch_yahoo_future(symbol: str) -> Optional[dict]:
    """获取期货数据 (使用Yahoo的期货符号如 NQ=F)"""
    return fetch_yahoo_quote(symbol)


# ============================================================
# 4. 从无敌哥网站获取中间价汇率
# ============================================================

def fetch_usd_cny_rate() -> Optional[float]:
    """
    从无敌哥网站获取美元人民币中间价 (USCNY)
    通常在参考数据表格中有 USDCNY / USCNY 等数据
    """
    # 从任意一个基金详情页抓取汇率
    url = "https://www.palmmicro.com/woody/res/sh513100cn.php"
    html = fetch_url(url, timeout=10)
    if not html:
        return None
    
    # 寻找 USCNY 或 USDCNY 汇率
    # USCNY6.8157（央行中间价，跟在USCNY文本后面）
    # USDCNY6.7878（新浪实时汇率）
    
    # 找央行中间价 USCNY
    # 页面中第一次出现 USCNY 是在 meta description 中
    # 第二次出现是在参考数据表格中
    
    # 找所有出现位置
    positions = [m.start() for m in re.finditer('USCNY', html)]
    
    for idx in positions:
        after = html[idx:idx+300]
        # 跳过meta description中的那次
        if 'meta' in after[:50] or 'description' in after[:50]:
            continue
        
        # 找font标签内的数字
        match = re.search(r'<font[^>]*>(6\.[\d]+|7\.[\d]+)</font>', after)
        if match:
            val = float(match.group(1))
            if 6.0 < val < 8.0:
                return val
        
        # 或者td标签内的数字
        match = re.search(r'<td[^>]*>(6\.[\d]+|7\.[\d]+)</td>', after)
        if match:
            val = float(match.group(1))
            if 6.0 < val < 8.0:
                return val
    
    # 备选: 找 USDCNY（新浪交易汇率）
    for idx in [m.start() for m in re.finditer('USDCNY', html)]:
        after = html[idx:idx+300]
        match = re.search(r'USDCNY(6\.[\d]+|7\.[\d]+)', after)
        if match:
            val = float(match.group(1))
            if 6.0 < val < 8.0:
                return val
    
    return None


# ============================================================
# 5. 从新浪API获取数据 (备用，国内数据源)
# ============================================================

def fetch_sina_us_stock(symbol: str) -> Optional[dict]:
    """
    从新浪获取美股数据 (备用)
    格式: var hq_str_gb_xop="XOP,..."
    """
    sina_symbol = symbol.lower()
    url = f"https://hq.sinajs.cn/list=gb_{sina_symbol}"
    data = fetch_url(url, timeout=10)
    if not data:
        return None
    
    # 解析新浪格式
    match = re.search(r'hq_str[^=]+="([^"]*)"', data)
    if not match:
        return None
    
    parts = match.group(1).split(",")
    if len(parts) < 30:
        return None
    
    return {
        "symbol": symbol,
        "name": parts[0],
        "price": safe_float(parts[1]),
        "prev_close": safe_float(parts[26]),
        "time": parts[25] if len(parts) > 25 else "",
    }


# ============================================================
# 批量获取所有数据
# ============================================================

def fetch_all_data() -> dict:
    """
    一次调用获取所有需要的原始数据
    返回: { lof_data, yahoo_quotes, cny_rate, timestamp }
    """
    result = {
        "timestamp": datetime.now(BJ_TZ).isoformat(),
        "lof_data": None,
        "yahoo_quotes": {},
        "cny_rate": None,
        "errors": [],
    }
    
    # 1. 从无敌哥抓LOF数据
    try:
        result["lof_data"] = fetch_palmmicro_lof_data()
        if result["lof_data"]:
            print(f"[Fetcher] 无敌哥数据: {len(result['lof_data'])} 只基金")
        else:
            result["errors"].append("无敌哥网站抓取失败")
    except Exception as e:
        result["errors"].append(f"无敌哥抓取异常: {e}")
    
    # 2. 获取汇率
    try:
        result["cny_rate"] = fetch_usd_cny_rate()
        if result["cny_rate"]:
            print(f"[Fetcher] USCNY汇率: {result['cny_rate']}")
    except Exception as e:
        result["errors"].append(f"汇率抓取异常: {e}")
    
    return result
