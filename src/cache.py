from src.model import getDatabase, User, Post, Follower, Like, Browse
from src.redis import getRedisClient, clearRedisCache
from src.query import DBQueryService

class CacheService:
    def __init__(self):
        self.redis = getRedisClient()
        self.db = getDatabase()

    def _closeDB(self):
        self.db.close()

    def likePost(self, user_id, post_id):

        if self.redis.getbit(f"post:likes:bitmap:{post_id}", user_id):
            raise Exception("User has already liked this post")

        if not self.redis.exists(f"post:likes:count:{post_id}"):
            #初始化postlikes计数器
            likes_count = self.db.query(Like).filter(Like.post_id == post_id).count()
            self.redis.set(f"post:likes:count:{post_id}", likes_count)
        
        pipe = self.redis.pipeline()
        pipe.setbit(f"post:likes:bitmap:{post_id}", user_id, 1)
        pipe.incr(f"post:likes:count:{post_id}")
        pipe.execute()
        
        existing = self.db.query(Like).filter(Like.userId == user_id, Like.postId == post_id).first()

        if existing:
            self._closeDB()
            raise Exception("User already liked this post")
        
        like = Like(user_id=user_id, post_id=post_id)
        self.db.add(like)
        self.db.commit()
        self._closeDB()

    def unlikePost(self, user_id, post_id):

        if not self.redis.getbit(f"post:likes:bitmap:{post_id}", user_id):
           raise Exception("User has not liked this post yet")
        
        if not self.redis.exists(f"post:likes:count:{post_id}"):
            likes_count = self.db.query(Like).filter(Like.postId == post_id).count()
            self.redis.set(f"post:likes:count:{post_id}", likes_count)

        pipe = self.redis.pipeline()
        pipe.setbit(f"post:likes:bitmap:{post_id}", user_id, 0)
        pipe.decr(f"post:likes:count:{post_id}")
        pipe.execute()
        
        existing = self.db.query(Like).filter(Like.userId == user_id, Like.postId == post_id).first()

        if not existing:
            self._closeDB()
            raise Exception("User has not liked this post yet")

        self.db.delete(existing)
        self.db.commit()
        self._closeDB()

    def getPostLikes(self, post_id):

        #从redis中获取postlikes计数器
        if self.redis.exists(f"post:likes:count:{post_id}"):
            likes_count = self.redis.get(f"post:likes:count:{post_id}")
        else:
            #从数据库中获取postlikes计数器
            likes_count = self.db.query(Like).filter(Like.postId == post_id).count()
            self.redis.set(f"post:likes:count:{post_id}", likes_count)
            self._closeDB()

        return likes_count
    
    def getFollowers(self, user_id):

        if self.redis.exists(f"user:followers:set:{user_id}"):
            followers = self.redis.smembers(f"user:followers:set:{user_id}")
        else:
            rows = self.db.query(Follower.fansId).filter(
                    Follower.idolId == user_id
                ).all()
            followers = [str(row[0]) for row in rows]
            self.redis.sadd(f"user:followers:set:{user_id}", *followers)
            self._closeDB()

        return followers

    def getFollowing(self, user_id):

        if self.redis.exists(f"user:following:set:{user_id}"):
            following = self.redis.smembers(f"user:following:set:{user_id}")
        else:
            rows = self.db.query(Follower.idolId).filter(
                    Follower.fansId == user_id
                ).all()
            following = [str(row[0]) for row in rows]
            self.redis.sadd(f"user:following:set:{user_id}", *following)
            self._closeDB()
        
        return following

    def getFriends(self, user_id):

        following = self.getFollowing(user_id)
        followers = self.getFollowers(user_id)
        friends = set(following) & set(followers)
        
        return list(friends)

    def getFollowersCount(self, user_id):

        if self.redis.exists(f"user:followers:count:{user_id}"):
            followers_count = self.redis.get(f"user:followers:count:{user_id}")
        else:
            followers = self.getFollowers(user_id)
            followers_count = len(followers)
            self.redis.set(f"user:followers:count:{user_id}", followers_count)
            self._closeDB()
        
        return followers_count

if __name__ == '__main__':
    cache = CacheService()
    print(cache.getPostLikes(1))
    print(cache.getFollowers(1))
    print(cache.getFollowing(1))
    print(cache.getFriends(1))
    print(cache.getFollowersCount(1))



        