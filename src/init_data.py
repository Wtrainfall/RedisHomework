from src.model import getDatabase, initDatabase, clearDatabase, User, Post, Follower, Browse, Like
from sqlalchemy.dialects.sqlite import insert

def insertMockData():
    db = getDatabase()
    
    try:
        clearDatabase(db)
        
        users = [
            User(username='user01'), User(username='user02'),
            User(username='user03'), User(username='user04'),
            User(username='user05'), User(username='user06'),
            User(username='user07'), User(username='user08'),
            User(username='user09'), User(username='user10'),
            User(username='user11'), User(username='user12')
        ]
        db.add_all(users)
        db.commit()
        
        posts = [
            Post(postContent='今天天气不错', postPublisher=1),
            Post(postContent='学习MySQL真有趣', postPublisher=2),
            Post(postContent='MongoDB聚合框架好强', postPublisher=3),
            Post(postContent='早餐吃了包子', postPublisher=4),
            Post(postContent='下班路上看到晚霞', postPublisher=5),
            Post(postContent='喜欢编程的一天', postPublisher=6),
            Post(postContent='Redis五种数据类型', postPublisher=1),
            Post(postContent='数据结构与算法', postPublisher=2),
            Post(postContent='人工智能未来', postPublisher=7),
            Post(postContent='大数据实习项目', postPublisher=8),
            Post(postContent='社交平台数据库设计', postPublisher=9),
            Post(postContent='点赞评论关注', postPublisher=10)
        ]
        db.add_all(posts)
        db.commit()
        
        followers_data = [
            (1, 2), (1, 3), (1, 4), (2, 1), (2, 5), (3, 1), (3, 6),
            (4, 2), (4, 5), (5, 1), (5, 3), (6, 2), (6, 7), (7, 1),
            (7, 8), (8, 1), (8, 9), (9, 10), (10, 1), (11, 1),
            (11, 2), (12, 1)
        ]

        browses_data = [
            (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 1), (2, 2), (2, 3), (2, 4),
            (3, 1), (3, 2), (3, 5), (3, 6),
            (4, 1), (4, 3), (4, 5), (4, 7),
            (5, 1), (5, 2), (5, 4), (5, 6), (5, 8),
            (6, 1), (6, 2), (6, 3), (6, 5),
            (7, 1), (7, 2), (7, 4), (7, 9),
            (8, 1), (8, 2), (8, 5), (8, 10),
            (9, 1), (9, 3), (9, 6), (9, 11),
            (10, 1), (10, 2), (10, 4), (10, 12),
            (11, 1), (11, 2), (11, 3), (11, 5),
            (12, 1), (12, 2), (12, 4), (12, 6),
            (2, 6), (3, 7), (4, 8), (5, 9), (6, 10),
            (7, 11), (8, 12), (9, 1), (10, 3), (11, 4), (12, 7)
        ]

        likes_data = [
            (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1),
            (8, 1), (9, 1), (10, 1), (11, 1), (12, 1),
            (1, 2), (3, 2), (4, 2), (5, 2), (7, 2), (8, 2),
            (1, 3), (2, 3), (5, 3), (6, 3), (9, 3),
            (2, 4), (3, 4), (5, 4), (8, 4),
            (1, 5), (2, 5), (4, 5), (7, 5),
            (2, 6), (3, 6), (5, 6),
            (3, 7), (4, 8), (5, 9), (6, 10)
        ]

        db.execute(
            insert(Follower).values([
                {'fansId': f, 'idolId': i} for f, i in followers_data
            ]).on_conflict_do_nothing(
                index_elements=['fansId', 'idolId'] 
            )
        )
        
        db.execute(
            insert(Browse).values([
                {'userId': u, 'postId': p} for u, p in browses_data
            ]).on_conflict_do_nothing(
                index_elements=['userId', 'postId']
            )
        )
        
        db.execute(
            insert(Like).values([
                {'userId': u, 'postId': p} for u, p in likes_data
            ]).on_conflict_do_nothing(
                index_elements=['userId', 'postId']
            )
        )

        db.commit()
        
        print('Compeleted inserting mock data.')
    finally:
        db.close()


if __name__ == '__main__':
    initDatabase()
    insertMockData()