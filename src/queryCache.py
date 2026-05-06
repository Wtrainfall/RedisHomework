from src.cache import CacheService
from src.redis import getRedisClient, clearRedisCache
from src.model import getDatabase, User, Post, Follower, Like, Browse
from src.filter import UserBloomFilter

class CacheQueryService:

    def __init__(self):
        self.cache = CacheService()
        self.redis = getRedisClient()
        self.db = getDatabase()

    def getFriends(self, user_id):

        if self.redis.exists(f"user:followers:set:{user_id}"):
            followers = self.redis.smembers(f"user:followers:set:{user_id}")
        else:
            followers = self.cache.followers(user_id)
        
        if self.redis.exists(f"user:following:set:{user_id}"):
            following = self.redis.smembers(f"user:following:set:{user_id}")
        else:
            following = self.cache.following(user_id)
        
        friends = set(followers) & set(following)
        return friends

    def ifLike(self, user_id, post_id):

        if self.redis.exists(f"post:likes:bitmap:{post_id}"):
            like = self.redis.getbit(f"post:likes:bitmap:{post_id}", user_id)
        else:
            like = self.cache.postLike(user_id, post_id)
        
        return like
        
    def getLikeCounts(self, post_id):
        
        if self.redis.exists(f"post:likes:count:{post_id}"):
            likes_count = self.redis.get(f"post:likes:count:{post_id}")
        else:
            likes_count = self.cache.likeCounts(post_id)
        
        return likes_count

    def getTopLike(self):
        post_ids = [row[0] for row in self.db.query(Post.postId).all()]

        like_counts = []
        for post_id in post_ids:
            like_counts.append(int(self.getLikeCounts(post_id)))

        self.db.close()
        return sorted(zip(post_ids, like_counts), key=lambda x: x[1], reverse=True)[:10]

    def getSameFollowing(self, user_id):

        if self.redis.exists(f"user:following:set:{user_id}"):
            following = self.redis.smembers(f"user:following:set:{user_id}")
        else:
            following = self.cache.following(user_id)
        
        all_users = [row[0] for row in self.db.query(User.userId).all()]
        
        common_counts = []
        for uid in all_users:
            if uid != user_id:
                other_following = self.redis.smembers(f"user:following:set:{uid}")
                
                if not other_following:
                    rows = self.db.query(Follower.idolId).filter(
                        Follower.fansId == uid
                    ).all()
                    other_following = {str(row[0]) for row in rows}
                
                common = set(following) & other_following
                common_counts.append((int(uid), len(common)))

        self.db.close()
        common_counts.sort(key=lambda x: x[1], reverse=True)
        return common_counts[:3]

    def getFollowers(self, user_id):

        bf = UserBloomFilter()
        if not bf.exists(user_id):
            return None

        if self.redis.exists(f"user:followers:set:{user_id}"):
            followers = self.redis.smembers(f"user:followers:set:{user_id}")
        else:
            followers = self.cache.followers(user_id)
        
        return followers

    def getFollowing(self, user_id):

        bf = UserBloomFilter()
        if not bf.exists(user_id):
            return None

        if self.redis.exists(f"user:following:set:{user_id}"):
            following = self.redis.smembers(f"user:following:set:{user_id}")
        else:
            following = self.cache.following(user_id)
        
        return following

if __name__ == '__main__':
    queryService = CacheQueryService()
    print(queryService.getFriends(1))
    print(queryService.ifLike(1, 2))
    print(queryService.getLikeCounts(1))
    print(queryService.getTopLike())
    print(queryService.getSameFollowing(1))
    print(queryService.getFollowers(4))