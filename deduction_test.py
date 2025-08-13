from deduction import KEY, compute_hmac_sha256
import hmac
import hashlib
import base64


def compute_hmac_sha256_2(key: str, message: str) -> str:
    """
    计算HMAC-SHA256签名
    
    参数:
        key: 密钥字符串
        message: 要签名的消息字符串
    
    返回:
        Base64编码的HMAC-SHA256签名
    """
    # 将密钥和消息转换为字节数组(UTF-8编码)
    key_bytes = key.encode('utf-8')
    message_bytes = message.encode('utf-8')
    
    # 使用hmac和hashlib计算哈希
    hmac_hash = hmac.new(key_bytes, message_bytes, hashlib.sha256)
    
    # 获取二进制哈希值并转换为Base64字符串
    hash_bytes = hmac_hash.digest()
    return base64.b64encode(hash_bytes).decode('utf-8')


def compute_hmac_sha256_3(message: str, key: str) -> str:
    # 将密钥和消息转换为字节数组（UTF-8 编码）
    key_bytes = key.encode('utf-8')
    message_bytes = message.encode('utf-8')

    # 使用 HMAC-SHA256 进行计算
    hmac_obj = hmac.new(key_bytes, message_bytes, hashlib.sha256)
    hash_bytes = hmac_obj.digest()

    # 返回 Base64 编码的结果
    return base64.b64encode(hash_bytes).decode('utf-8')

def generate_hmac(data: str, public_key: str) -> str:
    try:
        # UTF-8 编码
        key_bytes = public_key.encode('utf-8')
        data_bytes = data.encode('utf-8')

        # 计算 HMAC-SHA256
        hmac_obj = hmac.new(key_bytes, data_bytes, hashlib.sha256)
        digest_bytes = hmac_obj.digest()

        # Base64 编码
        return base64.b64encode(digest_bytes).decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"HMAC生成失败: {e}")

if __name__ == "__main__":
    # message = '{"deducteList":[{"deduction":2,"billPrice":0.3,"sourceId":1939613403762253825,"reduceCount":1,"clotheId":0}]}|1754894389926|1754092805389819906'
    message = '{"deducteList":[{"deduction":4,"billPrice":0.5,"sourceId":1898976321989808130,"reduceCount":1,"clotheId":0},{"deductionType":2,"billPrice":0.3,"sourceId":1898976321989808130,"reduceCount":1,"clotheId":0}]}|1754899991159|1783115976386400257'
    print(message)
    signature = compute_hmac_sha256(message)
    print('v1:', signature)
    signature2 = compute_hmac_sha256_2(KEY, message)
    print('v2:', signature2)
    signature3 = compute_hmac_sha256_3(message, KEY)
    print('v3:', signature3)

    end = "\n"
    key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwxAKb+pGIdtg189rgCtLGClLVTcWkAga0UTiZ8cfDzNDBF3eZBX96iXb5godZLHaAg38OZbtqclZfWBu9nBEpaV+nZudJ5z42RFpJlK6p9ACetR+/rX5Xfol9k0DayI9lP42uyK8h+wv/LPcA5PT/eE4aSMwn2g/xrVuLPGpCXM5Ca3de8s6Rj5JdW2GccLsi3GueLet2N4+a88cvpNMr4poVu135cb+SyxEbt3/4z0HhTFM0QF+GLaw+3faT8A4peiiot4io1UCUyW8fRXIAiHv5J0s8Y3bJW311BZFs/jnAodiIvQKzh3pEMKMyo0kw0T7HF5G4oSe+6Dvn9AV6QIDAQAB" + end

    message = '{"deducteList":[{"deduction":4,"billPrice":0.5,"sourceId":1898976321989808130,"reduceCount":1,"clotheId":0},{"deductionType":2,"billPrice":0.3,"sourceId":1898976321989808130,"reduceCount":1,"clotheId":0}]}|1754899991159|1783115976386400257' + end

    # 注意：这里不做任何 JSON 格式化、空格处理，直接 UTF-8 原样参与签名
    key_bytes = key.encode('utf-8')
    message_bytes = message.encode('utf-8')

    hmac_obj = hmac.new(key_bytes, message_bytes, hashlib.sha256)
    hash_bytes = hmac_obj.digest()
    result = base64.b64encode(hash_bytes).decode('utf-8')

    print('v4:', result)

    result = generate_hmac(message, key)
    print('v5:', result)