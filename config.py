"""
基金配置：LOF基金列表 — 仅LOF，不含ETF
数据来源 palmmicro.com（无敌哥）+ 手动补充
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class FundConfig:
    code: str                # A股代码 (如 SH501018)
    name: str                # 基金名称
    index_code: str          # 跟踪指数代码
    index_name: str          # 指数名称
    region: str              # 地区 (US, HK, CN, JP, EU, IN, etc.)
    currency: str            # 币种 (USD, HKD, CNY)
    position_ratio: float = 0.95  # 仓位
    pair_future: Optional[str] = None

# ===== 原油/油气 =====
OIL_FUNDS = [
    FundConfig("SH501018", "南方原油LOF", "CL", "原油期货", "US", "USD", position_ratio=0.95, pair_future="CL"),
    FundConfig("SZ160723", "嘉实原油LOF", "CL", "原油期货", "US", "USD", position_ratio=0.95, pair_future="CL"),
    FundConfig("SZ161129", "原油LOF易方达", "CL", "原油期货", "US", "USD", position_ratio=0.95, pair_future="CL"),
    FundConfig("SZ163208", "全球油气能源LOF", "XOP", "标普油气", "US", "USD", position_ratio=0.95),
    FundConfig("SZ162411", "华宝油气LOF", "XOP", "标普油气", "US", "USD", position_ratio=0.95),
]

# ===== 美股指数（LOF） =====
US_INDEX_LOFS = [
    FundConfig("SZ161130", "纳斯达克100LOF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SZ161125", "标普500LOF", "SPX", "标普500", "US", "USD", position_ratio=0.95, pair_future="ES"),
    FundConfig("SH501312", "海外科技LOF", "QQQ", "海外科技", "US", "USD", position_ratio=0.95),
]

# ===== 中概互联 =====
CHINA_INTERNET_LOFS = [
    FundConfig("SZ164906", "中概互联网LOF", "KWEB", "中证海外中国互联网", "US", "USD", position_ratio=0.95),
]

# ===== 消费 =====
CONSUMER_LOFS = [
    FundConfig("SZ162415", "美国消费LOF", "XLY", "标普美国消费", "US", "USD", position_ratio=0.95),
]

# ===== 恒生/港股 =====
HK_LOFS = [
    FundConfig("SZ164705", "恒生LOF", "HSI", "恒生指数", "HK", "HKD", position_ratio=0.95),
    FundConfig("SH501302", "恒生指数基金LOF", "HSI", "恒生指数", "HK", "HKD", position_ratio=0.95),
    FundConfig("SZ160924", "恒生指数LOF", "HSI", "恒生指数", "HK", "HKD", position_ratio=0.95),
    FundConfig("SZ161124", "港股小盘LOF", "HSI", "港股小盘", "HK", "HKD", position_ratio=0.95),
]

# ===== 黄金/商品 =====
COMMODITY_LOFS = [
    FundConfig("SZ160719", "嘉实黄金LOF", "GC", "黄金", "US", "USD", position_ratio=0.95),
    FundConfig("SZ161116", "黄金主题LOF", "GC", "黄金", "US", "USD", position_ratio=0.95),
    FundConfig("SZ164701", "黄金LOF", "GC", "黄金", "US", "USD", position_ratio=0.95),
    FundConfig("SZ160216", "国泰商品LOF", "CCI", "大宗商品", "US", "USD", position_ratio=0.95),
    FundConfig("SZ165513", "中信保诚商品LOF", "CCI", "大宗商品", "US", "USD", position_ratio=0.95),
    FundConfig("SZ161815", "抗通胀LOF", "TIP", "抗通胀债券", "US", "USD", position_ratio=0.95),
]

# ===== 新兴市场 =====
EMERGING_LOFS = [
    FundConfig("SZ164824", "印度基金LOF", "SENSEX", "孟买SENSEX", "IN", "INR", position_ratio=0.95),
]

# ===== 全部LOF列表 =====
ALL_LOFS = (
    OIL_FUNDS
    + US_INDEX_LOFS
    + CHINA_INTERNET_LOFS
    + CONSUMER_LOFS
    + HK_LOFS
    + COMMODITY_LOFS
    + EMERGING_LOFS
)

# 索引映射（A股代码 → 配置）
INDEX_MAP = {f.code: f for f in ALL_LOFS}

# Yahoo Finance 符号映射（仅LOF基金有对应指数的）
YAHOO_SYMBOLS = {
    "NDX": "^NDX",
    "SPX": "^GSPC",
    "HSI": "^HSI",
    "HSTECH": "^HSTECH",
    "SENSEX": "^BSESN",
    "XOP": "XOP",
    "XLY": "XLY",
    "KWEB": "KWEB",
    "QQQ": "QQQ",
}

# 期货符号
FUTURE_YAHOO_SYMBOLS = {
    "NQ": "NQ=F",
    "ES": "ES=F",
    "CL": "CL=F",
}
