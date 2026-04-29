from flask import Flask
from flask import render_template
from src.queryDB import DBQueryService
import os

base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir,'static'))

@app.route('/')
def home():

    query_service = DBQueryService()
    
    post_id = [1, 2, 3, 4, 5]
    posts = []
    
    for i in post_id:
        post = query_service.getPostInfo(i)
        posts.append(post)
    
    return render_template('homepage.html', posts=posts)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)