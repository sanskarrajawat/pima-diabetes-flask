# ================================
# IMPORTS
# ================================
from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
import joblib
from datetime import datetime

# ================================
# CREATE APP
# ================================
app = Flask(__name__)
app.secret_key = "123"   # session login key

# ================================
# LOAD ML MODEL
# ================================
model = joblib.load("diabetes_model.pkl")

# ================================
# CONNECT MONGODB
# ================================
client = MongoClient("mongodb+srv://rajawatsanskar740:Vaira%400388@cluster0.amjdd1i.mongodb.net/")
db = client["diabetes_db"]

print("MongoDB Connected 👍")


# ==========================================================
# 1️⃣ HOME PAGE
# ==========================================================
@app.route("/")
def home():
    return render_template("home.html")


# ==========================================================
# 2️⃣ LOGIN PAGE
# ==========================================================
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        role = request.form["role"]
        username = request.form["username"]
        password = request.form["password"]

        if role == "user" and username == "user" and password == "":
            session["role"] = "user"
            return redirect("/predict_page")

        if role == "admin" and username == "admin" and password == "vaibhav":
            session["role"] = "admin"
            return redirect("/dashboard")

        return "❌ Wrong Username or Password"

    return render_template("login.html")


# ==========================================================
# 3️⃣ LOGOUT
# ==========================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ==========================================================
# 4️⃣ ADMIN DASHBOARD
# ==========================================================
@app.route("/dashboard")
def dashboard():

    data = list(db.predictions.find().sort("time", -1).limit(10))

    total = len(data)
    high = sum(1 for d in data if d.get("prediction") == 1)
    low  = sum(1 for d in data if d.get("prediction") == 0)

    return render_template(
        "dashboard.html",
        data=data,
        total=total,
        high=high,
        low=low
    )
# ==========================================================
# 5️⃣ USER PREDICTION PAGE
# ==========================================================
@app.route("/predict_page")
def predict_page():

    if "role" not in session:
        return redirect("/login")

    return render_template("predict.html")


# ==========================================================
# 6️⃣ ML PREDICTION API
# ==========================================================
@app.route("/predict", methods=["POST"])
def predict():

    try:
        data = request.json

        # ---------- Convert values safely ----------
        input_data = [[
            float(data.get("Pregnancies", 0)),
            float(data.get("Glucose", 0)),
            float(data.get("BloodPressure", 0)),
            float(data.get("SkinThickness", 0)),
            float(data.get("Insulin", 0)),
            float(data.get("BMI", 0)),
            float(data.get("DiabetesPedigreeFunction", 0)),
            float(data.get("Age", 0))
        ]]

        # ---------- Validation ----------
        if input_data[0][7] < 1 or input_data[0][7] > 120:
            return jsonify({"error": "Invalid Age"})
        if input_data[0][5] < 10 or input_data[0][5] > 70:
            return jsonify({"error": "Invalid BMI"})

        # ---------- Prediction ----------
        prediction = int(model.predict(input_data)[0])

        # some models don't support predict_proba
        try:
            prob = float(model.predict_proba(input_data)[0][1])
        except:
            prob = 0.5

        # ---------- Save MongoDB ----------
        db.predictions.insert_one({
            "input": data,
            "prediction": prediction,
            "probability": prob,
            "time": datetime.now()
        })

        return jsonify({
            "prediction": prediction,
            "probability": round(prob * 100, 2)
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Prediction failed. Check input values."})


# ==========================================================
# RUN APP
# ==========================================================
if __name__ == "__main__":
    app.run(debug=True)