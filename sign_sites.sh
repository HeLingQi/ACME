#!/bin/bash

source /root/ACME/.env
cd /root/ACME

bash sign.sh -d helingqi.com --host helingqi.com -p "$COMMON_PASS" -q -n --port 22
bash sign.sh -d vip.cy -p "$COMMON_PASS"
