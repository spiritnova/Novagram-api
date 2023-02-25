from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
import uuid as uuid
from datetime import datetime
from sqlalchemy import MetaData
from flask_cors import CORS, cross_origin


app = Flask(__name__)
CORS(app)
app.secret_key = "fksf-r1f1-1fjgk-fasrfsh:2454"

app.app_context().push()

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///novagram.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sql7600856:2KGKqCNgfD@sql7.freemysqlhosting.net:3306/sql7600856'


convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

# Intitialize the database
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db, render_as_batch=True)

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id')),
)



class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    picture = db.Column(db.String(200))
    email = db.Column(db.String(300))
    bio = db.Column(db.Text())
    followed = db.relationship(
        'Users', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return "%s, %s" % (self.name, self.username)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            db.session.commit()

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            db.session.commit()

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

class Posts(db.Model):
    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.now) 
    caption = db.Column(db.String(200))
    comments = db.relationship('Comment', backref='post')
    likes = db.relationship('Likes', backref='post')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey(Posts.post_id))
    likes = db.relationship('Likes', backref='comment')

class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey(Posts.post_id))
    comment_id = db.Column(db.Integer, db.ForeignKey(Comment.id))


@app.route("/", methods=["POST", "GET"])
@cross_origin()
def index():
    posts = []

    username = request.json.get("username")

    user = Users.query.filter_by(username=username).first()

    following = user.followed.all()

    for follow in following:
        user_posts = Posts.query.filter_by(user_id=follow.id).all()
        
        for post in user_posts:
            if post.comments:
                username = Users.query.filter_by(id=post.comments[0].user_id).first().username
                comment = {
                    "content": post.comments[0].content,
                    "username": username
                }

                data = {
                    "id": post.post_id,
                    "user": follow.username,
                    "caption": post.caption,
                    "picture": post.image,
                    "commentLength": len(post.comments),
                    "comment": comment
                }
            else:
                data ={
                    "id": post.post_id,
                    "user": follow.username,
                    "caption": post.caption,
                    "picture": post.image,
                    "commentLength": len(post.comments),
                }
            posts.append(data)
    return posts, 200

@app.route("/register", methods=["POST", "GET"])
@cross_origin()
def register():
    name = request.json.get("name")
    username = request.json.get("username")
    password = request.json.get("password")
    confirmPassword = request.json.get("confirmPassword")

    errors = {}

    if name == "" or len(name) < 4:
        errors["name"] = "Name cannot be empty or less than 4 characters"

    if username == "" or len(username) < 4:
        errors["username"] = "Username cannot be empty or less than 4 characters"
    
    if password == "" or len(password) < 8:
        errors["password"] = "Password cannot be empty or less than 8 characters"

    if password != confirmPassword:
        errors["confirmPassword"] = "Passwords do not match"

    if errors:
        return errors, 400


    # CHECK IF USERNAME ALREADY EXISTS IN THE DATABASE

    user = Users.query.filter_by(username = username).first()
    if user is None:
        user = Users(name=name, username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
    else:
        errors["username"] = "Username already exists"

    if errors:
        return errors, 400

    return ({"success" : 200})


@app.route("/login", methods=["POST", "GET"])
@cross_origin()
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    errors = {}


    if not username:
        errors["username"] = "Username cannot be blank"

    if not password:
        errors["password"] = "Password cannot be blank"

    user = Users.query.filter_by(username = username).first()

    if not user: # Check if the username exists in the database
        errors["username"] = "Username does not exist"
        return errors, 400

    userPassword = check_password_hash(user.password, password)

    if not userPassword:
        errors["password"] = "Sorry, your password was incorrect. Please double-check your password"

    if errors:
        return errors, 400

    return ({
        "success" : 200,
        "user_id": user.id,
        "username": user.username,
        "name": user.name,
        "picture": user.picture,
        "bio": user.bio,
        "email": user.email
        })

@app.route("/profile", methods=["POST", "GET"])
@cross_origin()
def post():

    picture = request.json.get("image")
    caption = request.json.get("caption")

    username = request.json.get("username")

    user = Users.query.filter_by(username = username).first()

    if picture:
        post = Posts(user_id = user.id, image=picture, caption=caption)
        db.session.add(post)
        db.session.commit()


    return({"success" : 200,})

@app.route("/profile/edit", methods=["POST", "GET"])
@cross_origin()
def edit():
    user_username = request.json.get("user")
    name = request.json.get("name")
    username = request.json.get("username")
    bio = request.json.get("bio")
    email = request.json.get("email")

    errors = {}

    if not name:
        errors["name"] = "Name cannot be blank"

    if not username:
        errors["username"] = "Username cannot be blank"

    if not user_username:
        errors["userError"] = "User error"

    if errors:
        return errors, 400

    user = Users.query.filter_by(username = user_username).first()  
    getUser = Users.query.filter_by(username=username).first()


    if getUser.username != user.username:
        if getUser is None:
            user.username = username
            user.name = name
            user.bio = bio
            user.email = email
            db.session.commit()
        else:
            errors["username"] = "username already exists"
            return errors, 400

    user.name = name
    user.bio = bio
    user.email = email
    db.session.commit()


    if errors:
        return errors, 400
        
    return ({
        "success": 200, 
        "message": "Profile has been edited",
        "data": {
            "username" : user.username,
            "name": user.name,
            "bio": user.bio,
            "email": user.email
        }
        })

@app.route("/<username>")
@cross_origin()
def getPosts(username):
    posts = []

    user = Users.query.filter_by(username = username).first() # Get the user from the 
    
    if not user:
        return "Not Found", 404

    if user: # If the user exists
        getPosts = Posts.query.filter_by(user_id = user.id).all()


        for post in getPosts:
            data = {
                "id": post.post_id,
                "image": post.image,
                "caption": post.caption,
            }
            posts.append(data)

    postCount = len(posts)

    return ({
        "posts": posts,
        "count": postCount,
        })

@app.route("/post/<id>", methods=["get"])
@cross_origin()
def getPost(id):
    comments = []
    likes = []
    post = Posts.query.filter_by(post_id=id).first()
    user = Users.query.filter_by(id=post.user_id).first()

    for comment in post.comments:
        commentUser = Users.query.filter_by(id = comment.user_id).first()

        commentLikes = []

        for like in comment.likes:
            likeUser = Users.query.filter_by(id=like.user_id).first()
            likeData = {
                "id": like.id,
                "username": likeUser.username,
                "picture": likeUser.picture,
            }

            commentLikes.append(likeData)

        data = {
            "id": comment.id,
            "username": commentUser.username,
            "picture": commentUser.picture,
            "content": comment.content,
            "likes": commentLikes
        }
        comments.append(data)

    for like in post.likes:
        likeUser = Users.query.filter_by(id = like.user_id).first()
        likesData = {
            "id": like.id,
            "username": likeUser.username,
            "picture": likeUser.picture,
        }
        likes.append(likesData)    
    date = post.date_time.strftime("%B %d, %Y")

    return ({"success": 200,
            "data":{
                "id": post.post_id,
                "image": post.image,
                "caption": post.caption,
                "date":date,
                "comments": comments,
                "likes": likes,
                "username": user.username,
                "picture": user.picture,
            }
        })

@app.route("/profile/picture", methods=["post", "get"])
@cross_origin()
def setPfp():
    image = request.json.get("image")

    print(image)
    username = request.json.get("username")

    user = Users.query.filter_by(username = username).first()

    if image:
        user.picture = image
        db.session.commit()

    return ({"success" : 200})

if __name__=="__main__":
    app.run(debug=True)

@app.route("/comment", methods=["POST", "GET"])
@cross_origin()
def comment():
    comment = request.json.get("comment")
    user_id = request.json.get("user_id")
    id = request.json.get("id")

    if comment:
        cmnt = Comment(content = comment, post_id=id, user_id=user_id)
        db.session.add(cmnt)
        db.session.commit()
    
    return ({"success" : 200})

@app.route("/post/like", methods=["POST", "GET"])
@cross_origin()
def like():
    status = request.json.get("status")
    post_id = request.json.get("post_id")
    user_id = request.json.get("user_id")

    post_like = Likes.query.filter_by(user_id = user_id, post_id=post_id).first()

    if post_id:
        if post_like:
            db.session.delete(post_like)
            db.session.commit()

        else:
            like = Likes(status = status, post_id = post_id, user_id=user_id)
            db.session.add(like)
            db.session.commit()
    return({"success" : 200})

@app.route("/post/delete", methods=["POST", "GET"])
@cross_origin()
def delete():
    post_id = request.json.get("id")

    post = Posts.query.filter_by(post_id = post_id).first()

    if post:
        db.session.delete(post)
        db.session.commit()

    return ({"success" : 200})

@app.route("/comment/like", methods=["POST", "GET"])
@cross_origin()
def commentLike():
    comment_id = request.json.get("id")
    post_id = request.json.get("post_id")
    user_id = request.json.get("user_id")

    comment_like = Likes.query.filter_by(comment_id=comment_id).first()

    # print(comment_like)

    if comment_id:
        if comment_like:
            db.session.delete(comment_like)
            db.session.commit()
        else:
            like = Likes(status = True, comment_id = comment_id, user_id=user_id, post_id=post_id)
            db.session.add(like)
            db.session.commit()
    return({"success" : 200})

@app.route("/user/<username>", methods=["POST", "GET"])
@cross_origin()
def user(username): 
    followings = []
    followerss = []

    followings2 = []
    followerss2 = []

    user = Users.query.filter_by(username = username).first()

    if not user:
        return "Invalid username", 404

    username = request.json.get("username")

    currentUser = Users.query.filter_by(username = username).first()

    following = currentUser.followed.all()
    for follow in following:
        data = {
            "name": follow.name,
            "username": follow.username,
            "picture": follow.picture,
        }
        followings.append(data)
    followers = currentUser.followers.all()

    for follower in followers:
        followerData = {
            "name": follower.name,
            "username": follower.username,
            "picture": follower.picture
        }
        followerss.append(followerData)


    following2 = user.followed.all()
    for follow2 in following2:
        data2 = {
            "name": follow2.name,
            "username": follow2.username,
            "picture": follow2.picture
        }
        followings2.append(data2)

    followers2 = user.followers.all()
    for follower2 in followers2:
        follower2Data = {
           "name": follower2.name,
           "username": follower2.username,
           "picture": follower2.picture
        }
        followerss2.append(follower2Data)
    if user:
        return ({
            "id" : user.id,
            "username": user.username,
            "name": user.name,
            "picture": user.picture,
            "bio" : user.bio,
            "following": followings,
            "followers": followerss,
            "user_following": followings2,
            "user_followers": followerss2
        })

@app.route("/explore")
@cross_origin()
def explore():

    allPosts = []

    page = request.args.get('page', 1, type=int)

    posts = Posts.query.paginate(page=page, per_page=20)

    for post in posts.items:
        data = {
            "id": post.post_id,
            "image": post.image
        }
        allPosts.append(data)

    return allPosts

@app.route("/follow", methods=["POST", "GET"])
@cross_origin()
def follow():
    state = request.json.get("state")
    getfollower = request.json.get("follower")
    getfollowed = request.json.get("followed")

    errors = {}

    follower = Users.query.filter_by(username = getfollower).first()
    followed = Users.query.filter_by(username = getfollowed).first()

    if follower == followed:
        errors["ERROR": "you can't follow yourself"]

    if state:
        follower.follow(followed)

    else:
        follower.unfollow(followed)

    if errors:
        return errors, 400
    return "Followed", 200

@app.route("/search/<value>")
@cross_origin()
def search(value):
    usersList = []
    users = Users.query.all()

    for user in users:
        if value != '':
            if value in user.username.lower():
                data = {
                    "username": user.username,
                    "name": user.name,
                    "picture": user.picture
                }
                usersList.append(data)

    return usersList , 200

@app.route("/test")
@cross_origin()
def test():
    return ({
        "test": "test 1"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    