import struct
import asyncio
import ssl
import websockets
from generated.protos import XProto_pb2
import random
import time
import signature
import requests
import json

endpoint = 'http://180.184.140.234:9999'
phone = '13500003000'

def get_verify_code():
    url = f"{endpoint}/admin/mobile/{phone}"
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    print("状态码:", response.status_code)
    print("响应内容:", response.text)
    return response

def send_token_request():
    url = endpoint + f"/admin/oauth/token?mobile=SMS@{phone}&code=8888&grant_type=mobile"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "isToken": "false",
        "TENANT-ID": "1",
        "Authorization": "Basic cGlnOnBpZw=="
    }
    response = requests.post(url, headers=headers)
    print("状态码:", response.status_code)
    print("响应内容:", response.text)
    return response.json()

def schedule(user_id, room_id):
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
        # "user_id": 1754092805389819906,
        "user_id": user_id,
        "priority_ips": ["14.103.136.236","120.245.126.162"],
        "latitude": 0.0,
        "longitude": 0.0,
        "poi": None,
        # "room_id": 1897191226568142849,
        "room_id": room_id,
    }

    # 发送 POST 请求
    response = requests.post(url, json=data, headers=headers)

    # 打印返回值
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
    res = response.json()
    instoken = res['data']['inst_acc_info']['token']
    ws_url = res['data']['inst_acc_info']['ws_url']
    
    # 如果ws_url为空，使用默认的WebSocket URL
    if not ws_url:
        ws_url = "dev_wss.ai1010.cn/w8"
        print(f"ws_url为空，使用默认URL: {ws_url}")
    
    print(f'token={instoken}')
    print(f'ws_url={ws_url}')
    return instoken, ws_url


async def send_login_request(uid, access_token, instoken, room_id, enter_stage_info, ws_url):
    # WebSocket连接参数
    url = f"wss://{ws_url}"
    print(f"连接WebSocket: {url}")

    # 创建禁用验证的SSL上下文（仅用于测试）
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with websockets.connect(
            url,
            ssl=ssl_context,
            ping_interval=None,  # 禁用自动ping
            open_timeout=10  # 设置连接超时
    ) as websocket:
        # 创建 protobuf 消息
        login_req = XProto_pb2.oLoginReq()
        login_req.account = uid
        login_req.token = access_token
        login_req.insToken = instoken

        # 序列化消息
        protobuf_body = login_req.SerializeToString()

        # 构造完整消息 (4字节长度 + 2字节消息号 + Protobuf数据)
        message_id = 101  # LoginReq的ID
        total_length = 4 + 2 + len(protobuf_body)  # 包含长度字段自身

        # 小端格式打包
        message = (
                struct.pack('<I', total_length) +  # 4字节长度 (小端)
                struct.pack('<H', message_id) +  # 2字节消息ID (小端)
                protobuf_body  # Protobuf数据
        )

        # 发送消息
        await websocket.send(message)
        print(f"已发送登录请求 ({len(message)} 字节)")

        # 接收响应
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"收到原始响应: {response[:100]}...")  # 只打印前100字节

            # 解析响应
            # 响应格式: [4字节长度] [2字节消息ID] [protobuf数据]
            total_len = struct.unpack('<I', response[:4])[0]
            msg_id = struct.unpack('<H', response[4:6])[0]
            payload = response[6:]

            print(f"响应消息ID: {msg_id}, 长度: {total_len}")

            # 根据消息ID解析不同的响应类型
            if msg_id == 1101:  # LoginAsw
                login_asw = XProto_pb2.oLoginAsw()
                login_asw.ParseFromString(payload)
                print(f"登录响应: {login_asw.code}")
                # 查看枚举值对应的名称
                error_name = XProto_pb2.eError.Name(login_asw.code)
                print(f"登录结果: {error_name}")
                
                # 如果登录成功，发送进入房间请求
                if login_asw.code == XProto_pb2.SUCCESS:
                    print("登录成功，准备进入房间...")
                    # 进入房间成功后，会在房间内发送登台请求
                    await send_enter_room_request(websocket, room_id, enter_stage_info)  # 使用schedule函数中的room_id，并传递enter_stage_info

            elif msg_id == 1105:  # LoginOtherPush
                login_other = XProto_pb2.oLoginOtherPush()
                login_other.ParseFromString(payload)
                print("收到顶号通知")

            else:
                print(f"收到未知消息类型: {msg_id}")

        except asyncio.TimeoutError:
            print("等待响应超时")


async def send_enter_room_request(websocket, room_id, enter_stage_info):
    """发送进入房间请求"""
    try:
        # 创建进入房间请求
        enter_room_req = XProto_pb2.oEnterRoomReq()
        enter_room_req.roomId = room_id

        # 序列化消息
        protobuf_body = enter_room_req.SerializeToString()

        # 构造完整消息 (4字节长度 + 2字节消息号 + Protobuf数据)
        message_id = 201  # EnterRoomReq的ID
        total_length = 4 + 2 + len(protobuf_body)  # 包含长度字段自身

        # 小端格式打包
        message = (
                struct.pack('<I', total_length) +  # 4字节长度 (小端)
                struct.pack('<H', message_id) +  # 2字节消息ID (小端)
                protobuf_body  # Protobuf数据
        )

        # 发送消息
        await websocket.send(message)
        print(f"已发送进入房间请求 ({len(message)} 字节), roomId: {room_id}")

        # 接收响应
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        print(f"收到进入房间原始响应: {response[:100]}...")  # 只打印前100字节

        # 解析响应
        total_len = struct.unpack('<I', response[:4])[0]
        msg_id = struct.unpack('<H', response[4:6])[0]
        payload = response[6:]

        print(f"进入房间响应消息ID: {msg_id}, 长度: {total_len}")

        # 根据消息ID解析不同的响应类型
        if msg_id == 1201:  # EnterRoomAsw
            enter_room_asw = XProto_pb2.oEnterRoomAsw()
            enter_room_asw.ParseFromString(payload)
            print(f"进入房间响应: {enter_room_asw.code}")
            # 查看枚举值对应的名称
            error_name = XProto_pb2.eError.Name(enter_room_asw.code)
            print(f"进入房间结果: {error_name}")
            
            if enter_room_asw.code == XProto_pb2.SUCCESS:
                print(f"成功进入房间: {enter_room_asw.roomId}")
                print(f"在线用户数量: {len(enter_room_asw.onlineUsers)}")
                print(f"舞台数量: {enter_room_asw.stageCount}")
                print(f"场景: {enter_room_asw.scene}")
                print(f"全员禁言: {enter_room_asw.allMute}")
                if enter_room_asw.onlineUsers:
                    print(f"在线用户: {enter_room_asw.onlineUsers}")
                if enter_room_asw.stageRtcIds:
                    print(f"舞台信息: {enter_room_asw.stageRtcIds}")
                if enter_room_asw.queueUserIds:
                    print(f"排队用户: {enter_room_asw.queueUserIds}")
                if enter_room_asw.muteUsers:
                    print(f"被禁言用户: {enter_room_asw.muteUsers}")
                
                # 进入房间成功后，发送登台请求
                print("准备发送登台请求...")
                await send_enter_stage_request(websocket, enter_stage_info)
            else:
                print(f"进入房间失败: {error_name}")

        elif msg_id == 1202:  # EnterRoomPush
            enter_room_push = XProto_pb2.oEnterRoomPush()
            enter_room_push.ParseFromString(payload)
            print(f"收到用户进入房间广播: 用户ID {enter_room_push.enterUserId}")

        else:
            print(f"收到未知消息类型: {msg_id}")

    except asyncio.TimeoutError:
        print("等待进入房间响应超时")
    except Exception as e:
        print(f"发送进入房间请求时发生错误: {e}")


async def send_enter_stage_request(websocket, enter_stage_info):
    """发送登台请求"""
    try:
        # 创建登台请求
        enter_stage_req = XProto_pb2.oEnterStageReq()
        enter_stage_req.context = enter_stage_info

        # 序列化消息
        protobuf_body = enter_stage_req.SerializeToString()

        # 构造完整消息 (4字节长度 + 2字节消息号 + Protobuf数据)
        message_id = 501  # EnterStageReq的ID
        total_length = 4 + 2 + len(protobuf_body)  # 包含长度字段自身

        # 小端格式打包
        message = (
                struct.pack('<I', total_length) +  # 4字节长度 (小端)
                struct.pack('<H', message_id) +  # 2字节消息ID (小端)
                protobuf_body  # Protobuf数据
        )

        # 发送消息
        await websocket.send(message)
        print(f"已发送登台请求 ({len(message)} 字节)")

        # 接收响应 - 可能需要循环接收多个消息
        # while True:
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"收到消息原始响应: {response[:100]}...")  # 只打印前100字节

            # 解析响应
            total_len = struct.unpack('<I', response[:4])[0]
            msg_id = struct.unpack('<H', response[4:6])[0]
            payload = response[6:]

            print(f"响应消息ID: {msg_id}, 长度: {total_len}")

            # 根据消息ID解析不同的响应类型
            if msg_id == 1501:  # EnterStageAsw
                enter_stage_asw = XProto_pb2.oEnterStageAsw()
                enter_stage_asw.ParseFromString(payload)
                print(f"登台响应: {enter_stage_asw.code}")
                # 查看枚举值对应的名称
                error_name = XProto_pb2.eError.Name(enter_stage_asw.code)
                print(f"登台结果: {error_name}")
                
                if enter_stage_asw.code == XProto_pb2.SUCCESS:
                    print(f"成功登台: 房间ID {enter_stage_asw.roomId}, 舞台ID {enter_stage_asw.stageId}")
                else:
                    print(f"登台失败: {error_name}")
                # break  # 收到登台响应后退出循环

            elif msg_id == 1502:  # EnterStagePush
                enter_stage_push = XProto_pb2.oEnterStagePush()
                enter_stage_push.ParseFromString(payload)
                print(f"收到用户登台广播: 用户ID {enter_stage_push.userId}, 舞台ID {enter_stage_push.stageId}")

            elif msg_id == 1522:  # StageStatusChangePush
                stage_status_change = XProto_pb2.oStageStatusChangePush()
                stage_status_change.ParseFromString(payload)
                print(f"收到舞台状态变更: 索引{stage_status_change.index}, 舞台ID{stage_status_change.stageId}, 用户ID{stage_status_change.userId}, 状态{stage_status_change.stageType}")

            elif msg_id == 1505:  # StageQueueInfoPush
                stage_queue_info = XProto_pb2.oStageQueueInfoPush()
                stage_queue_info.ParseFromString(payload)
                print(f"收到舞台队列信息: 队列类型{stage_queue_info.type}, 排队人数{stage_queue_info.queueCount}, 舞台数量{stage_queue_info.stageCount}")
                if stage_queue_info.queueUserIds:
                    print(f"排队用户: {len(stage_queue_info.queueUserIds)}个")
                if stage_queue_info.stageUserIds:
                    print(f"台上用户: {len(stage_queue_info.stageUserIds)}个")

            else:
                print(f"收到未知消息类型: {msg_id}")

        except asyncio.TimeoutError:
            print("等待登台响应超时")
            # break

    except Exception as e:
        print(f"发送登台请求时发生错误: {e}")


def get_room_data(room_id):
    """获取房间数据的GET请求"""
    url = f"http://180.184.140.234:9999/admin/room/polling/query?id={room_id}"
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"房间数据请求状态码: {response.status_code}")
        print(f"房间数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        print(f"解析JSON响应失败: {e}")
        return None


def get_sysroomshare(co_creation_id, access_token):
    '''通过共创id获取房间信息'''
    # local_endpoint = "http://180.184.140.234:9999"
    url = f"{endpoint}/admin/sysroomshare/{co_creation_id}"
    headers = {
        'Content-Type': 'application/json',
        # "Authorization": "Basic cGlnOnBpZw=="
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"房间数据请求状态码: {response.status_code}")
        print(f"房间数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        print(f"解析JSON响应失败: {e}")
        return None

def create_room(room_id, co_creation_id, access_token):
    '''创建房间'''
    url = f'{endpoint}/admin/room/create'
    headers = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "sourceRoomId": room_id,
        "shareId": co_creation_id
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"房间数据请求状态码: {response.status_code}")
        # print(f"房间数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        print(f"解析JSON响应失败: {e}")
        return None

def join_room(room_primary_id, access_token, relationship_type):
    '''加入房间'''
    url = f'{endpoint}/admin/roomUser/join'
    headers = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "id": room_primary_id,
        "relationshipType": relationship_type
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"房间数据请求状态码: {response.status_code}")
        print(f"房间数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        print(f"解析JSON响应失败: {e}")
        return None

def get_clothe_size(clothe_id, access_token):
    '''获取衣服尺寸'''
    url = f'{endpoint}/admin/sysclotheextra/getSize/{clothe_id}'
    headers = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(url, headers=headers)
        print(f"获取衣服尺寸数据请求状态码: {response.status_code}")
        print(f"获取衣服尺寸数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        print(f"解析JSON响应失败: {e}")
        return None

def build_enter_stage_info(room_info):
    '''构建进入房间信息'''
    room_info_data = room_info['data']

    clothe_ids = room_info_data['clothId'].split(';')
    clothe_ids = set(clothe_ids)
    garments = {}
    cnt = 1
    for clothe_id in clothe_ids:
        if clothe_id is None or clothe_id == '' or clothe_id == '0':
            continue
        clothe_size_rsp = get_clothe_size(clothe_id, access_token)
        if clothe_size_rsp is None or 'data' not in clothe_size_rsp:
            print(f"get_clothe_size {clothe_id} err")
            continue
        clothe_size = clothe_size_rsp['data']
        print(f'clothe_id; {clothe_id}, clothe_size: {clothe_size}')
        if cnt == 1:
            garments['garment1Id'] = clothe_id
            garments['garment1Size'] = clothe_size
        elif cnt == 2:
            garments['garment2Id'] = clothe_id
            garments['garment2Size'] = clothe_size
        elif cnt == 3:
            garments['garment3Id'] = clothe_id
            garments['garment3Size'] = clothe_size
        else:
            print(f'cnt: {cnt}, clothe_id: {clothe_id}, clothe_size: {clothe_size} not filled')
            continue
        cnt += 1

    enter_stage_info = {
        "avatarId": 0,
        "userId": room_info_data['userId'],
        "mapName": room_info_data['scenarioId'],
        "garments": garments,
        "animation": {
            "animId": room_info_data['actionId'],
            "playRate": 1,
            "isLoop": True
        },
        "isControl": True,
        "startTime": 0,
        "endTime": 0,
    }
    # 将enter_stage_info转成json字符串
    print(f'enter_stage_info: {enter_stage_info}')
    enter_stage_info = json.dumps(enter_stage_info)
    return json.dumps(enter_stage_info)

if __name__ == "__main__":
    co_creation_id = 2
    # 发送验证码
    get_verify_code()
    print("*" * 50 + "获取验证码成功" + "*" * 50)
    # # # 登录
    res = send_token_request()
    access_token = res['access_token']
    account = int(res['user_id'])
    print(f"access_token: {access_token}, uid={account}")
    print("*" * 50 + "发送token成功" + "*" * 50)

    room_info = get_sysroomshare(co_creation_id, access_token)
    print("*" * 50 + "获取房间信息成功" + "*" * 50)
    if room_info is None:
        raise Exception("get_sysroomshare err")
    room_id = int(room_info['data']['roomId'])
    enter_stage_info = build_enter_stage_info(room_info)
    print("*" * 50 + "构建登台信息成功" + "*" * 50)
    
    create_info = create_room(room_info['data']['roomId'], co_creation_id, access_token)
    if create_info is None:
        raise Exception("create_room err")
    room_primary_id = create_info['data']['id']
    print(f'primary room key: {room_primary_id}')
    print("*" * 50 + "创建房间成功" + "*" * 50)
    join_info = join_room(room_primary_id, access_token, 1)
    if join_info is None:
        raise Exception("join_room err")
    print(f'join_info: {join_info}')
    print("*" * 50 + "join房间成功" + "*" * 50)
    
    # 使用原始房间ID，不是创建房间返回的主键ID
    room_id = int(room_info['data']['roomId'])  # 使用原始房间ID
    user_id = "1754092805389819906"
    # user_id = room_info['data']['userId']
    insToken, ws_url = schedule(user_id, room_id)
    print('insToken:', insToken, 'user_id:', user_id, 'room_id:', room_id)
    asyncio.get_event_loop().run_until_complete(send_login_request(account, access_token, insToken, room_id, enter_stage_info, ws_url))
    print("*" * 50 + "登台成功" + "*" * 50)
    
    # # 获取房间数据
    # room_id = 1897191226568142849  # 使用相同的房间ID
    # room_data = get_room_data(room_id)
    # if room_data:
    #     print("房间数据获取成功")
    # else:
    #     print("房间数据获取失败")

    