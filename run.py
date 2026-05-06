from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from src.queryDB import DBQueryService
from src.queryCache import CacheQueryService
from src.cache import CacheService
from src.filter import UserBloomFilter
from src.model import getDatabase, User, Post, Follower, Like, Browse
from sqlalchemy.orm import joinedload
import os

base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

app.secret_key = 'your-secret-key-here'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    return session.get('user_id')

@app.route('/')
@login_required
def home():
    db = getDatabase()
    try:
        posts = db.query(Post).options(joinedload(Post.publisher)).order_by(Post.pubDate.desc()).all()
        cache_service = CacheQueryService()
        current_user_id = get_current_user_id()

        posts_data = []
        for post in posts:
            post_dict = {
                'postId': post.postId,
                'postContent': post.postContent,
                'publisherId': post.postPublisher,
                'pubDate': post.pubDate.strftime('%Y-%m-%d %H:%M'),
                'publisherName': post.publisher.username if post.publisher else f'用户{post.postPublisher}'
            }
            post_dict['likeCount'] = cache_service.getLikeCounts(post.postId)
            post_dict['isLiked'] = bool(cache_service.ifLike(current_user_id, post.postId))
            posts_data.append(post_dict)

        return render_template('homepage.html', posts=posts_data, current_user_id=current_user_id)
    finally:
        db.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            return render_template('login.html', error='请输入用户名')

        db = getDatabase()
        try:
            user = db.query(User).filter(User.username == username).first()
            if user:
                session['user_id'] = user.userId
                session['username'] = user.username
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error='用户不存在')
        finally:
            db.close()
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            return render_template('register.html', error='请输入用户名')

        db = getDatabase()
        try:
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                return render_template('register.html', error='用户名已存在')

            new_user = User(username=username)
            db.add(new_user)
            db.commit()

            bf = UserBloomFilter()
            bf.add(new_user.userId)

            session['user_id'] = new_user.userId
            session['username'] = new_user.username
            return redirect(url_for('home'))
        finally:
            db.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/post/<int:post_id>')
@login_required
def post_detail(post_id):
    db = getDatabase()
    try:
        post = db.query(Post).options(joinedload(Post.publisher)).filter(Post.postId == post_id).first()
        if not post:
            return '帖子不存在', 404

        cache_service = CacheQueryService()
        current_user_id = get_current_user_id()

        browse = Browse(userId=current_user_id, postId=post_id)
        db.merge(browse)
        db.commit()

        post_data = {
            'postId': post.postId,
            'postContent': post.postContent,
            'publisherId': post.postPublisher,
            'publisherName': post.publisher.username if post.publisher else f'用户{post.postPublisher}',
            'pubDate': post.pubDate.strftime('%Y-%m-%d %H:%M'),
            'likeCount': cache_service.getLikeCounts(post.postId),
            'isLiked': bool(cache_service.ifLike(current_user_id, post.postId))
        }

        return render_template('post_detail.html', post=post_data)
    finally:
        db.close()

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    bf = UserBloomFilter()
    if not bf.exists(user_id):
        return '用户不存在', 404

    db = getDatabase()
    try:
        user = db.query(User).filter(User.userId == user_id).first()
        if not user:
            return '用户不存在', 404

        cache_service = CacheQueryService()
        current_user_id = get_current_user_id()

        followers = cache_service.getFollowers(user_id)
        following = cache_service.getFollowing(user_id)

        is_following = str(current_user_id) in followers if followers else False

        user_data = {
            'userId': user.userId,
            'username': user.username,
            'followersCount': len(followers) if followers else 0,
            'followingCount': len(following) if following else 0,
            'is_following': is_following
        }

        posts = db.query(Post).filter(Post.postPublisher == user_id).order_by(Post.pubDate.desc()).all()
        posts_data = []
        for post in posts:
            post_dict = {
                'postId': post.postId,
                'postContent': post.postContent,
                'pubDate': post.pubDate.strftime('%Y-%m-%d %H:%M'),
                'likeCount': cache_service.getLikeCounts(post.postId),
                'isLiked': bool(cache_service.ifLike(current_user_id, post.postId))
            }
            posts_data.append(post_dict)

        return render_template('profile.html', user=user_data, posts=posts_data, current_user_id=current_user_id)
    finally:
        db.close()

@app.route('/api/like', methods=['POST'])
@login_required
def api_like():
    data = request.json
    post_id = data.get('post_id')
    current_user_id = get_current_user_id()

    if not post_id:
        return jsonify({'success': False, 'message': '参数错误'})

    db = getDatabase()
    try:
        existing = db.query(Like).filter(
            Like.userId == current_user_id,
            Like.postId == post_id
        ).first()

        cache_service = CacheService()

        if existing:
            db.delete(existing)
            db.commit()
            return jsonify({'success': True, 'action': 'unlike', 'message': '取消点赞成功'})
        else:
            like = Like(userId=current_user_id, postId=post_id)
            db.add(like)
            db.commit()
            return jsonify({'success': True, 'action': 'like', 'message': '点赞成功'})
    finally:
        db.close()

@app.route('/api/follow', methods=['POST'])
@login_required
def api_follow():
    data = request.json
    target_user_id = data.get('user_id')
    current_user_id = get_current_user_id()

    if not target_user_id or target_user_id == current_user_id:
        return jsonify({'success': False, 'message': '参数错误'})

    db = getDatabase()
    try:
        existing = db.query(Follower).filter(
            Follower.fansId == current_user_id,
            Follower.idolId == target_user_id
        ).first()

        if existing:
            db.delete(existing)
            db.commit()
            return jsonify({'success': True, 'action': 'unfollow', 'message': '取消关注成功'})
        else:
            follow = Follower(fansId=current_user_id, idolId=target_user_id)
            db.add(follow)
            db.commit()
            return jsonify({'success': True, 'action': 'follow', 'message': '关注成功'})
    finally:
        db.close()

@app.route('/api/top-likes')
@login_required
def api_top_likes():
    cache_service = CacheQueryService()
    top_posts = cache_service.getTopLike()

    db = getDatabase()
    try:
        result = []
        for post_id, like_count in top_posts:
            post = db.query(Post).options(joinedload(Post.publisher)).filter(Post.postId == post_id).first()
            if post:
                publisher_name = post.publisher.username if post.publisher else f'用户{post.postPublisher}'
                result.append({
                    'postId': post.postId,
                    'postContent': post.postContent[:50] + '...' if len(post.postContent) > 50 else post.postContent,
                    'publisherName': publisher_name,
                    'likeCount': like_count
                })
        return jsonify({'success': True, 'data': result})
    finally:
        db.close()

@app.route('/api/recommend-users')
@login_required
def api_recommend_users():
    current_user_id = get_current_user_id()
    cache_service = CacheQueryService()
    recommend = cache_service.getSameFollowing(current_user_id)

    db = getDatabase()
    try:
        result = []
        for user_id, common_count in recommend:
            user = db.query(User).filter(User.userId == user_id).first()
            if user:
                result.append({
                    'userId': user.userId,
                    'username': user.username,
                    'commonCount': common_count
                })
        return jsonify({'success': True, 'data': result})
    finally:
        db.close()

@app.route('/api/friends')
@login_required
def api_friends():
    current_user_id = get_current_user_id()
    cache_service = CacheQueryService()
    friends = cache_service.getFriends(current_user_id)

    db = getDatabase()
    try:
        result = []
        for friend_id in friends:
            user = db.query(User).filter(User.userId == int(friend_id)).first()
            if user:
                result.append({
                    'userId': user.userId,
                    'username': user.username
                })
        return jsonify({'success': True, 'data': result})
    finally:
        db.close()

@app.route('/api/init-data', methods=['POST'])
def api_init_data():
    from src.init_data import insertMockData
    insertMockData()
    return jsonify({'success': True, 'message': '数据初始化完成'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
