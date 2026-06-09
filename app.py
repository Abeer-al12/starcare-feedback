from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from datetime import datetime
import os
import qrcode
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from dotenv import load_dotenv

load_dotenv()
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from flask import Response
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "starcare_secret"


# ---------------- MONGO (Atlas) ----------------
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI is missing in environment variables")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["starcare_feedback"]
collection = db["feedback"]
users_collection = db["users"]

# db.users.insert_one({
#     "username": "admin",
#     "password": "1234",
#     "role": "admin"
# })

# db.users.insert_one({
#     "username": "it_head",
#     "password": "1234",
#     "role": "it"
# })
# ---------------- BASE URL ----------------
BASE_URL = "https://starcare-feedback-1.onrender.com/"

# ---------------- BRANCHES ----------------
# branches = ["alhail", "mabella", "alamerat"]

users = {
    "admin": {"password": "1234", "role": "admin"},
    "it_head": {"password": "1111", "role": "it"},
    "alhail_head": {"password": "2222", "role": "alhail"},
    "mabella_head": {"password": "3333", "role": "mabella"},
}
# ---------------- LOCATIONS ----------------
locations = [
    "consultation101","consultation102","consultation103","consultation104",
    "cystoscopy110","urodynamic109","waiting_area",
    "laboratory107","staff","ultrasound106","xray108",
    "triage105","nurse","department","doctor","it","admin","toilet","sample_collaction"
]

# ---------------- ROOM NAMES ----------------
room_names = {
    "consultation101":"Consultation Room 101",
    "consultation102":"Consultation Room 102",
    "consultation103":"Consultation Room 103",
    "consultation104":"Consultation Room 104",
    "cystoscopy110":"Cystoscopy Room 110",
    "urodynamic109":"Urodynamic Room 109",
    "waiting_area":"Waiting Area",
    "laboratory107":"Laboratory 107",
    "ultrasound106":"Ultrasound Room 106",
    "xray108":"X-Ray Room 108",
    "triage105":"Triage Room 105",
    "staff":"Staff Area",
    "nurse":"Nurse Station",
    "department":"Department",
    "doctor":"Doctor Office",
    "it":"IT Department",
    "admin":"Administration",
    "toilet":"Restroom",
    "sample_collaction":"sample collection room"
}

branch_rooms_map = {
    # 🏥 Al Hail
    "alhail": [
        "consultation101",
        "consultation102",
        "consultation103",
        "consultation104",
        "cystoscopy110",
        "urodynamic109",
        "waiting_area",
        "laboratory107",
        "staff",
        "ultrasound106",
        "xray108",
        "triage105",
        "nurse",
        "department",
        "doctor",
        "it",
        "admin",
        "toilet",
        "sample_collaction"
    ],

    # 💊 Pharmacy
    "pharmacy": [
        "pharmacy_area",
        "pharmacy_store",
        "medical_area"
    ],

    # 🏥 Al Amerat (مثال)
    "alamerat": [
        "consultation201",
        "waiting_area_2",
        "lab_201",
        "nurse_station_2"
    ],

    # 🏥 Mabella (مثال)
    "mabella": [
        "consultation301",
        "xray301",
        "ultrasound301",
        "reception"
    ]
}

branches = list(branch_rooms_map.keys())

def get_branch_from_location(location):
    for branch, rooms in branch_rooms_map.items():
        if location in rooms:
            return branch
    return "unknown"
# ---------------- HOME ----------------
@app.route('/')
def home():
    return "StarCare System Running 🚀"

# ---------------- FEEDBACK ----------------
# @app.route('/feedback/<location>', methods=['GET', 'POST'])
# def feedback(location):

#     if location not in locations:
#         return "Invalid Location", 404

#     if request.method == 'POST':

#         rating = request.form.get('rating')
#         comment = request.form.get('comment')

#         if not rating:
#             return {"error": "missing rating"}

#         rating = int(rating)

#     # ⭐ 4 و 5 → حفظ مباشر
#         if rating >= 4:

#             collection.insert_one({
#                 "location": location,
#                 "branch": get_branch_from_location(location),  # ✔ مهم
#                 "rating": rating,
#                 "comment": comment,
#                 "phone": None,
#                 "date": datetime.now()
#             })

#             return {"need_phone": False}

#     # ⭐ 1 - 3 → نطلب رقم
#         return {
#             "need_phone": True,
#             "rating": rating,
#             "comment": comment,
#             "location": location
#         }

#     return render_template(
#         "feedback.html",
#         location=location,
#         room_name=room_names.get(location, "Unknown Room"),
#         need_phone=False
#     )


@app.route('/feedback/<branch>/<room>', methods=['GET', 'POST'])
def feedback(branch, room):

    if request.method == 'POST':

        rating = request.form.get('rating')
        comment = request.form.get('comment')

        if not rating:
            return {"error": "missing rating"}

        rating = int(rating)

        # ⭐ 4-5 → شكر مباشر
        if rating >= 4:

            collection.insert_one({
                "branch": branch,
                "location": room,
                "rating": rating,
                "comment": comment,
                "phone": None,
                "date": datetime.now()
            })

            return {"status": "success", "redirect": "/thankyou"}

        # ⭐ 1-3 → نطلب رقم
        return {
            "status": "need_phone",
            "rating": rating,
            "comment": comment,
            "branch": branch,
            "room": room
        }

    return render_template(
        "feedback.html",
        branch=branch,
        room=room,
        room_name=room_names.get(room, room)
    )


@app.route('/save_low_rating', methods=['POST'])
def save_low_rating():

    data = request.json

    collection.insert_one({
        "location": data["location"],
        "branch": get_branch_from_location(data["location"]),  # 👈 مهم
        "rating": int(data["rating"]),
        "comment": data["comment"],
        "phone": data["phone"],
        "date": datetime.now()
    })

    return {"success": True}


@app.route('/thankyou/<location>')
def thankyou(location):

    name = room_names.get(location, "Unknown Room")

    return render_template(
        "thankyou.html",
        location=location,
        room_name=name
    )
# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = db.users.find_one({
            "username": username,
            "password": password
        })

        if user:

            session['admin'] = True
            session['role'] = user["role"]
            session['username'] = username

            return redirect('/admin')

        return "Wrong credentials"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():

    if 'admin' not in session:
        return redirect('/login')

    role = session.get("role")
    username = session.get("username")

    selected_location = request.args.get("location")
    active_branch = request.args.get("branch")

    if active_branch:
        session["active_branch"] = active_branch
    else:
        active_branch = session.get("active_branch")

    user = db.users.find_one({"username": username})
    allowed_locations = user.get("locations", []) if user else []

    # =========================
    # 🔥 QUERY الأساسي
    # =========================
    query = {}

# 🔐 صلاحيات
    if role != "admin":
        query["location"] = {"$in": allowed_locations}

# 🌟 branch filter (أقوى من location)
    if active_branch:
        query["branch"] = active_branch

# 🌟 location فقط إذا ما فيه branch ولا role restriction
    elif selected_location:
        query["location"] = selected_location


    # =========================
    # 📊 البيانات الرئيسية
    # =========================
    data = list(collection.find(query).sort("date", -1))

    # =========================
    # ⚠️ Low ratings (مهم)
    # =========================
    low_ratings = list(collection.find({
        **query,
        "rating": {"$lte": 3}
    }).sort("date", -1))

    # =========================
    # 📈 الإحصائيات
    # =========================
    total = len(data)
    avg = round(sum(i["rating"] for i in data) / total, 2) if total else 0

    stats = {}

    for i in data:
        loc = i.get("location")

        if loc not in stats:
            stats[loc] = {"count": 0, "total": 0}

        stats[loc]["count"] += 1
        stats[loc]["total"] += i["rating"]

    stats_list = [
        {
            "location": l,
            "count": v["count"],
            "avg": round(v["total"] / v["count"], 2)
        }
        for l, v in stats.items()
    ]

    # =========================
    # 🚀 branches (حل الخطأ)
    # =========================
    branches = list(branch_rooms_map.keys())

    return render_template(
        "dashboard.html",
        data=data,
        low_ratings=low_ratings,
        total_feedback=total,
        avg_rating=avg,
        stats=stats_list,
        role=role,
        branches=branches,
        active_branch=active_branch
    )

#اضافه مستخدمين
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():

    if session.get("role") != "admin":
        return "Forbidden", 403

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # ⭐ هذا الجديد
        locations = request.form.getlist('locations')

        db.users.insert_one({
            "username": username,
            "password": password,
            "role": role,
            "locations": locations
        })

        return redirect('/manage_users')

    return render_template("add_user.html")

#حذف مستخدمين 
@app.route('/delete_user/<username>')
def delete_user(username):

    if session.get("role") != "admin":
        return "Forbidden", 403

    db.users.delete_one({"username": username})

    return redirect('/manage_users')

    #عرض مستخدمين 
@app.route('/manage_users')
def manage_users():

    if session.get("role") != "admin":
        return "Forbidden", 403

    users = list(db.users.find())

    return render_template("manage_users.html", users=users)

@app.route('/add_role', methods=['GET', 'POST'])
def add_role():

    if session.get("role") != "admin":
        return "Forbidden", 403

    if request.method == 'POST':

        role = request.form['role']
        locations = request.form.getlist('locations')

        db.roles.insert_one({
            "role": role,
            "locations": locations
        })

        return redirect('/admin')

    return render_template("add_role.html")

@app.route('/api/feedback')
def api_feedback():
    data = list(collection.find().sort("date", -1))

    for i in data:
        i["_id"] = str(i["_id"])
        i["date"] = str(i["date"])

    return {"data": data}

@app.route('/delete_feedback/<id>')
def delete_feedback(id):

    if 'admin' not in session:
        return redirect('/login')

    collection.delete_one({
        "_id": ObjectId(id)
    })

    return redirect('/admin')
# ---------------- PDF ----------------
@app.route('/download_pdf')
def download_pdf():

    if 'admin' not in session:
        return redirect('/login')

    role = session.get("role")

    # 🌿 هنا تحط الفرع
    branch = session.get("active_branch")

    query = {}

    # 🌿 فلترة الفرع (هذا هو التعديل المهم)
    if branch:
        query["branch"] = branch

    # 📦 جلب البيانات
    data = list(collection.find(query))

    # (حذفنا هذا الغلط القديم)
    # data = list(collection.find()) ❌

    # 🔢 الحسابات
    total = len(data)

    avg = round(
        sum(i["rating"] for i in data) / total,
        2
    ) if total else 0

    stats = {}

    for i in data:

        loc = i["location"]

        if loc not in stats:
            stats[loc] = {
                "count": 0,
                "total": 0
            }

        stats[loc]["count"] += 1
        stats[loc]["total"] += i["rating"]

    # 📄 PDF generation
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph("StarCare Hospital Feedback Report", styles['Title'])
    )

    elements.append(
        Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal'])
    )

    elements.append(
        Paragraph(f"Total Feedback: {total}", styles['Normal'])
    )

    elements.append(
        Paragraph(f"Overall Rating: {avg} ⭐", styles['Normal'])
    )

    elements.append(Spacer(1, 20))

    rows = [["Room", "Feedbacks", "Average", "Status"]]

    for loc, v in stats.items():

        avg_loc = round(v["total"] / v["count"], 2)

        if avg_loc <= 2:
            status = "CRITICAL"
        elif avg_loc <= 3:
            status = "NEEDS IMPROVEMENT"
        elif avg_loc <= 4:
            status = "GOOD"
        else:
            status = "EXCELLENT"

        rows.append([
            room_names.get(loc, loc),
            str(v["count"]),
            str(avg_loc),
            status
        ])

    table = Table(rows)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#59e3ec")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    elements.append(table)

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    return Response(
        pdf,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': 'attachment; filename=starcare_report.pdf'
        }
    )
# ---------------- ANALYTICS ----------------
@app.route('/analytics')
def analytics():

    if 'admin' not in session:
        return redirect('/login')

    # 🌿 الفرع الحالي
    branch = session.get("active_branch")

    # 📦 query
    query = {}

    if branch:
        query["branch"] = branch

    # 📊 جلب البيانات
    data = list(collection.find(query))

    # 📈 stats
    stats = {}

    for i in data:
        loc = i.get("location")

        if loc not in stats:
            stats[loc] = {"count": 0, "total": 0}

        stats[loc]["count"] += 1
        stats[loc]["total"] += i["rating"]

    chart_data = [
        {
            "location": room_names.get(loc, loc),
            "count": v["count"],
            "avg": round(v["total"] / v["count"], 2)
        }
        for loc, v in stats.items()
    ]

    return render_template(
        "analytics.html",
        data=chart_data
    )
# ---------------- GENERATE QR ----------------
@app.route('/generate_qr')
def generate_qr():

    os.makedirs("qr_codes", exist_ok=True)

    for loc in locations:
        img = qrcode.make(BASE_URL + loc)
        img.save(f"qr_codes/{loc}.png")

    return "QR Generated Successfully"

# ---------------- QR DASHBOARD ----------------
@app.route('/qr_dashboard')
def qr_dashboard():

    rooms_data = []

    for branch, rooms in branch_rooms_map.items():

        for room in rooms:

            rooms_data.append({
                "branch": branch,
                "room": room,
                "name": room_names.get(room, room),
                "count": collection.count_documents({
                    "branch": branch,
                    "location": room
                }),
                "qr": f"{BASE_URL}/feedback/{branch}/{room}"
            })

    return render_template("qr_dashboard.html", rooms=rooms_data)

# @app.route('/fix_branch')
# def fix_branch():

#     for i in collection.find():

#         if "branch" not in i or not i.get("branch"):

#             collection.update_one(
#                 {"_id": ObjectId(i["_id"])},
#                 {"$set": {"branch": get_branch_from_location(i["location"])}}
#             )

#     return "DONE"
# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)