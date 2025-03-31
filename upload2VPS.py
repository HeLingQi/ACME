import paramiko
import argparse
import os


def transfer_files(domain, port, username, password, host=None):
    local_crt_path = f"/root/ACME/acme/crt/{domain}/server.crt.pem"
    local_key_path = f"/root/ACME/acme/crt/{domain}/server.key.pem"
    # remote_crt_path = f"/etc/nginx/ssl/{domain}.crt"
    # remote_key_path = f"/etc/nginx/ssl/{domain}.key"
    remote_paths = [
        (f"/etc/nginx/ssl/{domain}.crt", f"/etc/nginx/ssl/{domain}.key"),
        (f"/usr/local/nginx/conf/ssl/{domain}.crt", f"/usr/local/nginx/conf/ssl/{domain}.key")
    ]

    # 创建 SSH 客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if host is None:
        host = domain
    try:
        # 连接到远程服务器
        ssh.connect(host, port=port, username=username, password=password)

        # 检查路径有效性
        remote_crt_path = None
        remote_key_path = None
        for crt_path, key_path in remote_paths:
            stdin, stdout, stderr = ssh.exec_command(f"ls {os.path.dirname(crt_path)}")
            if not stderr.read().strip():  # 如果目录存在
                remote_crt_path, remote_key_path = crt_path, key_path
                break
        
        if not remote_crt_path or not remote_key_path:
            print("无法找到有效的远程路径，确保远程服务器有 /etc/nginx/ssl 或 /usr/local/nginx/conf/ssl/ 目录。")
            return

        # 使用 SFTP 传输文件
        sftp = ssh.open_sftp()
        sftp.put(local_crt_path, remote_crt_path)
        sftp.put(local_key_path, remote_key_path)
        sftp.close()

        # 重载 Nginx
        stdin, stdout, stderr = ssh.exec_command('/etc/init.d/nginx reload')
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if error:
            # 如果 `/etc/init.d/nginx` 失败，尝试 `service`
            stdin, stdout, stderr = ssh.exec_command('service nginx reload')
            output = stdout.read().decode()
            error = stderr.read().decode()

        print(output)
        print(error)

    except Exception as e:

        print(f"发生错误: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="上传 SSL 证书并刷新 Nginx")
    parser.add_argument('-d', '--domain', required=True, help="域名，例如：helingqi.com")
    parser.add_argument('-port', '--port', type=int, default=2323, help="SSH 端口，默认为 2323")
    parser.add_argument('-u', '--username', required=True, help="SSH 用户名")
    parser.add_argument('-p', '--password', required=True, help="SSH 密码")
    parser.add_argument('-H', '--host', help="主机名，如果未提供，则默认为 -d 的值")

    args = parser.parse_args()
    # 如果 -h 未提供，则使用 -d 的值
    if not args.host:
        args.host = args.domain

    transfer_files(args.domain, args.port, args.username, args.password, args.host)
