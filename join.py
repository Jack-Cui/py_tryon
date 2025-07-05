import requests
import json
import random
import time
import signature

# 加入房间，不过响应没啥东西
def join_room(room_id, web_host, access_token):
    """
    加入房间的POST请求
    
    Args:
        room_id: 房间ID
        web_host: 服务器主机地址
        access_token: 访问令牌
    
    Returns:
        response: 请求响应对象
    """
    # 构造请求URL
    url = f"{web_host}/admin/roomUser/join"
    
    # 构造请求数据
    data = {
        "id": room_id
    }
    
    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        # 发送POST请求
        response = requests.post(
            url=url,
            json=data,  # 使用json参数自动序列化并设置Content-Type
            headers=headers,
            timeout=30  # 设置超时时间
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        print(f"请求成功，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def test_schedule():
    url = 'http://dev_gw.ai1010.cn/alloc/room_inst?rand=%d&ts=%d'
    rand = random.randint(10000000, 99999999)
    ts = int(time.time())
    url = url % (rand, ts)
    print(f"url= {url}")
    secretkey = "nDQ5EVbQUiDSYpOz"
    # 生成签名
    sign = signature.make_sha256_signature(rand, ts, secretkey)
    print(f"Generated Signature: {sign}")
    # 添加自定义 Header
    headers = {
        "X-SHA-Signature": sign
    }
    # 可选的请求体（如果有的话）
    data = {
        "user_id": 1754092805389819906,
        "priority_ips": ["14.103.136.236","120.245.126.162"],
        "latitude": 0.0,
        "longitude": 0.0,
        "poi": None,
        "room_id": 1897191226568142849,
    }

    # 发送 POST 请求
    response = requests.post(url, json=data, headers=headers)

    # 打印返回值
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)


# 使用示例
if __name__ == "__main__":
    # 示例参数（需要根据实际情况修改）
    ROOM_ID = "1897191226568142849"
    WEB_HOST = "http://180.184.140.234:9999"  # 替换为实际的服务器地址
    ACCESS_TOKEN = "80e5268b-dc0b-450e-9b4e-d9a0deaf5fbf"   # 替换为实际的访问令牌
    # response1 = join_room(ROOM_ID, WEB_HOST, ACCESS_TOKEN)
    # print(response1)
    test_schedule()