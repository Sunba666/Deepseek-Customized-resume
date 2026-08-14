"""隐私脱敏：正则 + 预设模式替换敏感信息。

覆盖：手机号、邮箱、身份证号、详细住址、座机号、银行卡号。
导出文件默认经过脱敏，符合「本地优先 + 匿名分享」。
"""
import re

# 手机号（中国大陆 1[3-9]\d{9}），保留前3后4
_PHONE = re.compile(r"(?<!\d)(1[3-9]\d)(\d{4})(\d{4})(?!\d)")

# 身份证号（18位，含X）
_ID = re.compile(r"(?<!\d)(\d{6})(\d{8})(\d{3}[\dXx])(?!\d)")

# 邮箱
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")

# 座机（含区号）
_TEL = re.compile(r"(?<!\d)(0\d{2,3})-?(\d{7,8})(?!\d)")

# 银行卡（13-19位数字）
_BANK = re.compile(r"(?<!\d)(\d{4})(\d{9,13})(\d{4})(?!\d)")

# 详细住址：省市区 + 街道/路/号/小区/楼/室
_ADDRESS = re.compile(
    r"((?:[\u4e00-\u9fa5]{2,}(?:省|自治区|市))?"
    r"(?:[\u4e00-\u9fa5]{2,}(?:市|区|县))?"
    r"(?:[\u4e00-\u9fa5]{2,}(?:路|街|大道|巷))?"
    r"(?:\d+号)?(?:[\u4e00-\u9fa5]{0,8}(?:小区|花园|公寓|大厦|写字楼)?)"
    r"(?:\d+栋?)?(?:\d+单元)?(?:\d+室|号)?)"
)

# 期望薪资里的数字不能误伤，地址匹配需宽松处理，故地址单独处理

_PHONE_REPL = r"\1****\3"
_ID_REPL = r"\1********\3"
_EMAIL_REPL = "[邮箱已隐藏]"
_TEL_REPL = r"\1****\2"
_BANK_REPL = r"\1********\3"


def redact(text: str) -> str:
    """对文本做脱敏，返回替换后的文本。"""
    if not text:
        return text
    text = _PHONE.sub(_PHONE_REPL, text)
    text = _ID.sub(_ID_REPL, text)
    text = _EMAIL.sub(_EMAIL_REPL, text)
    text = _TEL.sub(_TEL_REPL, text)
    text = _BANK.sub(_BANK_REPL, text)
    # 地址：只隐藏省市区之后的部分过于激进，保守处理——仅当行内含"地址/住址/居住地"等关键词时替换整段
    lines = []
    for line in text.splitlines():
        if re.search(r"(地址|住址|居住地|现居|家庭住址)", line):
            line = _ADDRESS.sub("[住址已隐藏]", line)
        lines.append(line)
    return "\n".join(lines)


def extract_contact(text: str) -> dict:
    """提取联系方式预览（用于前端展示，导出时一律脱敏）。"""
    preview = {}
    m = _PHONE.search(text)
    if m:
        preview["phone"] = f"{m.group(1)}****{m.group(3)}"
    if _EMAIL.search(text):
        preview["email"] = "[邮箱已隐藏]"
    return preview
