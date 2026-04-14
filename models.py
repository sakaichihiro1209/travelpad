from database import db
from datetime import datetime
from flask_login import UserMixin

TRANSPORT_TYPES = [
    "電車", "バス", "車", "徒歩", "飛行機", "船", "タクシー", "自転車"
]

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.Text, nullable=False)
    email         = db.Column(db.Text, nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    profile_image = db.Column(db.Text, nullable=True)
    bio           = db.Column(db.Text, nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    plans         = db.relationship("Plan", backref="author")
    likes         = db.relationship("Like", backref="user")

class Plan(db.Model):
    __tablename__ = "plans"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title       = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    area        = db.Column(db.Text, nullable=True)
    days        = db.Column(db.Integer, nullable=False)
    cover_image = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    planitems   = db.relationship("PlanItem", backref="plan",
                                  order_by="PlanItem.day, PlanItem.order",
                                  cascade="all, delete-orphan")
    likes       = db.relationship("Like", backref="plan",
                                  cascade="all, delete-orphan")

class PlanItem(db.Model):
    __tablename__ = "planitems"
    id         = db.Column(db.Integer, primary_key=True)
    plan_id    = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    day        = db.Column(db.Integer, nullable=False)
    order      = db.Column(db.Integer, nullable=False)
    item_type  = db.Column(db.Text, nullable=False)    # "spot" or "move"
    name       = db.Column(db.Text, nullable=True)     # spotのみ
    memo       = db.Column(db.Text, nullable=True)     # 共通
    duration   = db.Column(db.Integer, nullable=True)  # moveのみ（分）
    transport  = db.Column(db.Text, nullable=True)     # moveのみ
    place_id   = db.Column(db.Integer, db.ForeignKey("places.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Place(db.Model):
    __tablename__ = "places"
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

class Like(db.Model):
    __tablename__ = "likes"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id    = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
