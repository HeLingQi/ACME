# ACME
项目基于 `https://github.com/MoeClub/ACME `，实现自动签发续订，上传到指定服务器，七牛云CDN，腾讯云CDN（有bug，待修）。

## GTS 授权
```
# 登录谷歌账户, 打开网址点击 Enable 按钮 (无需GCP账号,只需要能够访问谷歌的账户创建项目)
https://console.cloud.google.com/apis/library/publicca.googleapis.com
# 点开右上角的命令图标打开 Cloud Shell, 输入创建密钥命令
gcloud publicca external-account-keys create
# 使用 acme.py 进行授权后即可签发 GTS 证书
python3 acme.py -register -s google -mail "xyz@abc.com" -kid "<keyId>" -key "<hmacKey>"


# 选择GCP项目<可选>
gcloud config set project <project-name>
# 打开API权限<可选>
gcloud services enable publicca.googleapis.com

```


## 使用方法
最好将脚本放在 国外服务器的 /root 下
- 安装依赖，pip3 install -r requirements.txt
- 先配置 .env的通用密码和华为云的 key和 secret， 如过要上传到七牛云（-n）和腾讯云（-q），请先配置好七牛云和腾讯云的 AK 和 SK
- 配置 sign_sites.sh 脚本（这里存放要签发续订的网站）
- 最后配置 定时任务 `0 0 */7 * * cd /root/ACME && bash sign_sites.sh >> /root/ACME/sign.log 2>&1`
