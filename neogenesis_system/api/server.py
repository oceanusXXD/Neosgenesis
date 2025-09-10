#!/usr/bin/env python3
"""
Neogenesis System API 服务器启动脚本

这个脚本用于启动 Neogenesis System 的 FastAPI Web 服务。
提供了不同的启动模式和配置选项。
"""

import argparse
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    import uvicorn
    from neogenesis_system.api.main import app
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保已安装所需依赖:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def setup_logging(log_level: str = "INFO"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('api.log')
        ]
    )


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Neogenesis System API 服务器",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="服务器主机地址"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器端口"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载（开发模式）"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数量（生产模式）"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="日志级别"
    )
    
    parser.add_argument(
        "--access-log",
        action="store_true",
        help="启用访问日志"
    )
    
    parser.add_argument(
        "--ssl-keyfile",
        type=str,
        help="SSL 私钥文件路径"
    )
    
    parser.add_argument(
        "--ssl-certfile", 
        type=str,
        help="SSL 证书文件路径"
    )
    
    parser.add_argument(
        "--production",
        action="store_true",
        help="生产模式（禁用调试功能）"
    )
    
    return parser.parse_args()


def validate_ssl_files(keyfile: str = None, certfile: str = None):
    """验证 SSL 文件"""
    if keyfile and not os.path.exists(keyfile):
        print(f"❌ SSL 私钥文件不存在: {keyfile}")
        return False
    
    if certfile and not os.path.exists(certfile):
        print(f"❌ SSL 证书文件不存在: {certfile}")
        return False
    
    return True


def print_startup_info(host: str, port: int, ssl_enabled: bool = False):
    """打印启动信息"""
    protocol = "https" if ssl_enabled else "http"
    print("\n" + "="*60)
    print("🚀 Neogenesis System API 服务器启动中...")
    print("="*60)
    print(f"📡 服务地址: {protocol}://{host}:{port}")
    print(f"📚 API 文档: {protocol}://{host}:{port}/docs")
    print(f"📖 ReDoc 文档: {protocol}://{host}:{port}/redoc")
    print(f"🔍 健康检查: {protocol}://{host}:{port}/health")
    print("="*60)
    print("按 Ctrl+C 停止服务器")
    print()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 验证 SSL 文件（如果提供）
    if args.ssl_keyfile or args.ssl_certfile:
        if not validate_ssl_files(args.ssl_keyfile, args.ssl_certfile):
            sys.exit(1)
        ssl_enabled = True
    else:
        ssl_enabled = False
    
    # 打印启动信息
    print_startup_info(args.host, args.port, ssl_enabled)
    
    # 准备 uvicorn 配置
    uvicorn_config = {
        "app": app,
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "access_log": args.access_log,
    }
    
    # SSL 配置
    if ssl_enabled:
        uvicorn_config.update({
            "ssl_keyfile": args.ssl_keyfile,
            "ssl_certfile": args.ssl_certfile,
        })
    
    # 开发/生产模式配置
    if args.production:
        # 生产模式
        logger.info("🏭 以生产模式启动")
        uvicorn_config.update({
            "workers": args.workers if args.workers > 1 else 1,
            "reload": False,
        })
    else:
        # 开发模式
        logger.info("🔧 以开发模式启动")
        uvicorn_config.update({
            "reload": args.reload,
            "reload_dirs": [str(project_root)],
        })
    
    try:
        # 启动服务器
        uvicorn.run(**uvicorn_config)
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
