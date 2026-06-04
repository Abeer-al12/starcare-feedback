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

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from flask import Response

app = Flask(__name__)
app.secret_key = "starcare_secret"

# ---------------- MONGO (Atlas) ----------------
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI is missing in environment variables")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["starcare_feedback"]
collection = db["feedback"]

# ---------------- BASE URL ----------------
BASE_URL = "https://starcare-feedback-1.onrender.com/feedback/"

# ---------------- BRANCHES ----------------
# branches = ["alhail", "mabella", "alamerat"]
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

# branch_rooms_map = {
#     # 🏥 Al Hail
#     "alhail": [
#         "consultation101",
#         "consultation102",
#         "consultation103",
#         "consultation104",
#         "cystoscopy110",
#         "urodynamic109",
#         "waiting_area",
#         "laboratory107",
#         "staff",
#         "ultrasound106",
#         "xray108",
#         "triage105",
#         "nurse",
#         "department",
#         "doctor",
#         "it",
#         "admin",
#         "toilet",
#         "sample_collaction"
#     ],

#     # 💊 Pharmacy
#     "pharmacy": [
#         "pharmacy_area",
#         "pharmacy_store",
#         "medical_area"
#     ],

#     # 🏥 Al Amerat (مثال)
#     "alamerat": [
#         "consultation201",
#         "waiting_area_2",
#         "lab_201",
#         "nurse_station_2"
#     ],

#     # 🏥 Mabella (مثال)
#     "mabella": [
#         "consultation301",
#         "xray301",
#         "ultrasound301",
#         "reception"
#     ]
# }
# ---------------- HOME ----------------
@app.route('/')
def home():
    return "StarCare System Running 🚀"

# ---------------- FEEDBACK ----------------
@app.route('/feedback/<location>', methods=['GET', 'POST'])
def feedback(location):

    if location not in locations:
        return "Invalid Location", 404

    # 👇 لازم تحطه هنا (قبل GET/POST)
    # rooms = branch_rooms_map.get(location, [])

    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        # branch = request.form.get("branch")

        if not rating:
            return "Rating required", 400

        collection.insert_one({
            # "branch": branch,
            "location": location,
            "rating": int(rating),
            "comment": comment,
            "date": datetime.now()
        })

        return render_template(
            "thankyou.html",
            location=location,
            room_name=room_names[location]
        )

    # branches = list(branch_rooms_map.keys())  # أو حطها ثابتة

    return render_template(
        "feedback.html",
        location=location,
        room_name=room_names[location],
        # branches=branches,
        # rooms=rooms
    )
# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "1234":
            session['admin'] = True
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

    data = list(collection.find().sort("date", -1))

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
        "location": loc,
        "count": v["count"],
        "avg": round(v["total"] / v["count"], 2)
    }
    for loc, v in stats.items()
]

    return render_template(
        "dashboard.html",
        data=data,
        total_feedback=total,
        avg_rating=avg,
        stats=stats_list
)


@app.route('/api/feedback')
def api_feedback():
    data = list(collection.find().sort("date", -1))

    for i in data:
        i["_id"] = str(i["_id"])
        i["date"] = str(i["date"])

    return {"data": data}

# @app.route('/get_rooms/<branch>')
# def get_rooms(branch):
#     return {"rooms": branch_rooms_map.get(branch, [])}
# ---------------- PDF ----------------
@app.route('/download_pdf')
def download_pdf():

    if 'admin' not in session:
        return redirect('/login')

    data = list(collection.find())

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

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "StarCare Hospital Feedback Report",
            styles['Title']
        )
    )

    elements.append(
        Paragraph(
            f"Date: {datetime.now().strftime('%Y-%m-%d')}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"Total Feedback: {total}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"Overall Rating: {avg} ⭐",
            styles['Normal']
        )
    )

    elements.append(Spacer(1, 20))

    rows = [["Room", "Feedbacks", "Average", "Status"]]

    for loc, v in stats.items():

        avg_loc = round(
            v["total"] / v["count"],
            2
        )

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

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "Rooms Requiring Attention",
            styles['Heading2']
        )
    )

    for loc, v in stats.items():

        avg_loc = round(
            v["total"] / v["count"],
            2
        )

        if avg_loc <= 3:

            elements.append(
                Paragraph(
                    f"• {room_names.get(loc, loc)} → Average Rating: {avg_loc}",
                    styles['Normal']
                )
            )

    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    return Response(
        pdf,
        mimetype='application/pdf',
        headers={
            'Content-Disposition':
            'attachment; filename=starcare_report.pdf'
        }
    )
# ---------------- ANALYTICS ----------------
@app.route('/analytics')
def analytics():

    if 'admin' not in session:
        return redirect('/login')

    data = list(collection.find())

    stats = {}

    # for i in data:
    #     branch = i.get("branch", "unknown")

    #     if branch not in stats:
    #         stats[branch] = {"count": 0, "total": 0}

    #     stats[branch]["count"] += 1
    #     stats[branch]["total"] += i["rating"]

    chart_data = [
        {
            "location": b,
            "count": v["count"],
            "avg": round(v["total"] / v["count"], 2)
        }
        for b, v in stats.items()
    ]

    return render_template("analytics.html", data=chart_data)

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

    for loc in locations:
        count = collection.count_documents({"location": loc})

        rooms_data.append({
            "name": loc,
            "count": count,
            "qr": BASE_URL + loc
        })

    return render_template("qr_dashboard.html", rooms=rooms_data)

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)