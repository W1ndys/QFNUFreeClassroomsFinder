import time
import hmac
import hashlib
import base64
import requests
import json


def feishu(title: str, content: str) -> dict:
    """
    发送飞书机器人消息

    Args:
        webhook_url: 飞书机器人的webhook地址
        secret: 安全设置中的签名校验密钥
        title: 消息标题
        content: 消息内容

    Returns:
        dict: 接口返回结果
    """
    feishu_webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/b6ee8f67-e8c3-466b-8fcb-5a5d25ce8f14"
    feishu_secret = "dot1PCzKFDwYl0jrZWDnHe"
    timestamp = str(int(time.time()))

    # 计算签名
    string_to_sign = f"{timestamp}\n{feishu_secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode("utf-8")

    # 构建请求头
    headers = {"Content-Type": "application/json"}

    # 构建消息内容
    msg = {
        "timestamp": timestamp,
        "sign": sign,
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [[{"tag": "text", "text": content}]],
                }
            }
        },
    }

    # 发送请求
    try:
        if not isinstance(feishu_webhook, str):
            return {"error": "飞书webhook未配置"}
        response = requests.post(feishu_webhook, headers=headers, data=json.dumps(msg))
        return response.json()
    except Exception as e:
        return {"error": str(e)}
