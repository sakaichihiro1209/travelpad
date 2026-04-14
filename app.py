import os
from flask import Flask, render_template
from flask_login import LoginManager, login_required
from dotenv import load_dotenv
from database import db
from sqlalchemy import func

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"]               = os.environ.get("SECRET_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"]  = "sqlite:///travelpad.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"]            = os.path.join("static", "uploads")
app.config["MAX_CONTENT_LENGTH"]       = 2 * 1024 * 1024  # 2MB

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

@app.route("/")
def index():
    from models import Plan
    new_plans     = Plan.query.order_by(Plan.created_at.desc()).limit(6).all()
    popular_plans = Plan.query\
        .outerjoin(Plan.likes)\
        .group_by(Plan.id)\
        .order_by(func.count().desc())\
        .limit(6).all()
    return render_template("index.html", new_plans=new_plans, popular_plans=popular_plans)

@app.route("/mypage")
@login_required
def mypage():
    return render_template("mypage.html")

@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"]        = "no-cache"
    response.headers["Expires"]       = "0"
    return response

from auth import auth
from plans import plans
app.register_blueprint(auth)
app.register_blueprint(plans)

if __name__ == "__main__":
    app.run(debug=True)
