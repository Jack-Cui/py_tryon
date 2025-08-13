import json
import hmac
import base64
import time
import uuid
import requests
from dataclasses import dataclass, field
from typing import List, Optional
from demo import get_verify_code, send_token_request, endpoint, setup_logger, log_info

# 固定密钥
KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwxAKb+pGIdtg189rgCtLGClLVTcWkAga0UTiZ8cfDzNDBF3eZBX96iXb5godZLHaAg38OZbtqclZfWBu9nBEpaV+nZudJ5z42RFpJlK6p9ACetR+/rX5Xfol9k0DayI9lP42uyK8h+wv/LPcA5PT/eE4aSMwn2g/xrVuLPGpCXM5Ca3de8s6Rj5JdW2GccLsi3GueLet2N4+a88cvpNMr4poVu135cb+SyxEbt3/4z0HhTFM0QF+GLaw+3faT8A4peiiot4io1UCUyW8fRXIAiHv5J0s8Y3bJW311BZFs/jnAodiIvQKzh3pEMKMyo0kw0T7HF5G4oSe+6Dvn9AV6QIDAQAB"

logger = setup_logger()

def compute_hmac_sha256(message: str) -> str:
    """
    计算 HMAC-SHA256 并返回 Base64 编码结果
    """
    key_bytes = KEY.encode("utf-8")
    message_bytes = message.encode("utf-8")
    hmac_obj = hmac.new(key_bytes, message_bytes, digestmod="sha256")
    return base64.b64encode(hmac_obj.digest()).decode("utf-8")


@dataclass
class BalanceDeductionItem:
    deductionType: int
    billPrice: float
    sourceId: int
    reduceCount: int
    clotheId: int


@dataclass
class BalanceDeductionRaw:
    deducteList: List[BalanceDeductionItem] = field(default_factory=list)


def get_balance_deduction_request(
    balance_raw: BalanceDeductionRaw,
    access_token: str,
    user_id: int,
    web_host: str,
    callback_success: Optional[callable] = None
):
    url = f"{web_host}/admin/balance/deduction"

    #data = json.dumps(balance_raw, default=lambda o: o.__dict__)
    data = json.dumps(balance_raw, default=lambda o: o.__dict__, separators=(',', ':'))

    timestamp = str(int(time.time() * 1000))
    request_id = uuid.uuid4().hex

    s_message = f"{data}|{timestamp}|{user_id}"
    #  增加json对象去掉空格的处理，和服务端java方法json序列化结果保持一致
    #s_message.replace(" ", "")

    log_info(f"s_message: {s_message}")
    signature = compute_hmac_sha256(s_message)

    # timestamp = "1754650211157"
    # request_id = "7562911722694462bad0aa2a65b3ddda"
    # signature = "mTM/WYyhf5lRWcN8pK7Z22divNrfUazzwaew1hNTACo="
    # log_info(f"timestamp: {timestamp}, request_id: {request_id}, signature: {signature}", user_id=user_id)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "X-timestamp": timestamp,
        "X-requestId": request_id,
        "X-signature": signature,
    }
    #log_info(f"url: {url}, headers: {headers}, data: {json.dumps(balance_raw, default=lambda o: o.__dict__)}")
    log_info(f"url: {url}, headers: {headers}, data: {json.dumps(balance_raw, default=lambda o: o.__dict__, separators=(',', ':'))}")
    
    response = requests.post(url, headers=headers, data=data)

    if not response.ok:
        print(f"[BalanceManager] Error: {response.status_code} {response.text}")
        return

    try:
        json_data = response.json()
    except Exception as e:
        print(f"[BalanceManager] JSON parse error: {e}")
        return

    print("[BalanceManager] Json:", json_data)

    if json_data.get("code") == 0:
        account_balance = json_data["data"]["accountBalance"]
        if callback_success:
            callback_success(account_balance)
    elif json_data.get("code") == 1:
        print("[BalanceManager] 扣费异常")


if __name__ == "__main__":
    get_verify_code()
    log_info("*" * 50 + "获取验证码成功" + "*" * 50)
    # # # 登录
    res = send_token_request()
    access_token = res['access_token']
    balance_raw = BalanceDeductionRaw()
    balance_raw.deducteList.append(BalanceDeductionItem(deductionType=2, billPrice=0.3, sourceId=1939613403762253825, reduceCount=1, clotheId=0))
    get_balance_deduction_request(balance_raw, access_token, 1754092805389819906,
    endpoint, lambda x: print(x))