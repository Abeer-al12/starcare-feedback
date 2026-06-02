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

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect('/login')

    data = list(collection.find().sort("date", -1))

    total_feedback = len(data)

    avg_rating = round(
        sum(i["rating"] for i in data) / total_feedback, 2
    ) if total_feedback else 0

    stats = {}

    for i in data:
        loc = i["location"]
        stats.setdefault(loc, {"count":0, "total":0})
        stats[loc]["count"] += 1
        stats[loc]["total"] += i["rating"]

    stats_list = [
        {
            "location": loc,
            "count": v["count"],
            "avg": round(v["total"]/v["count"], 2)
        }
        for loc, v in stats.items()
    ]

    return render_template(
        "dashboard.html",
        data=data,
        total_feedback=total_feedback,
        avg_rating=avg_rating,
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
        stats.setdefault(loc, {"count":0, "total":0})
        stats[loc]["count"] += 1
        stats[loc]["total"] += i["rating"]

    chart_data = [
        {
            "location": loc,
            "count": v["count"],
            "avg": round(v["total"]/v["count"], 2)
        }
        for loc, v in stats.items()
    ]

    return render_template("analytics.html", data=chart_data)

# ---------------- QR ----------------
@app.route('/generate_qr')
def generate_qr():

    folder = "qr_codes"
    os.makedirs(folder, exist_ok=True)

    for loc in locations:
        img = qrcode.make(BASE_URL + loc)
        img.save(f"{folder}/{loc}.png")

    return "QR Generated Successfully"

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)