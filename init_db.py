from app import app
from database import db
import models

with app.app_context():
    db.create_all()
    print("データベースを作成しました！")
