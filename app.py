from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from datetime import datetime
import os
import qrcode

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

# ---------------- LOCATIONS ----------------
locations = [
    "consultation101","consultation102","consultation103","consultation104",
    "cystoscopy110","urodynamic109","waiting_area",
    "laboratory107","staff","ultrasound106","xray108",
    "triage105","nurse","department","doctor","it","admin","toilet"
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
    "toilet":"Restroom"
}

# ---------------- HOME ----------------
@app.route('/')
def home():
    return "StarCare System Running 🚀"

# ---------------- FEEDBACK ----------------
@app.route('/feedback/<location>', methods=['GET', 'POST'])
def feedback(location):

    if location not in locations:
        return "Invalid Location", 404

    if request.method == 'POST':
        try:
            rating = request.form.get('rating')
            comment = request.form.get('comment')

            if not rating:
                return "Rating required", 400

            data = {
                "location": location,
                "rating": int(rating),
                "comment": comment,
                "date": datetime.now()
            }

            collection.insert_one(data)

            return render_template(
                "thankyou.html",
                location=location,
                room_name=room_names[location]
            )

        except Exception as e:
            print("ERROR:", e)
            return f"Server Error: {e}", 500

    return render_template(
        "feedback.html",
        location=location,
        room_name=room_names[location]
    )

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':
        if request.form['username'] == "admin" and request.form['password'] == "1234":
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
        loc = i["location"]
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

# ---------------- ANALYTICS ----------------
@app.route('/analytics')
def analytics():

    if 'admin' not in session:
        return redirect('/login')

    data = list(collection.find())

    stats = {}

    for i in data:
        loc = i["location"]
        if loc not in stats:
            stats[loc] = {"count": 0, "total": 0}

        stats[loc]["count"] += 1
        stats[loc]["total"] += i["rating"]

    chart_data = [
        {
            "location": loc,
            "count": v["count"],
            "avg": round(v["total"] / v["count"], 2)
        }
        for loc, v in stats.items()
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