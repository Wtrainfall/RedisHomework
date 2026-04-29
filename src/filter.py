from src.config import BF_ERROR_RATE, BF_INITIAL_SIZE, BF_KEY
from src.redis import getRedisClient
from src.model import User, getDatabase
import redis

class UserBloomFilter:
    def __init__(self):
        self.redis = getRedisClient()
        self.key = BF_KEY
        self.error_rate = BF_ERROR_RATE
        self.initial_size = BF_INITIAL_SIZE
        self.db = getDatabase()

    def _init_bloom_filter(self):

        if not self.redis.exists(self.key):
            try:
                self.redis.execute_command(
                    "BF.RESERVE",
                    self.key,
                    self.error_rate,
                    self.initial_size,
                )
            except redis.ResponseError as e:
                raise ValueError(f"Failed to initialize bloom filter: {e}")

            all_users = [row[0] for row in self.db.query(User.userId).all()]
            for uid in all_users:
                self.add(uid)

    def add(self, item):

        return self.redis.execute_command("BF.ADD", self.key, item)

    def exists(self, item):

        return self.redis.execute_command("BF.EXISTS", self.key, item)
    
    def reset(self):
        self.redis.execute_command("DEL", self.key)
        self._init_bloom_filter()

