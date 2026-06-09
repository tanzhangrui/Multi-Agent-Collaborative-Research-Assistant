"""输入安全护栏 - 对用户输入进行安全校验"""
import re
from typing import Tuple, Optional


BLOCKED_PATTERNS = [
    (r'(?:忽略|无视|跳过).*(?:指令|规则|限制|约束)', '提示注入攻击检测'),
    (r'(?:pretend|ignore|override|bypass).*(?:instruction|rule|constraint)', 'Prompt injection detected'),
    (r'你(?:现在|必须|应该).*(?:是|成为|扮演).*(?:黑客|恶意|攻击)', '恶意角色扮演检测'),
]

MAX_INPUT_LENGTH = 2000
MIN_INPUT_LENGTH = 1


async def validate_input(text: str) -> Tuple[bool, Optional[str]]:
    """校验用户输入是否安全合规

    Returns:
        (is_valid, error_message)
    """
    if not text or len(text.strip()) < MIN_INPUT_LENGTH:
        return False, "输入内容不能为空"

    if len(text) > MAX_INPUT_LENGTH:
        return False, f"输入内容过长，请控制在{MAX_INPUT_LENGTH}字以内"

    # 检测提示注入攻击
    for pattern, desc in BLOCKED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"输入内容未通过安全检查：{desc}"

    return True, None
