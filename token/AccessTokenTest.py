# cd python/src && python AccessTokenTest.py
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
import AccessToken

# const config = {
#   appId: '643e46acb15c24012c963951',
#   roomId: '1897845474368745473',
#   tokens: [
#     {
#       userId: '1754092805389819906',
#       token: '001643e46acb15c24012c963951XAD0ns4AXZRfaN3OaGgTADE4OTc4NDU0NzQzNjg3NDU0NzMTADE3NTQwOTI4MDUzODk4MTk5MDYGAAAA3c5oaAEA3c5oaAIA3c5oaAMA3c5oaAQA3c5oaAUA3c5oaCAAeTc1iDr78uiVKZ8Kv4f9xLOIKQbcd4wyR9fEsgQPu9Y=',
#     },
#   ],
# };

app_id = "643e46acb15c24012c963951"
app_key = "b329b39ca8df4b5185078f29d8d8025f"
room_id = "1939613403762253825"
user_id = "1754092805389819906"

token = AccessToken.AccessToken(app_id, app_key, room_id, user_id)
token.add_privilege(AccessToken.PrivSubscribeStream, 0)
token.add_privilege(AccessToken.PrivPublishStream, int(time.time()) + 3600)
token.expire_time(int(time.time()) + 3600)

s = token.serialize()

print(s)

t = AccessToken.parse(s)

print(t.verify(app_key))
