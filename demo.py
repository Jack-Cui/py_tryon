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
import logging
import inspect
from datetime import datetime

endpoint = 'http://180.184.140.234:9999'
phone = '13500003000'

# 配置日志
def setup_logger():
    """设置日志配置"""
    # 创建logger
    logger = logging.getLogger('demo')
    logger.setLevel(logging.INFO)
    
    # 如果已经有handler，不重复添加
    if logger.handlers:
        return logger
    
    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建文件handler
    file_handler = logging.FileHandler('demo.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 设置格式器
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加handler到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 创建logger实例
logger = setup_logger()

def log_info(message):
    """记录信息日志，包含当前时间和行号"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 获取调用者的文件名和行号
    current_frame = inspect.currentframe()
    if current_frame and current_frame.f_back:
        filename = current_frame.f_back.f_code.co_filename.split('/')[-1]  # 只取文件名部分
        lineno = current_frame.f_back.f_lineno
        logger.info(f"[{current_time}] [{filename}:{lineno}] {message}")
    else:
        logger.info(f"[{current_time}] [unknown:0] {message}")

def log_error(message):
    """记录错误日志，包含当前时间和行号"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 获取调用者的文件名和行号
    current_frame = inspect.currentframe()
    if current_frame and current_frame.f_back:
        filename = current_frame.f_back.f_code.co_filename.split('/')[-1]  # 只取文件名部分
        lineno = current_frame.f_back.f_lineno
        logger.error(f"[{current_time}] [{filename}:{lineno}] {message}")
    else:
        logger.error(f"[{current_time}] [unknown:0] {message}")

def log_warning(message):
    """记录警告日志，包含当前时间和行号"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 获取调用者的文件名和行号
    current_frame = inspect.currentframe()
    if current_frame and current_frame.f_back:
        filename = current_frame.f_back.f_code.co_filename.split('/')[-1]  # 只取文件名部分
        lineno = current_frame.f_back.f_lineno
        logger.warning(f"[{current_time}] [{filename}:{lineno}] {message}")
    else:
        logger.warning(f"[{current_time}] [unknown:0] {message}")

async def send_heartbeat(websocket, stop_event):
    """每20秒发送一次心跳"""
    try:
        while not stop_event.is_set():
            # 创建心跳请求
            heartbeat_req = XProto_pb2.oHeartBeatReq()
            heartbeat_req.timestamp = int(time.time() * 1000)  # 毫秒时间戳
            
            # 序列化消息
            protobuf_body = heartbeat_req.SerializeToString()
            
            # 构造完整消息 (4字节长度 + 2字节消息号 + Protobuf数据)
            message_id = 1111  # HeartBeatReq的ID
            total_length = 4 + 2 + len(protobuf_body)  # 包含长度字段自身
            
            # 小端格式打包
            message = (
                struct.pack('<I', total_length) +  # 4字节长度 (小端)
                struct.pack('<H', message_id) +  # 2字节消息ID (小端)
                protobuf_body  # Protobuf数据
            )
            
            # 发送心跳
            await websocket.send(message)
            log_info(f"已发送心跳请求 ({len(message)} 字节), timestamp: {heartbeat_req.timestamp}")
            
            # 等待20秒
            await asyncio.sleep(20)
            
    except asyncio.CancelledError:
        log_info("心跳任务被取消")
    except Exception as e:
        log_error(f"发送心跳时发生错误: {e}")

def get_verify_code():
    url = f"{endpoint}/admin/mobile/{phone}"
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    log_info(f"状态码: {response.status_code}")
    log_info(f"响应内容: {response.text}")
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
    log_info(f"状态码: {response.status_code}")
    log_info(f"响应内容: {response.text}")
    return response.json()

def schedule(user_id, room_id):
    url = 'http://dev_gw.ai1010.cn/alloc/room_inst?rand=%d&ts=%d'
    rand = random.randint(10000000, 99999999)
    ts = int(time.time())
    url = url % (rand, ts)
    log_info(f"url= {url}")
    secretkey = "nDQ5EVbQUiDSYpOz"
    # 生成签名
    sign = signature.make_sha256_signature(rand, ts, secretkey)
    log_info(f"Generated Signature: {sign}")
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
    log_info(f"Status Code: {response.status_code}")
    log_info("Response Body:")
    log_info(response.text)
    res = response.json()
    instoken = res['data']['inst_acc_info']['token']
    ws_url = res['data']['inst_acc_info']['ws_url']
    
    # 如果ws_url为空，使用默认的WebSocket URL
    if not ws_url:
        ws_url = "dev_wss.ai1010.cn/w8"
        log_info(f"ws_url为空，使用默认URL: {ws_url}")
    
    log_info(f'token={instoken}')
    log_info(f'ws_url={ws_url}')
    return instoken, ws_url


async def send_login_request(uid, access_token, instoken, room_id, enter_stage_info, ws_url):
    # WebSocket连接参数
    url = f"wss://{ws_url}"
    log_info(f"连接WebSocket: {url}")

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
        # 创建停止事件，用于控制心跳任务
        stop_event = asyncio.Event()
        
        # 启动心跳任务 - 连接建立后立即开始
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket, stop_event))
        log_info("WebSocket连接建立，心跳任务已启动")
        
        try:
            # 创建 protobuf 消息
            login_req = XProto_pb2.oLoginReq()
            login_req.account = uid
            login_req.token = access_token
            login_req.insToken = instoken
            log_info(f"登录请求参数: uid: {login_req.account}, token: {login_req.token}, insToken: {login_req.insToken}")

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
            log_info(f"已发送登录请求 ({len(message)} 字节)")

            # 接收响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                log_info(f"收到原始响应: {response[:100]}...")  # 只打印前100字节

                # 解析响应
                # 响应格式: [4字节长度] [2字节消息ID] [protobuf数据]
                total_len = struct.unpack('<I', response[:4])[0]
                msg_id = struct.unpack('<H', response[4:6])[0]
                payload = response[6:]

                log_info(f"响应消息ID: {msg_id}, 长度: {total_len}")

                # 根据消息ID解析不同的响应类型
                if msg_id == 1101:  # LoginAsw
                    login_asw = XProto_pb2.oLoginAsw()
                    login_asw.ParseFromString(payload)
                    log_info(f"登录响应: {login_asw.code}")
                    # 查看枚举值对应的名称
                    error_name = XProto_pb2.eError.Name(login_asw.code)
                    log_info(f"登录结果: {error_name}")
                    
                    # 如果登录成功，发送进入房间请求
                    if login_asw.code == XProto_pb2.SUCCESS:
                        log_info("登录成功，准备进入房间...")
                        # 进入房间成功后，会在房间内发送登台请求
                        await send_enter_room_request(websocket, room_id, enter_stage_info)  # 使用schedule函数中的room_id，并传递enter_stage_info

                elif msg_id == 1105:  # LoginOtherPush
                    login_other = XProto_pb2.oLoginOtherPush()
                    login_other.ParseFromString(payload)
                    log_info("收到顶号通知")

                elif msg_id == 1111:  # HeartBeatAsw
                    heartbeat_asw = XProto_pb2.oHeartBeatAsw()
                    heartbeat_asw.ParseFromString(payload)
                    log_info(f"收到心跳响应: timestamp={heartbeat_asw.timestamp}")

                else:
                    log_info(f"收到未知消息类型: {msg_id}")

            except asyncio.TimeoutError:
                log_error("等待响应超时")
                
        finally:
            # 停止心跳任务
            log_info("停止心跳任务...")
            stop_event.set()
            
            # 等待心跳任务完成
            try:
                await asyncio.wait_for(heartbeat_task, timeout=2.0)
            except asyncio.TimeoutError:
                log_warning("心跳任务停止超时，强制取消")
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass


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
        log_info(f"已发送进入房间请求 ({len(message)} 字节), roomId: {room_id}")

        # 循环接收消息直到收到进入房间响应
        enter_room_success = False
        timeout_count = 0
        max_timeouts = 3  # 最多等待3次超时
        
        while not enter_room_success and timeout_count < max_timeouts:
            try:
                # 接收响应
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                log_info(f"收到进入房间原始响应: {response[:100]}...")  # 只打印前100字节

                # 解析响应
                total_len = struct.unpack('<I', response[:4])[0]
                msg_id = struct.unpack('<H', response[4:6])[0]
                payload = response[6:]

                log_info(f"进入房间响应消息ID: {msg_id}, 长度: {total_len}")

                # 根据消息ID解析不同的响应类型
                if msg_id == 1201:  # EnterRoomAsw
                    enter_room_asw = XProto_pb2.oEnterRoomAsw()
                    enter_room_asw.ParseFromString(payload)
                    log_info(f"进入房间响应: {enter_room_asw.code}")
                    # 查看枚举值对应的名称
                    error_name = XProto_pb2.eError.Name(enter_room_asw.code)
                    log_info(f"进入房间结果: {error_name}")
                    
                    if enter_room_asw.code == XProto_pb2.SUCCESS:
                        log_info(f"成功进入房间: {enter_room_asw.roomId}")
                        log_info(f"在线用户数量: {len(enter_room_asw.onlineUsers)}")
                        log_info(f"舞台数量: {enter_room_asw.stageCount}")
                        log_info(f"场景: {enter_room_asw.scene}")
                        log_info(f"全员禁言: {enter_room_asw.allMute}")
                        if enter_room_asw.onlineUsers:
                            log_info(f"在线用户: {enter_room_asw.onlineUsers}")
                        if enter_room_asw.stageRtcIds:
                            log_info(f"舞台信息: {enter_room_asw.stageRtcIds}")
                        if enter_room_asw.queueUserIds:
                            log_info(f"排队用户: {enter_room_asw.queueUserIds}")
                        if enter_room_asw.muteUsers:
                            log_info(f"被禁言用户: {enter_room_asw.muteUsers}")
                        
                        # 进入房间成功后，发送登台请求
                        log_info("准备发送登台请求...")
                        await send_enter_stage_request(websocket, enter_stage_info, enter_room_asw.roomId)
                        enter_room_success = True
                    else:
                        log_error(f"进入房间失败: {error_name}")
                        return  # 进入房间失败，退出函数

                elif msg_id == 1202:  # EnterRoomPush
                    enter_room_push = XProto_pb2.oEnterRoomPush()
                    enter_room_push.ParseFromString(payload)
                    log_info(f"收到用户进入房间广播: 用户ID {enter_room_push.enterUserId}")

                elif msg_id == 1111:  # HeartBeatAsw
                    heartbeat_asw = XProto_pb2.oHeartBeatAsw()
                    heartbeat_asw.ParseFromString(payload)
                    log_info(f"收到心跳响应: timestamp={heartbeat_asw.timestamp}")
                    # 心跳响应不影响进入房间流程，继续等待

                else:
                    log_info(f"收到未知消息类型: {msg_id}")

            except asyncio.TimeoutError:
                timeout_count += 1
                log_warning(f"等待进入房间响应超时 ({timeout_count}/{max_timeouts})")
                
        if not enter_room_success:
            log_error("进入房间超时，未能收到成功响应")

    except Exception as e:
        log_error(f"发送进入房间请求时发生错误: {e}")


async def send_enter_stage_request(websocket, enter_stage_info, room_id):
    """发送登台请求"""
    try:
        log_info(f"登台信息: {enter_stage_info}")
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
        log_info(f"已发送登台请求 ({len(message)} 字节)")

        # 接收响应 - 循环接收消息直到登台成功或失败
        enter_stage_success = False
        received_stage_change = False
        room_id_for_leave = None
        
        timeout_count = 0
        max_timeouts = 2  # 最多等待2次超时，然后判断是否已经成功
        
        while not enter_stage_success and timeout_count < max_timeouts:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=40)
                log_info(f"收到消息原始响应: {response[:100]}...")  # 只打印前100字节

                # 解析响应
                total_len = struct.unpack('<I', response[:4])[0]
                msg_id = struct.unpack('<H', response[4:6])[0]
                payload = response[6:]

                log_info(f"响应消息ID: {msg_id}, 长度: {total_len}")

                # 根据消息ID解析不同的响应类型
                if msg_id == 1501:  # EnterStageAsw
                    enter_stage_asw = XProto_pb2.oEnterStageAsw()
                    enter_stage_asw.ParseFromString(payload)
                    log_info(f"登台响应: {enter_stage_asw.code}")
                    # 查看枚举值对应的名称
                    error_name = XProto_pb2.eError.Name(enter_stage_asw.code)
                    log_info(f"登台结果: {error_name}")
                    
                    if enter_stage_asw.code == XProto_pb2.SUCCESS:
                        log_info(f"成功登台: 房间ID {enter_stage_asw.roomId}, 舞台ID {enter_stage_asw.stageId}")
                        room_id_for_leave = enter_stage_asw.roomId
                        enter_stage_success = True
                    else:
                        log_error(f"登台失败: {error_name}")
                        return  # 登台失败，退出函数
                    
                elif msg_id == 1502:  # EnterStagePush
                    enter_stage_push = XProto_pb2.oEnterStagePush()
                    enter_stage_push.ParseFromString(payload)
                    log_info(f"收到用户登台广播: 用户ID {enter_stage_push.userId}, 舞台ID {enter_stage_push.stageId}")

                elif msg_id == 1522:  # StageStatusChangePush
                    stage_status_change = XProto_pb2.oStageStatusChangePush()
                    stage_status_change.ParseFromString(payload)
                    log_info(f"收到舞台状态变更: 索引{stage_status_change.index}, 舞台ID{stage_status_change.stageId}, 用户ID{stage_status_change.userId}, 状态{stage_status_change.stageType}")
                    
                    # 检查状态变更是否表示登台成功
                    if stage_status_change.stageType == XProto_pb2.StageTypeTryEnter:
                        log_info("舞台状态变更为 TryEnter - 正在尝试上台")
                        received_stage_change = True
                    elif stage_status_change.stageType == XProto_pb2.StageTypeWorking:
                        log_info("舞台状态变更为 Working - 已经在台上工作！")
                        received_stage_change = True
                        # 假设当前room_id就是我们要离开的房间ID（从全局变量获取）
                        # room_id_for_leave = room_id  # 需要从外部获取

                elif msg_id == 1505:  # StageQueueInfoPush
                    stage_queue_info = XProto_pb2.oStageQueueInfoPush()
                    stage_queue_info.ParseFromString(payload)
                    log_info(f"收到舞台队列信息: 队列类型{stage_queue_info.type}, 排队人数{stage_queue_info.queueCount}, 舞台数量{stage_queue_info.stageCount}")
                    if stage_queue_info.queueUserIds:
                        log_info(f"排队用户: {len(stage_queue_info.queueUserIds)}个")
                    if stage_queue_info.stageUserIds:
                        log_info(f"台上用户: {len(stage_queue_info.stageUserIds)}个")

                elif msg_id == 1111:  # HeartBeatAsw
                    heartbeat_asw = XProto_pb2.oHeartBeatAsw()
                    heartbeat_asw.ParseFromString(payload)
                    log_info(f"收到心跳响应: timestamp={heartbeat_asw.timestamp}")

                else:
                    log_info(f"收到未知消息类型: {msg_id}")

            except asyncio.TimeoutError:
                timeout_count += 1
                log_warning(f"等待登台响应超时 ({timeout_count}/{max_timeouts})")
                
                # 如果收到了舞台状态变更，可能登台已经成功
                if received_stage_change and timeout_count >= max_timeouts:
                    log_info("基于舞台状态变更判断登台可能成功，开始等待流程")
                    enter_stage_success = True
                    # 使用外部的room_id

        log_info(f"enter_stage_success: {enter_stage_success}, received_stage_change: {received_stage_change}")           
        # 如果成功登台（通过正式响应或状态变更推断）
        if enter_stage_success or received_stage_change:
            if not room_id_for_leave:
                # 如果没有从响应中得到room_id，使用传入的参数
                room_id_for_leave = room_id
                log_info(f"使用传入的房间ID: {room_id_for_leave}")
                
            log_info("登台成功，等待20秒后离开房间...")
            await wait_and_leave_room(websocket, room_id_for_leave)
        else:
            log_error("登台过程失败或超时")

    except Exception as e:
        log_error(f"发送登台请求时发生错误: {e}")


async def wait_and_leave_room(websocket, room_id):
    """等待20秒并在等待期间处理消息，然后离开房间"""
    start_time = asyncio.get_event_loop().time()
    target_time = start_time + 20  # 20秒后
    
    log_info(f"开始等待20秒... (当前时间: {start_time:.2f})")
    
    try:
        while True:
            current_time = asyncio.get_event_loop().time()
            remaining_time = target_time - current_time
            
            if remaining_time <= 0:
                log_info("等待时间已到，准备离开房间...")
                await send_leave_room_request(websocket, room_id)
                return
            
            log_info(f"剩余等待时间: {remaining_time:.1f}秒")
            
            try:
                # 设置较短的超时时间来检查消息，同时不阻塞太久
                response = await asyncio.wait_for(websocket.recv(), timeout=min(2.0, remaining_time))
                log_info(f"等待期间收到消息: {response[:50]}...")
                
                # 解析并处理收到的消息
                total_len = struct.unpack('<I', response[:4])[0]
                msg_id = struct.unpack('<H', response[4:6])[0]
                payload = response[6:]
                log_info(f"等待期间收到消息ID: {msg_id}, 长度: {total_len}")
                
                # 可以在这里处理其他类型的消息
                if msg_id == 1502:  # EnterStagePush
                    enter_stage_push = XProto_pb2.oEnterStagePush()
                    enter_stage_push.ParseFromString(payload)
                    log_info(f"等待期间收到用户登台广播: 用户ID {enter_stage_push.userId}, 舞台ID {enter_stage_push.stageId}")
                elif msg_id == 1522:  # StageStatusChangePush
                    stage_status_change = XProto_pb2.oStageStatusChangePush()
                    stage_status_change.ParseFromString(payload)
                    log_info(f"等待期间收到舞台状态变更: 索引{stage_status_change.index}, 舞台ID{stage_status_change.stageId}")
                elif msg_id == 1111:  # HeartBeatAsw
                    heartbeat_asw = XProto_pb2.oHeartBeatAsw()
                    heartbeat_asw.ParseFromString(payload)
                    log_info(f"等待期间收到心跳响应: timestamp={heartbeat_asw.timestamp}")
                else:
                    log_info(f"等待期间收到其他消息类型: {msg_id}")
                    
            except asyncio.TimeoutError:
                # 超时是正常的，继续循环检查时间
                continue
                
    except Exception as e:
        log_error(f"等待期间发生错误: {e}")
        # 即使发生错误，也尝试离开房间
        try:
            await send_leave_room_request(websocket, room_id)
        except:
            pass


async def send_leave_room_request(websocket, room_id):
    """发送离开房间请求"""
    try:
        # 创建离开房间请求
        leave_room_req = XProto_pb2.oLeaveRoomReq()
        leave_room_req.roomId = room_id

        # 序列化消息
        protobuf_body = leave_room_req.SerializeToString()

        # 构造完整消息 (4字节长度 + 2字节消息号 + Protobuf数据)
        message_id = 203  # LeaveRoomReq的ID
        total_length = 4 + 2 + len(protobuf_body)  # 包含长度字段自身

        # 小端格式打包
        message = (
                struct.pack('<I', total_length) +  # 4字节长度 (小端)
                struct.pack('<H', message_id) +  # 2字节消息ID (小端)
                protobuf_body  # Protobuf数据
        )

        # 发送消息
        await websocket.send(message)
        log_info(f"已发送离开房间请求 ({len(message)} 字节), roomId: {room_id}")

        # 接收响应
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        log_info(f"收到离开房间原始响应: {response[:100]}...")  # 只打印前100字节

        # 解析响应
        total_len = struct.unpack('<I', response[:4])[0]
        msg_id = struct.unpack('<H', response[4:6])[0]
        payload = response[6:]

        log_info(f"离开房间响应消息ID: {msg_id}, 长度: {total_len}")

        # 根据消息ID解析不同的响应类型
        if msg_id == 1203:  # LeaveRoomAsw
            leave_room_asw = XProto_pb2.oLeaveRoomAsw()
            leave_room_asw.ParseFromString(payload)
            log_info(f"离开房间响应: {leave_room_asw.code}")
            # 查看枚举值对应的名称
            error_name = XProto_pb2.eError.Name(leave_room_asw.code)
            log_info(f"离开房间结果: {error_name}")
            
            if leave_room_asw.code == XProto_pb2.SUCCESS:
                log_info("成功离开房间")
            else:
                log_error(f"离开房间失败: {error_name}")

        elif msg_id == 1204:  # LeaveRoomPush
            leave_room_push = XProto_pb2.oLeaveRoomPush()
            leave_room_push.ParseFromString(payload)
            log_info(f"收到用户离开房间广播: 用户ID {leave_room_push.leaveUserId}")

        elif msg_id == 1111:  # HeartBeatAsw
            heartbeat_asw = XProto_pb2.oHeartBeatAsw()
            heartbeat_asw.ParseFromString(payload)
            log_info(f"收到心跳响应: timestamp={heartbeat_asw.timestamp}")

        elif msg_id == 1505:  # StageQueueInfoPush
            stage_queue_info = XProto_pb2.oStageQueueInfoPush()
            stage_queue_info.ParseFromString(payload)
            log_info(f"收到舞台队列信息: 队列类型{stage_queue_info.type}, 排队人数{stage_queue_info.queueCount}, 舞台数量{stage_queue_info.stageCount}")
            if stage_queue_info.queueUserIds:
                log_info(f"排队用户: {len(stage_queue_info.queueUserIds)}个")
            if stage_queue_info.stageUserIds:
                log_info(f"台上用户: {len(stage_queue_info.stageUserIds)}个")

        else:
            log_info(f"收到未知消息类型: {msg_id}")

    except asyncio.TimeoutError:
        log_info("等待离开房间响应超时")
    except Exception as e:
        log_error(f"发送离开房间请求时发生错误: {e}")


def get_room_data(room_id):
    """获取房间数据的GET请求"""
    url = f"http://180.184.140.234:9999/admin/room/polling/query?id={room_id}"
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        log_info(f"房间数据请求状态码: {response.status_code}")
        log_info(f"房间数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            log_info(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        log_error(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        log_error(f"解析JSON响应失败: {e}")
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
        log_info(f"房间数据请求状态码: {response.status_code}")
        log_info(f"房间数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            log_info(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        log_error(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        log_error(f"解析JSON响应失败: {e}")
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
        log_info(f"房间数据请求状态码: {response.status_code}")
        # print(f"房间数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            log_info(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        log_error(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        log_error(f"解析JSON响应失败: {e}")
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
        log_info(f"房间数据请求状态码: {response.status_code}")
        log_info(f"房间数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            log_info(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        log_error(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        log_error(f"解析JSON响应失败: {e}")
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
        log_info(f"获取衣服尺寸数据请求状态码: {response.status_code}")
        log_info(f"获取衣服尺寸数据响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            log_info(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        log_error(f"请求发生错误: {e}")
        return None
    except ValueError as e:
        log_error(f"解析JSON响应失败: {e}")
        return None

def build_enter_stage_info(room_info):
    '''构建进入房间信息'''
    room_info_data = room_info['data']

    clothe_ids = room_info_data['clothId'].split(';')
    # clothe_ids = set(clothe_ids)
    garments = {}
    cnt = 1
    for clothe_id in clothe_ids:
        if clothe_id is None or clothe_id == '' or clothe_id == '0':
            clothe_id = "0"
            clothe_size = 0
        else:
            clothe_size_rsp = get_clothe_size(clothe_id, access_token)
            if clothe_size_rsp is None or 'data' not in clothe_size_rsp:
                log_error(f"get_clothe_size {clothe_id} err")
                # continue
            # clothe_size = clothe_size_rsp['data']
            clothe_size = 4
        log_info(f'clothe_id; {clothe_id}, clothe_size: {clothe_size}')
        if cnt == 1:
            garments['Garment1Id'] = clothe_id
            garments['Garment1Size'] = clothe_size
        elif cnt == 2:
            garments['Garment2Id'] = clothe_id
            garments['Garment2Size'] = clothe_size
        elif cnt == 3:
            garments['Garment3Id'] = clothe_id
            garments['Garment3Size'] = clothe_size
        else:
            log_error(f'cnt: {cnt}, clothe_id: {clothe_id}, clothe_size: {clothe_size} not filled')
            continue
        cnt += 1

    # enter_stage_info = {"AvatarId":0,"mapName":"Maps_Museum","Garments":{"Garment1Id":"1858424722817363969","Garment1Size":4,"Garment2Id":"0","Garment2Size":0,"Garment3Id":"0","Garment3Size":0},"Animation":None,"Camera":True,"Voice":False,"Size":1}
    enter_stage_info = {
        "AvatarId": 0,
        "UserId": room_info_data['userId'],
        # "UserId": None,
        # "UserId": "1754092805389819906",
        # "MapName": room_info_data['scenarioId'],
        "MapName": "Maps_jiaotang",
        "Garments": garments,
        "Animation": None,
        # "Animation": {
        #     "AnimId": room_info_data['actionId'],
        #     "PlayRate": 1,
        #     "IsLoop": True
        # },
        "Camera":True,
        "Voice":False,
        "Size":4,
        "isControl": True,
        "startTime": 0,
        "endTime": 0,
    }
    
    # 将enter_stage_info转成json字符串
    log_info(f'enter_stage_info: {enter_stage_info}')
    return json.dumps(enter_stage_info)

def get_room_info(room_id, access_token):
    '''获取房间信息'''
    url = f'{endpoint}/admin/room/query?id={room_id} '
    headers = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {access_token}"
    }
    try:    
        response = requests.get(url, headers=headers)
        log_info(f"获取房间信息请求状态码: {response.status_code}")
        log_info(f"获取房间信息响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            log_info(f"请求失败，状态码: {response.status_code}")
            return None
        
    except Exception as e:
        log_error(f"获取房间信息失败: {e}")

import sys
if __name__ == "__main__":
    co_creation_id = 2
    # 发送验证码
    # get_verify_code()
    # log_info("*" * 50 + "获取验证码成功" + "*" * 50)
    # # # 登录
    # res = send_token_request()
    # access_token = res['access_token']
    access_token = 'dac1ac12-de1d-4d0d-aad1-822c1d4e3f7b'
    account = 1754092805389819906
    # room_info = get_room_info(1897191226568142849, access_token)
    # if room_info is None:
    #     raise Exception("get_room_info err")
    # # log_info(f'room_info: {room_info}')
    # sys.exit(0)

    # account = int(res['user_id'])
    log_info(f"access_token: {access_token}, uid={account}")
    log_info("*" * 50 + "发送token成功" + "*" * 50)

    room_info = get_sysroomshare(co_creation_id, access_token)
    log_info("*" * 50 + "获取房间信息成功" + "*" * 50)
    if room_info is None:
        raise Exception("get_sysroomshare err")
    room_id = int(room_info['data']['roomId'])
    enter_stage_info = build_enter_stage_info(room_info)
    log_info("*" * 50 + "构建登台信息成功" + "*" * 50)
    
    # create_info = create_room(room_info['data']['roomId'], co_creation_id, access_token)
    # if create_info is None:
    #     raise Exception("create_room err")
    # room_primary_id = create_info['data']['id']
    # print(f'primary room key: {room_primary_id}')
    # print("*" * 50 + "创建房间成功" + "*" * 50)
    # join_info = join_room(room_primary_id, access_token, 1)
    # if join_info is None:
    #     raise Exception("join_room err")
    # print(f'join_info: {join_info}')
    # print("*" * 50 + "join房间成功" + "*" * 50)
    
    # 使用原始房间ID，不是创建房间返回的主键ID
    room_id = int(room_info['data']['roomId'])  # 使用原始房间ID
    user_id = "1754092805389819906"
    # user_id = room_info['data']['userId']
    insToken, ws_url = schedule(user_id, room_id)
    log_info(f'insToken: {insToken}, user_id: {user_id}, room_id: {room_id}')
    asyncio.get_event_loop().run_until_complete(send_login_request(int(user_id), access_token, insToken, room_id, enter_stage_info, ws_url))
    log_info("*" * 50 + "登台成功" + "*" * 50)
    
    # # 获取房间数据
    # room_id = 1897191226568142849  # 使用相同的房间ID
    # room_data = get_room_data(room_id)
    # if room_data:
    #     print("房间数据获取成功")
    # else:
    #     print("房间数据获取失败")

    