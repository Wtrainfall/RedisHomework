from src.model import getDatabase, User, Post, Follower, Like, Browse

class DBQueryService:

    def __init__(self):
        self.db = getDatabase()

    def _closeDatabase(self):
        self.db.close()

    def getFollowing(self, user_id):
        '''
        获取关注的人的id列表
        '''
        rows = self.db.query(Follower.idolId).filter(
                Follower.fansId == user_id
            ).all()
        following = [str(row[0]) for row in rows]
        
        data = {
            'followerId': user_id,
            'followingId': following
        }

        return data

    def getFollowers(self, user_id):
        '''
        获取粉丝的id列表
        '''
        rows = self.db.query(Follower.fansId).filter(
                Follower.idolId == user_id
            ).all()
        # json 格式化
        followers = [str(row[0]) for row in rows]

        data = {
        'followingId': user_id,
        'followerId': followers
        }

        return data 

    def getPostInfo(self, post_id):

        post = self.db.query(Post).filter(
                Post.postId == post_id
            ).first()
        
        if post is None:
            return None
        
        data = {
            'postId': post.postId,
            'postContent': post.postContent,
            'publisherId': post.postPublisher,
            'pubDate': post.pubDate
        }

        return data

        
    def getLikesInfo(self, post_id=None, user_id=None):

        if post_id is None and user_id is None:
            return None
        query = self.db.query(Like)
        if post_id is not None:
            query = query.filter(Like.postId == post_id)
            likes = query.all()
            data = {
                'likeUserId': [like.userId for like in likes]
            }
        if user_id is not None:
            query = query.filter(Like.userId == user_id)
            likes = query.all()
            data = {
                'likePostId': [like.postId for like in likes]
            }
        
        return data

    def getBrowseInfo(self, user_id):
        browse = self.db.query(Browse).filter(
                Browse.userId == user_id
            ).all()

        data = {
            'browsePostId': [browse.postId for browse in browse]
        }

        return data

if __name__ == '__main__':
    queryService = DBQueryService()
    print(queryService.getFollowers(1))
    print(queryService.getFollowing(1))
    print(queryService.getPostInfo(1))
    print(queryService.getLikesInfo(post_id=1))
    print(queryService.getLikesInfo(user_id=1))
    print(queryService.getBrowseInfo(1))
    queryService._closeDatabase()


