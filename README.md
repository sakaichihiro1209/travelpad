# travelpad

旅行プランを投稿・共有できる投稿型Webサービスです。

## 技術スタック

- Python / Flask
- Flask-SQLAlchemy / SQLite
- Flask-Login
- HTMX
- Sortable.js

## セットアップ手順

```bash
# 1. 仮想環境の作成・有効化
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. ライブラリのインストール
pip install -r requirements.txt

# 3. .envファイルの作成
copy .env.example .env       # Windows
cp .env.example .env         # Mac/Linux

# .envのSECRET_KEYを設定（Pythonで生成）
# python -c "import secrets; print(secrets.token_hex(32))"

# 4. DBの作成
python init_db.py

# 5. サーバー起動
python app.py
```

## ファイル構成

```
travelpad/
├── app.py              # エントリーポイント
├── database.py         # SQLAlchemyインスタンス
├── models.py           # DBモデル
├── auth.py             # 認証Blueprint
├── plans.py            # プランBlueprint
├── init_db.py          # DB初期化
├── requirements.txt
├── .env.example
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── plan_list.html
│   ├── plan_detail.html
│   ├── plan_new.html
│   ├── plan_edit.html
│   └── mypage.html
└── static/
    ├── css/style.css
    └── uploads/        # 画像保存先（自動作成）
```
# travelpad
