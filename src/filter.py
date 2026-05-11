from src.config import BF_ERROR_RATE, BF_INITIAL_SIZE, BF_KEY, CF_KEY_PREFIX, CF_CAPACITY, CF_BUCKET_SIZE, CF_MAX_ITERATIONS, CF_EXPANSION
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

'''由于简单的BloomFilter的使用无法删除记录，即在取消点赞这一场景下，无法将用户从BloomFilter中删除，
因此需要对现有的BloomFilter进行修改，用于记录用户对某篇文章的点赞情况。

这里参考了一种Cuckoo Filter的实现，其原理与Bloom Filter类似，但可以删除记录。
该过滤器目前只添加到项目中保留了类的调用，还没有集成到前端，前后端现仍使用的是原位图的方案，这里给出一种方案参考
'''

class LikeFilter:
    def __init__(self, post_id):
        self.redis = getRedisClient()
        self.post_id = post_id
        self.key = f"{CF_KEY_PREFIX}:{post_id}"
        self.db = getDatabase()

    def _init_filter(self):
        if not self.redis.exists(self.key):
            try:
                self.redis.execute_command(
                    "CF.RESERVE",
                    self.key,
                    CF_CAPACITY,
                    "BUCKETSIZE", CF_BUCKET_SIZE,
                    "MAXITERATIONS", CF_MAX_ITERATIONS,
                    "EXPANSION", CF_EXPANSION,
                )
            except redis.ResponseError as e:
                if "key already exists" not in str(e).lower():
                    raise ValueError(f"Failed to initialize cuckoo filter: {e}")

    def add(self, user_id):
        self._init_filter()

        try:
            result = self.redis.execute_command("CF.ADD", self.key, user_id)
            return result == 1
        except redis.ResponseError as e:
            raise ValueError(f"Failed to add to cuckoo filter: {e}")

    def addNx(self, user_id):
        self._init_filter()

        try:
            result = self.redis.execute_command("CF.ADDNX", self.key, user_id)
            return result == 1
        except redis.ResponseError as e:
            raise ValueError(f"Failed to addnx to cuckoo filter: {e}")

    def delete(self, user_id):
        if not self.redis.exists(self.key):
            return False

        try:
            result = self.redis.execute_command("CF.DEL", self.key, user_id)
            return result == 1
        except redis.ResponseError as e:
            # 元素可能不存在
            return False

    def exists(self, user_id):
        if not self.redis.exists(self.key):
            return False

        result = self.redis.execute_command("CF.EXISTS", self.key, user_id)
        return result == 1

    def count(self, user_id):
        if not self.redis.exists(self.key):
            return 0

        try:
            result = self.redis.execute_command("CF.COUNT", self.key, user_id)
            return result
        except redis.ResponseError:
            return 0

    def info(self):
        if not self.redis.exists(self.key):
            return None

        try:
            result = self.redis.execute_command("CF.INFO", self.key)
            # 转换为字典格式
            info_dict = {}
            for i in range(0, len(result), 2):
                key = result[i].decode() if isinstance(result[i], bytes) else result[i]
                value = result[i+1].decode() if isinstance(result[i+1], bytes) else result[i+1]
                info_dict[key] = value
            return info_dict
        except redis.ResponseError as e:
            return None

    def reset(self):
        if self.redis.exists(self.key):
            self.redis.execute_command("DEL", self.key)
        self._init_filter()

    def loadFromDatabase(self):
        from src.model import Like

        self.reset()

        likes = self.db.query(Like).filter(Like.postId == self.post_id).all()
        pipe = self.redis.pipeline()

        for like in likes:
            pipe.execute_command("CF.ADD", self.key, like.userId)

        if likes:
            pipe.execute()

        self.db.close()
        return len(likes)

if __name__ == '__main__':
    bf = LikeFilter(post_id=1)

    bf.add(100)
    print(bf.exists(100))  # True
    print(bf.exists(200))  # False
    bf.delete(100)
    print(bf.exists(100))  # False