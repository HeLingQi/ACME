#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import argparse
import hashlib
import hmac
import json
import time
import os
from datetime import datetime
from http.client import HTTPSConnection

# 常量定义
SERVICE = "ssl"
HOST = "ssl.tencentcloudapi.com"
VERSION = "2019-12-05"


def sign(key, msg):
    """生成签名"""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def create_authorization_header(secret_id, secret_key, action, payload):
    """创建授权头部"""
    algorithm = "TC3-HMAC-SHA256"
    timestamp = int(time.time())
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

    canonical_request = (
        f"POST\n/\n\ncontent-type:application/json; charset=utf-8\n"
        f"host:{HOST}\nx-tc-action:{action.lower()}\n\n"
        f"content-type;host;x-tc-action\n{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
    )

    credential_scope = f"{date}/{SERVICE}/tc3_request"
    string_to_sign = (
        f"{algorithm}\n{timestamp}\n{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    secret_signing = sign(sign(sign(f"TC3{secret_key}".encode("utf-8"), date), SERVICE), "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"{algorithm} Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders=content-type;host;x-tc-action, Signature={signature}"
    )

    return authorization, timestamp


def send_https_request(headers, payload):
    """发送 HTTPS 请求并返回响应"""
    conn = None
    try:
        conn = HTTPSConnection(HOST)
        conn.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
        response = conn.getresponse()
        return json.loads(response.read().decode())
    except Exception as err:
        print(f"请求错误: {err}")
    finally:
        conn.close()


def describe_certificates(secret_id, secret_key, domain):
    """获取证书资源"""
    action = "DescribeCertificates"
    payload = json.dumps({
        "SearchKey": domain,
        "ExpirationSort": "ASC",
        "FilterSource": "upload"
    })
    authorization, timestamp = create_authorization_header(secret_id, secret_key, action, payload)
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8",
        "Host": HOST,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": VERSION
    }
    try:
        response = send_https_request(headers, payload)
        return response.get('Response', {}).get('Certificates', [{}])[0].get('CertificateId')
    except Exception as err:
        print(err)
        return None


def update_certificate(secret_id, secret_key, old_certificate_id, cert_public_key, cert_private_key):
    """更新证书实例"""
    action = "UpdateCertificateInstance"
    payload = json.dumps({
        "OldCertificateId": old_certificate_id,
        "ResourceTypes": [
            'clb', 'cdn', 'waf', 'live', 'ddos', 'teo', 'apigateway', 'vod',
            'tke', 'tcb', 'tse', 'cos'
        ],
        "CertificatePublicKey": cert_public_key,
        "CertificatePrivateKey": cert_private_key,
    })

    authorization, timestamp = create_authorization_header(secret_id, secret_key, action, payload)
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8",
        "Host": HOST,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": VERSION
    }
    resp = send_https_request(headers, payload)
    print('证书上传结果', resp)


def main():
    parser = argparse.ArgumentParser(description='Upload certificate to Tencent Cloud.')
    parser.add_argument('-d', '--domain', required=True, help='Domain name')
    args = parser.parse_args()

    cert_path = f"/root/ACME/acme/crt/{args.domain}/server.crt.pem"
    key_path = f"/root/ACME/acme/crt/{args.domain}/server.key.pem"

    try:
        with open(cert_path, 'r') as cert_file:
            cert_public_key = cert_file.read()
        with open(key_path, 'r') as key_file:
            cert_private_key = key_file.read()
    except FileNotFoundError as e:
        print(f"文件错误: {e}")
        return

    print('开始获取旧资源ID信息')
    old_certificate_id = describe_certificates(secret_id, secret_key, args.domain)
    print('旧资源ID：' + old_certificate_id)
    if old_certificate_id:
        print('开始上传证书')
        update_certificate(secret_id, secret_key, old_certificate_id, cert_public_key, cert_private_key)


if __name__ == "__main__":
    # 这里的key 从.env文件中获取
    secret_id = os.getenv("TENCENT_SECRET_ID")
    secret_key = os.getenv("TENCENT_SECRET_KEY")
    main()
