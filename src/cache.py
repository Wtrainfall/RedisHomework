from src.model import getDatabase, User, Post, Follower, Like, Browse
from src.redis import getRedisClient, clearRedisCache

class CacheService:
    def __init__(self):
        self.redis = getRedisClient()
        self.db = getDatabase()

    def _closeDB(self):
        self.db.close()

    def postLike(self, user_id, post_id):
        query = self.db.query(Like)
        query = query.filter(Like.postId == post_id)
        likes = query.all()
        users = [like.userId for like in likes]
        pipe = self.redis.pipeline()
        for uid in users:
            pipe.setbit(f"post:likes:bitmap:{post_id}", uid, 1)
        pipe.execute()
        self.redis.expire(f"post:likes:bitmap:{post_id}", 600)
        self._closeDB()
        return user_id in users

    def likeCounts(self, post_id):
        likes_count = self.db.query(Like).filter(Like.postId == post_id).count()
        self.redis.set(f"post:likes:count:{post_id}", likes_count)
        self.redis.expire(f"post:likes:count:{post_id}", 600)
        self._closeDB()
        return likes_count

    def followers(self, user_id):
        rows = self.db.query(Follower.fansId).filter(
                Follower.idolId == user_id
            ).all()
        followers = [str(row[0]) for row in rows]
        self.redis.sadd(f"user:followers:set:{user_id}", *followers)
        self.redis.expire(f"user:followers:set:{user_id}", 600)
        self._closeDB()
        return followers

    def following(self, user_id):
        rows = self.db.query(Follower.idolId).filter(
                Follower.fansId == user_id
            ).all()
        following = [str(row[0]) for row in rows]
        self.redis.sadd(f"user:following:set:{user_id}", *following)
        self.redis.expire(f"user:following:set:{user_id}", 600)
        self._closeDB()
        return following

    def followersCount(self, user_id):
        followers = self.followers(user_id)
        followers_count = len(followers)
        self.redis.set(f"user:followers:count:{user_id}", followers_count)
        self.redis.expire(f"user:followers:count:{user_id}", 600)
        self._closeDB()
        return followers_count
    
    def clearCache(self):
        clearRedisCache()

if __name__ == '__main__':
    cache = CacheService()
    # cache.redis.flushall()
    print(cache.postLike(1, 1))
    print(cache.likeCounts(1))
    print(cache.followers(1))
    print(cache.following(1))
    print(cache.followersCount(1))



        