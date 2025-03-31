# -*- coding: utf-8 -*-
import os
import sys
import requests
import datetime
from qiniu import Auth
import argparse
import time

def upload_certificate(auth, cert_domain, priv_key, chain_cert):
    upload_url = 'https://api.qiniu.com/sslcert'
    token = auth.token_of_request(upload_url)
    now_date = datetime.date.today().strftime("%Y%m%d")
    cert_data = {
        'name': f"{cert_domain}-{now_date}",
        'common_name': cert_domain,
        'pri': priv_key,
        'ca': chain_cert
    }
    headers = {
        'Authorization': f'QBox {token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(upload_url, json=cert_data, headers=headers).json()
    cert_id = response.get('certID')
    if not cert_id:
        print('Certificate upload failed!')
        sys.exit(1)
    return cert_id

# 获取这个域名相关的子域名
def get_subdomains(auth, domain):
    url = f"http://api.qiniu.com/domain?sourceTypes=qiniuBucket&sourceTypes=ip"
    token = auth.token_of_request(url)
    headers = {
        'Authorization': f'QBox {token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.get(url, headers=headers).json()
    domains = response.get('domains', [])
    subdomains = []
    for item in domains:
        if item.get('name').find(domain) != -1:
            subdomains.append(item.get('name'))
    print('获取相关子域名', subdomains)
    return subdomains    

def update_cdn_certificate(auth, cert_domain, cert_id):
    update_url = f'http://api.qiniu.com/domain/{cert_domain}/httpsconf'
    token = auth.token_of_request(update_url)
    data = {
        'certId': cert_id,
        'forceHttps': False,
        'http2Enable': True
    }
    headers = {
        'Authorization': f'QBox {token}',
        'Content-Type': 'application/json'
    }
    response = requests.put(update_url, json=data, headers=headers).json()
    print('更新CDN SSL证书',response)
    print('CDN SSL证书更新完成.')

def remove_subdomain(domain):
    parts = domain.split('.')
    # 确保域名至少有两个部分（主域和顶级域）
    if len(parts) > 2:
        return '.'.join(parts[-2:])
    return domain

# 获取证书
def get_certificate(auth, domain):
    url = f"http://api.qiniu.com/sslcert?limit=1000"
    token = auth.token_of_request(url)
    headers = {
        'Authorization': f'QBox {token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.get(url, headers=headers).json()
    for item in response.get('certs'):
        print('获取证书', item.get('certid'), item.get('name'), item.get('create_time'))
        # 创建时间
        create_time = item.get('create_time')
        certid = item.get('certid')
        # 如果创建时间是0天以前的, create_time是时间戳
        if create_time < int(time.time()):
            print('获取到证书', certid, item.get('name'), item.get('create_time'))
            delete_certificate(auth, certid)
            
# 删除证书
def delete_certificate(auth, certid):
    url = f"http://api.qiniu.com/sslcert/{certid}"
    token = auth.token_of_request(url)
    headers = {
        'Authorization': f'QBox {token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.delete(url, headers=headers).json()
    print('删除证书', certid, response)
    
    
    
def main():
    parser = argparse.ArgumentParser(description='Upload certificate to QiNiu.')
    parser.add_argument('-d', '--domain', required=True, help='Domain name')
    args = parser.parse_args()
    domain = remove_subdomain(args.domain)
    cert_path = f"/root/ACME/acme/crt/{domain}/server.crt.pem"
    key_path = f"/root/ACME/acme/crt/{domain}/server.key.pem"

    try:
        with open(cert_path, 'r') as cert_file:
            cert_public_key = cert_file.read()
        with open(key_path, 'r') as key_file:
            cert_private_key = key_file.read()
    except FileNotFoundError as e:
        print(f"文件错误: {e}")
        return
    auth = Auth(access_key, secret_key)
    args = parser.parse_args()

    cert_id = upload_certificate(auth, domain, cert_private_key, cert_public_key)
    # # 获取这个域名相关的子域名
    subdomains = get_subdomains(auth, domain)
    for subdomain in subdomains:
        update_cdn_certificate(auth, subdomain, cert_id)
        
    # 处理其他过期证书
    get_certificate(auth, domain)

if __name__ == "__main__":
    access_key = os.getenv("QINIU_ACCESS_KEY")
    secret_key = os.getenv("QINIU_SECRET_KEY")
    main()
