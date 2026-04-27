from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, PrimaryKeyConstraint, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
from src.config import DB_PATH

Base = declarative_base()

engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

SessionLocal = scoped_session(sessionmaker(bind=engine))

class User(Base):
    """用户表"""
    __tablename__ = 'user'
    
    userId = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    createTime = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    posts = relationship("Post", back_populates="publisher", foreign_keys="Post.postPublisher")
    likes = relationship("Like", back_populates="user")
    browses = relationship("Browse", back_populates="user")
    
    following = relationship(
        "Follower",
        foreign_keys="Follower.fansId",
        back_populates="fans"
    )

    followers = relationship(
        "Follower",
        foreign_keys="Follower.idolId",
        back_populates="idol"
    )

class Follower(Base):
    """关注表：粉丝 -> 偶像"""
    __tablename__ = 'follower'
    
    fansId = Column(Integer, ForeignKey('user.userId'), nullable=False)
    idolId = Column(Integer, ForeignKey('user.userId'), nullable=False)
    followTime = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    __table_args__ = (
        PrimaryKeyConstraint('fansId', 'idolId'),
    )
    
    fans = relationship("User", foreign_keys=[fansId], back_populates="following")
    idol = relationship("User", foreign_keys=[idolId], back_populates="followers")


class Post(Base):
    """帖子表"""
    __tablename__ = 'post'
    
    postId = Column(Integer, primary_key=True, autoincrement=True)
    postContent = Column(String, nullable=False)
    postPublisher = Column(Integer, ForeignKey('user.userId'), nullable=False)
    pubDate = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    publisher = relationship("User", back_populates="posts", foreign_keys=[postPublisher])
    likes = relationship("Like", back_populates="post")
    browses = relationship("Browse", back_populates="post")


class Browse(Base):
    """浏览表"""
    __tablename__ = 'browse'
    
    userId = Column(Integer, ForeignKey('user.userId'), nullable=False)
    postId = Column(Integer, ForeignKey('post.postId'), nullable=False)
    browseDate = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    __table_args__ = (
        PrimaryKeyConstraint('userId', 'postId'),
    )
    
    user = relationship("User", back_populates="browses")
    post = relationship("Post", back_populates="browses")


class Like(Base):
    """点赞表"""
    __tablename__ = 'likes'
    
    userId = Column(Integer, ForeignKey('user.userId'), nullable=False)
    postId = Column(Integer, ForeignKey('post.postId'), nullable=False)
    likeDate = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    __table_args__ = (
        PrimaryKeyConstraint('userId', 'postId'),
    )
    
    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")

def getDatabase():
    session = SessionLocal()
    try:
        return session
    except:
        session.close()
        raise

def initDatabase():
    Base.metadata.create_all(bind=engine)

def clearDatabase(session):
    try:
        session.query(User).delete()
        session.query(Post).delete()
        session.query(Browse).delete()
        session.query(Like).delete()
        session.query(Follower).delete()
        session.commit()
    finally:
        session.close()
    