import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from database import db
from models import Plan, PlanItem, Place, Like, TRANSPORT_TYPES

plans = Blueprint("plans", __name__)

PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
]

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}


# ===== 共通関数 =====

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_or_create_place(name):
    place = Place.query.filter_by(name=name).first()
    if not place:
        place = Place(name=name)
        db.session.add(place)
        db.session.flush()
    return place


def save_cover_image(file):
    ext      = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return filename


def delete_cover_image(filename):
    if filename:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(path):
            os.remove(path)


def build_items_by_day(plan):
    items_by_day = {}
    for item in plan.planitems:
        items_by_day.setdefault(item.day, []).append(item)
    return items_by_day


# ===== プラン一覧 =====

@plans.route("/plans")
def plan_list():
    keyword      = request.args.get("keyword", "").strip()
    area         = request.args.get("area", "").strip()
    result_plans = []
    search_type  = None

    query = Plan.query
    if area:
        query = query.filter(Plan.area == area)

    if keyword:
        exact_place = Place.query.filter_by(name=keyword).first()
        if exact_place:
            search_type  = "exact"
            result_plans = query\
                .join(PlanItem, PlanItem.plan_id == Plan.id)\
                .filter(PlanItem.place_id == exact_place.id)\
                .distinct()\
                .order_by(Plan.created_at.desc())\
                .all()
        else:
            search_type    = "like"
            like_places    = Place.query.filter(Place.name.like(f"%{keyword}%")).all()
            like_place_ids = [p.id for p in like_places]
            if like_place_ids:
                result_plans = query\
                    .join(PlanItem, PlanItem.plan_id == Plan.id)\
                    .filter(PlanItem.place_id.in_(like_place_ids))\
                    .distinct()\
                    .order_by(Plan.created_at.desc())\
                    .all()
    else:
        result_plans = query.order_by(Plan.created_at.desc()).all()

    return render_template(
        "plan_list.html",
        plans       = result_plans,
        keyword     = keyword,
        area        = area,
        search_type = search_type,
        prefectures = PREFECTURES
    )


# ===== プラン詳細 =====

@plans.route("/plans/<int:plan_id>")
def plan_detail(plan_id):
    plan         = Plan.query.get_or_404(plan_id)
    items_by_day = build_items_by_day(plan)
    liked        = False
    if current_user.is_authenticated:
        liked = Like.query.filter_by(
            user_id=current_user.id, plan_id=plan_id
        ).first() is not None
    return render_template(
        "plan_detail.html",
        plan         = plan,
        items_by_day = items_by_day,
        liked        = liked
    )


# ===== プラン投稿 =====

@plans.route("/plans/new", methods=["GET", "POST"])
@login_required
def plan_new():
    if request.method == "POST":
        title       = request.form.get("title")
        description = request.form.get("description")
        area        = request.form.get("area")
        days        = request.form.get("days")

        if not title or not days:
            flash("タイトルと日数は必須です")
            return redirect(url_for("plans.plan_new"))

        cover_image = None
        file = request.files.get("cover_image")
        if file and file.filename != "" and allowed_file(file.filename):
            cover_image = save_cover_image(file)

        new_plan = Plan(
            user_id     = current_user.id,
            title       = title,
            description = description,
            area        = area,
            days        = int(days),
            cover_image = cover_image
        )
        db.session.add(new_plan)
        db.session.flush()

        # spotの保存
        spot_names  = request.form.getlist("spot_name")
        spot_days   = request.form.getlist("spot_day")
        spot_memos  = request.form.getlist("spot_memo")
        spot_orders = request.form.getlist("spot_order")

        for i, name in enumerate(spot_names):
            name = name.strip()
            if not name:
                continue
            place = get_or_create_place(name)
            item  = PlanItem(
                plan_id   = new_plan.id,
                day       = int(spot_days[i]),
                order     = int(spot_orders[i]),
                item_type = "spot",
                name      = name,
                memo      = spot_memos[i] if i < len(spot_memos) else None,
                place_id  = place.id
            )
            db.session.add(item)

        # moveの保存
        move_transports = request.form.getlist("move_transport")
        move_days       = request.form.getlist("move_day")
        move_durations  = request.form.getlist("move_duration")
        move_memos      = request.form.getlist("move_memo")
        move_orders     = request.form.getlist("move_order")

        for i, transport in enumerate(move_transports):
            if not transport:
                continue
            item = PlanItem(
                plan_id   = new_plan.id,
                day       = int(move_days[i]),
                order     = int(move_orders[i]),
                item_type = "move",
                transport = transport,
                duration  = int(move_durations[i]) if move_durations[i] else None,
                memo      = move_memos[i] if i < len(move_memos) else None
            )
            db.session.add(item)

        db.session.commit()
        flash("プランを投稿しました！")
        return redirect(url_for("plans.plan_detail", plan_id=new_plan.id))

    return render_template(
        "plan_new.html",
        prefectures     = PREFECTURES,
        transport_types = TRANSPORT_TYPES
    )


# ===== プラン編集 =====

@plans.route("/plans/<int:plan_id>/edit", methods=["GET", "POST"])
@login_required
def plan_edit(plan_id):
    plan = Plan.query.get_or_404(plan_id)

    if plan.user_id != current_user.id:
        flash("編集権限がありません")
        return redirect(url_for("plans.plan_detail", plan_id=plan_id))

    if request.method == "POST":
        plan.title       = request.form.get("title")
        plan.description = request.form.get("description")
        plan.area        = request.form.get("area")
        plan.days        = int(request.form.get("days"))

        # カバー画像
        file = request.files.get("cover_image")
        if file and file.filename != "" and allowed_file(file.filename):
            delete_cover_image(plan.cover_image)
            plan.cover_image = save_cover_image(file)

        # 並び順・日の更新
        item_ids    = request.form.getlist("item_id")
        item_orders = request.form.getlist("item_order")
        item_days   = request.form.getlist("item_day")

        for i, item_id in enumerate(item_ids):
            item = PlanItem.query.get(int(item_id))
            if item and item.plan_id == plan_id:
                item.order = int(item_orders[i])
                item.day   = int(item_days[i])

        db.session.commit()
        flash("プランを更新しました！")
        return redirect(url_for("plans.plan_detail", plan_id=plan_id))

    items_by_day = build_items_by_day(plan)
    return render_template(
        "plan_edit.html",
        plan            = plan,
        items_by_day    = items_by_day,
        prefectures     = PREFECTURES,
        transport_types = TRANSPORT_TYPES
    )


# ===== プラン削除 =====

@plans.route("/plans/<int:plan_id>/delete", methods=["POST"])
@login_required
def plan_delete(plan_id):
    plan = Plan.query.get_or_404(plan_id)

    if plan.user_id != current_user.id:
        flash("削除権限がありません")
        return redirect(url_for("plans.plan_detail", plan_id=plan_id))

    delete_cover_image(plan.cover_image)
    db.session.delete(plan)
    db.session.commit()
    flash("プランを削除しました")
    return redirect(url_for("index"))


# ===== いいね =====

@plans.route("/plans/<int:plan_id>/like", methods=["POST"])
@login_required
def plan_like(plan_id):
    existing = Like.query.filter_by(
        user_id=current_user.id, plan_id=plan_id
    ).first()

    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Like(user_id=current_user.id, plan_id=plan_id))

    db.session.commit()
    return redirect(url_for("plans.plan_detail", plan_id=plan_id))


# ===== planitem追加（編集画面から） =====

@plans.route("/plans/<int:plan_id>/items/add-spot", methods=["POST"])
@login_required
def item_add_spot(plan_id):
    plan = Plan.query.get_or_404(plan_id)

    if plan.user_id != current_user.id:
        flash("権限がありません")
        return redirect(url_for("plans.plan_detail", plan_id=plan_id))

    name = request.form.get("name", "").strip()
    memo = request.form.get("memo", "") or None

    if not name:
        flash("スポット名は必須です")
        return redirect(url_for("plans.plan_edit", plan_id=plan_id))

    place = get_or_create_place(name)
    item  = PlanItem(
        plan_id   = plan_id,
        day       = 1,
        order     = 999,
        item_type = "spot",
        name      = name,
        memo      = memo,
        place_id  = place.id
    )
    db.session.add(item)
    db.session.commit()
    flash("スポットを追加しました！ドラッグで並び替えて「更新する」で確定してください。")
    return redirect(url_for("plans.plan_edit", plan_id=plan_id))


@plans.route("/plans/<int:plan_id>/items/add-move", methods=["POST"])
@login_required
def item_add_move(plan_id):
    plan = Plan.query.get_or_404(plan_id)

    if plan.user_id != current_user.id:
        flash("権限がありません")
        return redirect(url_for("plans.plan_detail", plan_id=plan_id))

    transport = request.form.get("transport", "")
    duration  = request.form.get("duration", "")
    memo      = request.form.get("memo", "") or None

    if not transport:
        flash("移動手段は必須です")
        return redirect(url_for("plans.plan_edit", plan_id=plan_id))

    item = PlanItem(
        plan_id   = plan_id,
        day       = 1,
        order     = 999,
        item_type = "move",
        transport = transport,
        duration  = int(duration) if duration else None,
        memo      = memo
    )
    db.session.add(item)
    db.session.commit()
    flash("移動を追加しました！ドラッグで並び替えて「更新する」で確定してください。")
    return redirect(url_for("plans.plan_edit", plan_id=plan_id))


# ===== planitem削除 =====

@plans.route("/plans/<int:plan_id>/items/<int:item_id>/delete", methods=["POST"])
@login_required
def item_delete(plan_id, item_id):
    item = PlanItem.query.get_or_404(item_id)
    plan = Plan.query.get_or_404(plan_id)

    if plan.user_id != current_user.id:
        flash("権限がありません")
        return redirect(url_for("plans.plan_edit", plan_id=plan_id))

    db.session.delete(item)
    db.session.commit()
    flash("削除しました")
    return redirect(url_for("plans.plan_edit", plan_id=plan_id))
