import redis
from src.config import REDIS_CONFIG

class RedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance
    
    def connect(self):
        
        if self._client is None:
            self._client = redis.Redis(**REDIS_CONFIG)
        return self._client
    
    def get_client(self):

        if self._client is None:
            return self.connect()
        return self._client

def getRedisClient():
    return RedisClient().get_client()
    
def clearRedisCache():
    client = getRedisClient()
    client.flushdb()
    