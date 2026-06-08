# VPS deployment

Linux VPS に travelpad を置いてテストするための最短手順です。

## 1. Code

```bash
git clone <repository-url> travelpad
cd travelpad
```

Git を使わない場合は、`venv/`、`.env`、`__pycache__/`、`travelpad.db` を除いたファイルを VPS に配置します。

## 2. Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Environment variables

`.env` を作成します。

```env
SECRET_KEY=replace-with-a-random-secret
DATABASE_URL=sqlite:///travelpad.db
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

`SECRET_KEY` は次のコマンドで生成できます。

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

SQLite で短期テストする場合は `DATABASE_URL=sqlite:///travelpad.db` のままで動きます。PostgreSQL を使う場合は `DATABASE_URL` に PostgreSQL の接続 URL を設定します。

## 4. Database

```bash
python init_db.py
```

初期データを投入する場合は、必要に応じて次も実行します。

```bash
python seed.py
```

## 5. Start test server

```bash
gunicorn -b 0.0.0.0:8000 app:app
```

ブラウザで `http://<server-ip>:8000` を開きます。VPS 側の firewall / security group で TCP `8000` を許可してください。

## 6. systemd example

常時起動したい場合は `/etc/systemd/system/travelpad.service` を作ります。

```ini
[Unit]
Description=travelpad
After=network.target

[Service]
User=<linux-user>
WorkingDirectory=/home/<linux-user>/travelpad
EnvironmentFile=/home/<linux-user>/travelpad/.env
ExecStart=/home/<linux-user>/travelpad/venv/bin/gunicorn -b 0.0.0.0:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now travelpad
sudo systemctl status travelpad
```
