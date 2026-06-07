"""
核心计算引擎 — 移植自 palmmicro.com (无敌哥) 的 PHP 代码
实现了三级EST计算:
  - 官方EST (Official): 基于T日跟踪指数净值 + T日央行中间价
  - 参考EST (Fair): 基于最新可用数据
  - 实时EST (Realtime): 基于期货实时价格

核心公式:
  calibration_factor = est_netvalue * cny_rate / official_nav
  estimated_nav = est_current * cny_current / calibration_factor
  premium = (price - estimated_nav) / estimated_nav * 100
"""
from dataclasses import dataclass
from typing import Optional

from config import FundConfig, INDEX_MAP


# ============================================================
# 仓位调整 (Position Adjustment)
# ============================================================
# LOF基金通常不满仓操作，需要根据仓位比例调整估值
# AdjustPosition(fVal) = ratio * fVal + (1 - ratio) * baseVal
# 其中 baseVal = 上一次校准时的基准值

def fund_adjust_position(ratio: float, val: float, old_val: float) -> float:
    """
    仓位调整函数
    来自 PHP: FundAdjustPosition($fRatio, $fVal, $fOldVal)
    公式: ratio * val + (1 - ratio) * old_val
    """
    return ratio * val + (1.0 - ratio) * old_val


def fund_reverse_adjust_position(ratio: float, val: float, old_val: float) -> float:
    """
    仓位反向调整
    来自 PHP: FundReverseAdjustPosition($fRatio, $fVal, $fOldVal)
    """
    return val / ratio - old_val * (1.0 / ratio - 1.0)


# ============================================================
# QDII 估值计算
# ============================================================

def qdii_get_calibration(est_val: float, cny_rate: float, nav: float) -> float:
    """
    计算校准因子 (Calibration Factor)
    公式: est_val * cny_rate / nav
    含义: 跟踪标的在人民币计价下的价值 / 官方净值
    来自 PHP: QdiiGetCalibration($strEst, $strCNY, $strNetValue)
    """
    return est_val * cny_rate / nav


def qdii_get_val(est_val: float, cny_rate: float, factor: float) -> float:
    """
    根据校准因子计算估算净值
    公式: est_val * cny_rate / factor
    来自 PHP: QdiiGetVal($fEst, $fCny, $fFactor)
    """
    return est_val * cny_rate / factor


def qdii_get_peer_val(qdii_val: float, cny_rate: float, factor: float) -> float:
    """
    反向计算：从估算净值反推跟踪标的价格
    公式: qdii_val * factor / cny_rate
    来自 PHP: QdiiGetPeerVal($fQdii, $fCny, $fFactor)
    """
    return qdii_val * factor / cny_rate


# ============================================================
# 溢价率计算主逻辑
# ============================================================

@dataclass
class FundEstimate:
    """单只基金的估算结果"""
    code: str
    name: str
    price: float                 # 场内交易价格
    price_time: str              # 价格时间
    
    official_nav: float          # 官方EST净值
    official_date: str           # 官方EST日期
    official_premium: float      # 官方EST溢价率(%)
    
    fair_nav: Optional[float] = None     # 参考EST净值
    fair_premium: Optional[float] = None # 参考EST溢价率(%)
    
    realtime_nav: Optional[float] = None     # 实时EST净值
    realtime_premium: Optional[float] = None # 实时EST溢价率(%)
    
    calibration_factor: Optional[float] = None  # 校准因子
    position_ratio: float = 0.95               # 仓位
    
    # 原始数据（调试用）
    est_price: Optional[float] = None       # 跟踪标的当前价格
    cny_rate: Optional[float] = None        # 当前汇率
    
    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "price": self.price,
            "price_time": self.price_time,
            "official_nav": self.official_nav,
            "official_date": self.official_date,
            "official_premium": round(self.official_premium, 2),
            "fair_nav": round(self.fair_nav, 4) if self.fair_nav else None,
            "fair_premium": round(self.fair_premium, 2) if self.fair_premium else None,
            "realtime_nav": round(self.realtime_nav, 4) if self.realtime_nav else None,
            "realtime_premium": round(self.realtime_premium, 2) if self.realtime_premium else None,
            "position_ratio": self.position_ratio,
        }


def calculate_estimates(
    fund: FundConfig,
    price: float,
    price_time: str,
    est_current: float,       # 跟踪标的最新价格/净值
    est_date: str,            # 跟踪标的日期
    cny_rate: float,          # 当前美元中间价
    official_nav: float,      # 最近一期官方净值
    official_nav_date: str,   # 官方净值日期
    calibration_factor: Optional[float] = None,  # 校准因子 (None则自动计算)
    prev_nav: Optional[float] = None,   # 上一次校准时的净值
    future_price: Optional[float] = None,  # 期货价格 (用于实时EST)
) -> FundEstimate:
    """
    计算一只基金的完整三级EST估值
    """
    # === 第1步：确定校准因子 ===
    if calibration_factor is None and est_current and cny_rate and official_nav:
        # 自动计算校准因子
        calibration_factor = qdii_get_calibration(est_current, cny_rate, official_nav)
    
    result = FundEstimate(
        code=fund.code,
        name=fund.name,
        price=price,
        price_time=price_time,
        official_nav=official_nav,
        official_date=official_nav_date,
        official_premium=0,
        position_ratio=fund.position_ratio,
        est_price=est_current,
        cny_rate=cny_rate,
        calibration_factor=calibration_factor,
    )
    
    if not calibration_factor or calibration_factor == 0:
        result.official_premium = 0
        return result
    
    # === 第2步：计算官方EST ===
    # 使用T日跟踪标的净值 + T日央行中间价
    official_est = qdii_get_val(est_current, cny_rate, calibration_factor)
    # 仓位调整
    base_val = prev_nav or official_est
    official_est_adjusted = fund_adjust_position(fund.position_ratio, official_est, base_val)
    result.official_nav = round(official_est_adjusted, 4)
    result.official_premium = (price - official_est_adjusted) / official_est_adjusted * 100
    
    # === 第3步：计算参考EST ===
    # 使用最新汇率 + 最新指数价格
    result.fair_nav = result.official_nav  # 默认与官方EST一致
    result.fair_premium = result.official_premium
    
    # === 第4步：计算实时EST（如果有期货数据）===
    if future_price is not None:
        # 期货价格到跟踪标的的映射
        # 对于美股指数基金：期货本身就是跟踪标的
        future_est = qdii_get_val(future_price, cny_rate, calibration_factor)
        future_est_adjusted = fund_adjust_position(fund.position_ratio, future_est, base_val)
        result.realtime_nav = round(future_est_adjusted, 4)
        result.realtime_premium = (price - future_est_adjusted) / future_est_adjusted * 100
    
    return result
