#!/bin/bash

# 显示帮助信息
show_help() {
  echo "用法: $0 -d domain.com [-p 密码] [--host 主机名] [-P 端口] [-q] [-n]"
  echo
  echo "选项:"
  echo "  -d, --domain  域名，例如: domain.com"
  echo "  --host        主机名，如果未提供，则默认为域名"
  echo "  -p            密码（可选），执行 upload2VPS.py"
  echo "  -P, --port    端口号（可选），默认值为 2323"
  echo "  -q, --qcloud  执行 upload2QCloud.py"
  echo "  -n, --qiniu   执行 upload2Qiniu.py"
  echo "  -h, --help    显示帮助信息"
}

# 初始化变量
DOMAIN=""
PASSWORD=""
HOST=""
PORT=2323
UPLOAD_QCLOUD=false
UPLOAD_QINIU=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    -d|--domain)
      DOMAIN="$2"
      shift 2
      ;;
    -p)
      PASSWORD="$2"
      shift 2
      ;;
    -H|--host)
      HOST="$2"
      shift 2
      ;;
    -P|--port)
      PORT="$2"
      shift 2
      ;;
    -q|--qcloud)
      UPLOAD_QCLOUD=true
      shift
      ;;
    -n|--qiniu)
      UPLOAD_QINIU=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "未知选项: $1"
      show_help
      exit 1
      ;;
  esac
done

# 检查是否提供了域名
if [ -z "$DOMAIN" ]; then
  echo "错误: 必须使用 -d 提供域名"
  show_help
  exit 1
fi

# 验证域名格式
if ! [[ "$DOMAIN" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
  echo "错误: 无效的域名格式: $DOMAIN"
  exit 1
fi

# 如果未提供主机名，则默认为域名
if [ -z "$HOST" ]; then
  HOST="$DOMAIN"
fi

# 执行主要逻辑
echo "执行 acme.py 脚本..."
python3 acme.py -d "$DOMAIN,*.${DOMAIN}" -v dns -s google -ecc

if [ -n "$PASSWORD" ]; then
  echo "上传文件到VPS..."
  python3 upload2VPS.py -d "$DOMAIN" -u root -p "$PASSWORD" --host "$HOST" --port "$PORT"
fi

if [ "$UPLOAD_QCLOUD" = true ]; then
  echo "上传文件到腾讯云..."
  python3 upload2QCloud.py -d "$DOMAIN"
fi

if [ "$UPLOAD_QINIU" = true ]; then
  echo "上传文件到七牛云..."
  python3 upload2Qiniu.py -d "$DOMAIN"
fi

echo "操作完成。"