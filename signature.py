import hashlib
import random
import time

def make_sha256_signature(rand: int, ts: int, secret_key: str) -> str:
    """
    生成 SHA256 签名（与 Go 版本算法一致）
    
    :param rand: 随机数（需与请求中的 rand 参数一致）
    :param ts: 时间戳（需与请求中的 ts 参数一致）
    :param secret_key: 密钥字符串
    :return: 十六进制格式的 SHA256 签名
    """
    # 拼接签名字符串（注意格式与 Go 代码严格一致）
    data_to_sign = f"rand={rand}&secretkey={secret_key}&ts={ts}"
    
    # 生成 SHA256 签名
    sha256 = hashlib.sha256()
    sha256.update(data_to_sign.encode('utf-8'))
    return sha256.hexdigest()

def make_signature(baseUrl: str) -> tuple[str, dict]:
    url = baseUrl + "?rand=%d&ts=%d"
    rand = random.randint(10000000, 99999999)
    ts = int(time.time())
    url = url % (rand, ts)
    print(f"url= {url}")

    secretkey = "nDQ5EVbQUiDSYpOz"
    # 生成签名
    sign = make_sha256_signature(rand, ts, secretkey)
    print(f"Generated Signature: {sign}")
    # 添加自定义 Header
    headers = {
        "X-SHA-Signature": sign
    }
    return url, headers
