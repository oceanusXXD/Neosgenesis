import logging
from pathlib import Path
import sys
import os
logger = logging.getLogger(__name__)
# 指定 .env 文件路径（根据你的项目结构）
# 确保虚拟环境中的包能被找到
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)  # 避免覆盖已有环境变量
else:
    logger.warning(f"⚠️ 未找到 .env 文件: {env_path}")
print(env_path)