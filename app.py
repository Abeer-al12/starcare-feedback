from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from datetime import datetime
import qrcode
import os

app = Flask(__name__)
app.secret_key = "starcare_secret"

# ---------------- MONGO ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["starcare_feedback"]
collection = db["feedback"]

# ---------------- BASE URL (IMPORTANT) ----------------
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
@app.route('/feedback/<location>', methods=['GET','POST'])
def feedback(location):

    if location not in locations:
        return "Invalid Location", 404

    if request.method == 'POST':

        data = {
            "location": location,
            "rating": int(request.form['rating']),
            "comment": request.form['comment'],
            "date": datetime.now()
        }

        collection.insert_one(data)

        return render_template(
            "thankyou.html",
            location=location,
            room_name=room_names[location]
        )

    return render_template(
    "feedback.html",
    location=location,
    room_name=room_names[location],
    locations=locations
)

# ---------------- ADMIN LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

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

# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin():

    if 'admin' not in session:
        return redirect('/login')

    data = list(collection.find().sort("date", -1))

    total_feedback = len(data)

    avg_rating = round(
        sum([i["rating"] for i in data]) / total_feedback, 2
    ) if total_feedback > 0 else 0

    stats_dict = {}

    for i in data:
        loc = i["location"]

        if loc not in stats_dict:
            stats_dict[loc] = {"count":0, "total":0}

        stats_dict[loc]["count"] += 1
        stats_dict[loc]["total"] += i["rating"]

    stats = []

    for loc, val in stats_dict.items():
        stats.append({
            "location": loc,
            "count": val["count"],
            "avg": round(val["total"]/val["count"], 2)
        })

    return render_template(
        "dashboard.html",
        data=data,
        total_feedback=total_feedback,
        avg_rating=avg_rating,
        stats=stats
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
            stats[loc] = {"count":0, "total":0}

        stats[loc]["count"] += 1
        stats[loc]["total"] += i["rating"]

    chart_data = []

    for loc, val in stats.items():
        chart_data.append({
            "location": loc,
            "count": val["count"],
            "avg": round(val["total"]/val["count"], 2)
        })

    return render_template("analytics.html", data=chart_data)

# ---------------- QR GENERATE ----------------
@app.route('/generate_qr')
def generate_qr():

    folder = "qr_codes"
    os.makedirs(folder, exist_ok=True)

    for loc in locations:

        img = qrcode.make(BASE_URL + loc)
        img.save(f"{folder}/{loc}.png")

    return "QR Generated Successfully ✅"

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
    app.run()