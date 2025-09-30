"""
微信公众号文章爬取工具
"""

from .mp_client import WeChatMPClient
from .config import get_config

__version__ = "1.0.0"
__all__ = ["WeChatMPClient", "get_config"]