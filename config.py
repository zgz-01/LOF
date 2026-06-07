"""
基金配置：指数映射、仓位、类型
此配置参考 palmmicro.com 源码中的 QdiiGetEstArray() 和相关函数
"""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FundConfig:
    code: str                # A股代码 (如 SH513100)
    name: str                # 基金名称
    index_code: str          # 跟踪指数代码 (如 NDX, SPX)
    index_name: str          # 指数名称 (如 纳斯达克100)
    region: str              # 地区 (US, HK, JP, EU, IN, etc.)
    currency: str            # 币种 (USD, HKD, JPY, EUR)
    position_ratio: float    # 仓位 (LOF~0.95, ETF~1.0)
    is_lof: bool = True      # 是否为 LOF（影响仓位默认值）
    pair_future: Optional[str] = None  # 期货代码 (如 NQ, ES)

# ===== 纳斯达克100 =====
NASDAQ_FUNDS = [
    FundConfig("SH513100", "纳指ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SH513110", "纳指ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SH513390", "纳指100ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SH513870", "纳指ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SZ159501", "纳指ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SZ159513", "纳斯达克100ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SZ159632", "纳斯达克ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SZ159660", "纳指ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SZ159696", "纳指ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SZ159941", "纳指ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SZ161130", "纳斯达克100LOF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
    FundConfig("SH513300", "纳斯达克ETF", "NDX", "纳斯达克100", "US", "USD", position_ratio=0.95, pair_future="NQ"),
]

# ===== 标普500 =====
SP500_FUNDS = [
    FundConfig("SH513500", "标普500ETF", "SPX", "标普500", "US", "USD", position_ratio=0.95, pair_future="ES"),
    FundConfig("SH513650", "标普500ETF", "SPX", "标普500", "US", "USD", position_ratio=0.95, pair_future="ES"),
    FundConfig("SZ159612", "标普500ETF", "SPX", "标普500", "US", "USD", position_ratio=0.95, pair_future="ES"),
    FundConfig("SZ161125", "标普500LOF", "SPX", "标普500", "US", "USD", position_ratio=0.95, pair_future="ES"),
    FundConfig("SZ159655", "标普500ETF", "SPX", "标普500", "US", "USD", position_ratio=0.95, pair_future="ES"),
]

# ===== 中概互联 =====
CHINA_INTERNET_FUNDS = [
    FundConfig("SH513050", "中概互联ETF", "KWEB", "中证海外中国互联网", "US", "USD", position_ratio=0.95, pair_future=None),
    FundConfig("SZ164906", "中概互联网LOF", "KWEB", "中证海外中国互联网", "US", "USD", position_ratio=0.95, pair_future=None),
]

# ===== 恒生科技/港股 =====
HK_FUNDS = [
    FundConfig("SH513180", "恒生科技ETF", "HSTECH", "恒生科技指数", "HK", "HKD", position_ratio=0.95, pair_future=None),
    FundConfig("SZ159740", "恒生科技ETF", "HSTECH", "恒生科技指数", "HK", "HKD", position_ratio=0.95, pair_future=None),
    FundConfig("SH513660", "恒生ETF", "HSI", "恒生指数", "HK", "HKD", position_ratio=0.95, pair_future=None),
    FundConfig("SZ159920", "恒生ETF", "HSI", "恒生指数", "HK", "HKD", position_ratio=0.95, pair_future=None),
]

# ===== 日经225 =====
JAPAN_FUNDS = [
    FundConfig("SH513000", "日经ETF", "NIKKEI225", "日经225", "JP", "JPY", position_ratio=0.95, pair_future=None),
    FundConfig("SH513520", "日经ETF", "NIKKEI225", "日经225", "JP", "JPY", position_ratio=0.95, pair_future=None),
    FundConfig("SH513880", "日经ETF", "NIKKEI225", "日经225", "JP", "JPY", position_ratio=0.95, pair_future=None),
]

# ===== 欧洲 =====
EUROPE_FUNDS = [
    FundConfig("SH513030", "德国ETF", "DAX", "德国DAX", "EU", "EUR", position_ratio=0.95, pair_future=None),
    FundConfig("SH513080", "法国CAC40ETF", "CAC40", "法国CAC40", "EU", "EUR", position_ratio=0.95, pair_future=None),
]

# ===== 其他 =====
OTHER_FUNDS = [
    FundConfig("SZ159513", "印度基金LOF", "SENSEX", "孟买SENSEX", "IN", "INR", position_ratio=0.95, pair_future=None),
    FundConfig("SZ164824", "印度市场", "SENSEX", "孟买SENSEX", "IN", "INR", position_ratio=0.95, pair_future=None),
    FundConfig("SZ162411", "华宝油气LOF", "XOP", "标普油气", "US", "USD", position_ratio=0.95, pair_future="CL"),
    FundConfig("SH513350", "标普油气ETF", "XOP", "标普油气", "US", "USD", position_ratio=0.95, pair_future="CL"),
    FundConfig("SZ162415", "美国消费LOF", "XLY", "标普美国消费", "US", "USD", position_ratio=0.95, pair_future=None),
]

# ===== 全部基金列表 =====
ALL_FUNDS = NASDAQ_FUNDS + SP500_FUNDS + CHINA_INTERNET_FUNDS + HK_FUNDS + JAPAN_FUNDS + EUROPE_FUNDS + OTHER_FUNDS

# 索引映射
INDEX_MAP = {f.code: f for f in ALL_FUNDS}

# 期货到指数的映射 (用于实时EST计算)
FUTURE_TO_INDEX = {
    "NQ": "NDX",
    "ES": "SPX",
    "CL": "XOP",
}

# Yahoo Finance 符号映射
YAHOO_SYMBOLS = {
    "NDX": "^NDX",
    "SPX": "^GSPC",
    "HSI": "^HSI",
    "HSTECH": "^HSTECH",
    "NIKKEI225": "^N225",
    "DAX": "^GDAXI",
    "CAC40": "^FCHI",
    "SENSEX": "^BSESN",
    "XOP": "XOP",
    "XLY": "XLY",
    "KWEB": "KWEB",
}

# 期货的 Yahoo Finance 符号
FUTURE_YAHOO_SYMBOLS = {
    "NQ": "NQ=F",      # E-mini Nasdaq-100 futures
    "ES": "ES=F",      # E-mini S&P 500 futures
    "CL": "CL=F",      # Crude oil futures
}

# 央行汇率符号（中国货币网）
# 用于从无敌哥网站获取USCNY中间价
CNY_SYMBOL = "USCNY"
