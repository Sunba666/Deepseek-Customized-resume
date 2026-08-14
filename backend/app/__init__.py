"""backend.app 包：resume-advisor 本地求职辅助后端。

本地优先：解析、脱敏、画像、风险核验、匹配、STAR 优化全部在本地完成；
LLM 仅当用户配置 API Key 时用于深度分析，否则规则引擎兜底。
"""
__version__ = "0.1.0"
