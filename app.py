from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
    jsonify,
    Response
)

import os
import sqlite3
import joblib
import pandas as pd
import requests
from bs4 import BeautifulSoup

from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = "SmartVillage_Electricity_Management_2026"


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "users.db"
)

DEMAND_DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "powerdemand_5min_2021_to_2024_with weather.csv"
)

ABNORMAL_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "sgcc_random_forest.pkl"
)

LOAD_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "load_forecasting_model.pkl"
)


# ============================================================
# GLOBAL DATA
# ============================================================

demand_df = pd.DataFrame()

abnormal_model = None

load_model = None


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    conn = get_db()

    # --------------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL,

            phone TEXT,

            department TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(email, role)

        )
        """
    )

    # --------------------------------------------------------
    # COMPLAINTS TABLE
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            name TEXT,

            email TEXT,

            complaint_type TEXT,

            description TEXT,

            status TEXT DEFAULT 'Pending',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    # --------------------------------------------------------
    # AI ALERTS TABLE
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_alerts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            alert_type TEXT,

            message TEXT,

            severity TEXT,

            status TEXT DEFAULT 'Active',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    conn.commit()

    conn.close()


# ============================================================
# LOAD ELECTRICITY DEMAND DATA
# ============================================================

def load_demand_data():

    global demand_df

    if not os.path.exists(DEMAND_DATA_PATH):

        print()
        print("WARNING:")
        print("Electricity demand dataset not found.")
        print(DEMAND_DATA_PATH)
        print()

        demand_df = pd.DataFrame()

        return

    try:

        print()
        print("Loading electricity demand dataset...")

        demand_df = pd.read_csv(
            DEMAND_DATA_PATH
        )

        print(
            "Dataset shape:",
            demand_df.shape
        )

        # ----------------------------------------------------
        # DATETIME
        # ----------------------------------------------------

        if "datetime" in demand_df.columns:

            demand_df["datetime"] = pd.to_datetime(
                demand_df["datetime"],
                errors="coerce"
            )

        # ----------------------------------------------------
        # POWER DEMAND
        # ----------------------------------------------------

        if "Power demand" in demand_df.columns:

            demand_df["Power demand"] = pd.to_numeric(
                demand_df["Power demand"],
                errors="coerce"
            )

        demand_df = demand_df.dropna(
            subset=["datetime", "Power demand"]
        )

        demand_df = demand_df.sort_values(
            "datetime"
        ).reset_index(drop=True)

        print(
            "Clean demand data:",
            demand_df.shape
        )

        print("Demand dataset loaded successfully.")

    except Exception as e:

        print(
            "Error loading demand dataset:",
            e
        )

        demand_df = pd.DataFrame()


# ============================================================
# LOAD AI MODELS
# ============================================================

def load_models():

    global abnormal_model
    global load_model

    # --------------------------------------------------------
    # ABNORMAL CONSUMPTION MODEL
    # --------------------------------------------------------

    if os.path.exists(ABNORMAL_MODEL_PATH):

        try:

            abnormal_model = joblib.load(
                ABNORMAL_MODEL_PATH
            )

            print(
                "Abnormal consumption model loaded."
            )

        except Exception as e:

            print(
                "Error loading abnormal model:",
                e
            )

    else:

        print(
            "WARNING: Abnormal model not found."
        )

    # --------------------------------------------------------
    # LOAD FORECASTING MODEL
    # --------------------------------------------------------

    if os.path.exists(LOAD_MODEL_PATH):

        try:

            load_model = joblib.load(
                LOAD_MODEL_PATH
            )

            print(
                "Load forecasting model loaded."
            )

        except Exception as e:

            print(
                "Error loading load model:",
                e
            )

    else:

        print(
            "WARNING: Load forecasting model not found."
        )


# ============================================================
# AUTHENTICATION HELPERS
# ============================================================

def is_logged_in():

    return "user_id" in session


def current_user():

    if not is_logged_in():

        return None

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return user


def user_required():

    user = current_user()

    if user is None:

        session.clear()

        return False

    return user["role"] == "user"


def officer_required():

    user = current_user()

    if user is None:

        session.clear()

        return False

    return user["role"] == "officer"


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if user is None:

        session.clear()

        return redirect(
            url_for("login")
        )

    if user["role"] == "officer":

        return redirect(
            url_for("officer_dashboard")
        )

    return redirect(
        url_for("user_dashboard")
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    error = None

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        role = request.form.get(
            "role",
            "user"
        ).strip().lower()

        if not email or not password:

            error = "Please enter email and password."

            return render_template(
                "login.html",
                error=error
            )

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND role = ?
            """,
            (email, role)
        ).fetchone()

        conn.close()

        if user is None:

            error = (
                "Account not found. "
                "Please check email, password and role."
            )

            return render_template(
                "login.html",
                error=error
            )

        if not check_password_hash(
            user["password"],
            password
        ):

            error = "Incorrect password."

            return render_template(
                "login.html",
                error=error
            )

        session.clear()

        session["user_id"] = user["id"]

        session["role"] = user["role"]

        if user["role"] == "officer":

            return redirect(
                url_for("officer_dashboard")
            )

        return redirect(
            url_for("user_dashboard")
        )

    return render_template(
        "login.html",
        error=error
    )


# ============================================================
# REGISTRATION
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    error = None

    success = None

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        department = request.form.get(
            "department",
            ""
        ).strip()

        role = request.form.get(
            "role",
            "user"
        ).strip().lower()

        if role not in [
            "user",
            "officer"
        ]:

            role = "user"

        if not name or not email or not password:

            error = (
                "Name, email and password are required."
            )

            return render_template(
                "register.html",
                error=error
            )

        if len(password) < 6:

            error = (
                "Password must contain at least "
                "6 characters."
            )

            return render_template(
                "register.html",
                error=error
            )

        hashed_password = generate_password_hash(
            password
        )

        try:

            conn = get_db()

            conn.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    role,
                    phone,
                    department
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    hashed_password,
                    role,
                    phone,
                    department
                )
            )

            conn.commit()

            conn.close()

            success = (
                "Registration successful. "
                "You can now login."
            )

            return render_template(
                "register.html",
                success=success
            )

        except sqlite3.IntegrityError:

            error = (
                "An account with this email "
                "and role already exists."
            )

            return render_template(
                "register.html",
                error=error
            )

        except Exception as e:

            error = str(e)

            return render_template(
                "register.html",
                error=error
            )

    return render_template(
        "register.html"
    )


# ============================================================
# USER DASHBOARD
# ============================================================

@app.route("/user")
def user_dashboard():

    if not user_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "user_dashboard.html",
        user=current_user()
    )


# ============================================================
# USER CONSUMPTION PAGE
# ============================================================

@app.route("/user/consumption")
def user_consumption():

    if not user_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "user_consumption.html",
        user=current_user()
    )


# ============================================================
# USER CONSUMPTION API
# ============================================================

@app.route("/api/user/consumption")
def user_consumption_api():

    if not user_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    if demand_df.empty:

        return jsonify([])

    df = demand_df.tail(50).copy()

    result = []

    for _, row in df.iterrows():

        result.append({

            "datetime":
                row["datetime"].strftime(
                    "%Y-%m-%d %H:%M"
                ),

            "consumption":
                round(
                    float(row["Power demand"]),
                    2
                )

        })

    return jsonify(result)


# ============================================================
# USER BILL PAGE
# ============================================================

@app.route("/user/bill")
def user_bill():

    if not user_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "user_bill.html",
        user=current_user()
    )


# ============================================================
# USER NOTIFICATIONS
# ============================================================

@app.route("/user/notifications")
def user_notifications():

    if not user_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "user_notifications.html",
        user=current_user()
    )


# ============================================================
# USER PROFILE
# ============================================================

@app.route("/profile")
def profile():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if user is None:

        session.clear()

        return redirect(
            url_for("login")
        )

    return render_template(
        "profile.html",
        user=user
    )


# ============================================================
# USER HELP & SUPPORT
# ============================================================

@app.route(
    "/user/help",
    methods=["GET", "POST"]
)
def user_help():

    if not user_required():

        return redirect(
            url_for("login")
        )

    message = None

    error = None

    user = current_user()

    if request.method == "POST":

        complaint_type = request.form.get(
            "complaint_type",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not complaint_type or not description:

            error = (
                "Please select complaint type "
                "and enter description."
            )

        else:

            conn = get_db()

            conn.execute(
                """
                INSERT INTO complaints
                (
                    user_id,
                    name,
                    email,
                    complaint_type,
                    description
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    user["name"],
                    user["email"],
                    complaint_type,
                    description
                )
            )

            conn.commit()

            conn.close()

            message = (
                "Complaint submitted successfully."
            )

    return render_template(
        "user_help.html",
        user=user,
        message=message,
        error=error
    )


# ============================================================
# USER DASHBOARD SUMMARY API
# ============================================================

@app.route("/api/user/summary")
def user_summary_api():

    if not user_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    if demand_df.empty:

        return jsonify({
            "current": 0,
            "average": 0,
            "maximum": 0,
            "status": "Data Unavailable"
        })

    current = float(
        demand_df.iloc[-1]["Power demand"]
    )

    average = float(
        demand_df["Power demand"].mean()
    )

    maximum = float(
        demand_df["Power demand"].max()
    )

    return jsonify({

        "current":
            round(current, 2),

        "average":
            round(average, 2),

        "maximum":
            round(maximum, 2),

        "status":
            "Online"

    })


# ============================================================
# GENERAL DEMAND API
# ============================================================

@app.route("/api/demand")
def demand_api():

    if not is_logged_in():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    if demand_df.empty:

        return jsonify([])

    df = demand_df.tail(100).copy()

    result = []

    for _, row in df.iterrows():

        result.append({

            "datetime":
                row["datetime"].strftime(
                    "%Y-%m-%d %H:%M"
                ),

            "demand":
                round(
                    float(row["Power demand"]),
                    2
                )

        })

    return jsonify(result)
# ============================================================
# CURRENT MSEDCL DEMAND API
# ============================================================

@app.route("/api/current-demand")
def current_demand_api():

    if not officer_required():

        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    MSEDCL_URL = (
        "https://www.mahadiscom.in/en/msedcl-peak-demand-en/"
    )

    try:

        # ----------------------------------------------------
        # REQUEST OFFICIAL MSEDCL PAGE
        # ----------------------------------------------------

        response = requests.get(
            MSEDCL_URL,
            timeout=15,
            headers={
                "User-Agent":
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/140 Safari/537.36"
            }
        )

        response.raise_for_status()


        # ----------------------------------------------------
        # PARSE HTML
        # ----------------------------------------------------

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # ----------------------------------------------------
        # FIND CURRENT STATUS TABLE
        # ----------------------------------------------------

        tables = soup.find_all("table")


        if not tables:

            return jsonify({

                "success": False,

                "error":
                    "MSEDCL demand table was not found."

            }), 503


        status_values = {}


        # ----------------------------------------------------
        # SEARCH ALL TABLE ROWS
        # ----------------------------------------------------

        for table in tables:

            rows = table.find_all("tr")

            for row in rows:

                cells = row.find_all(
                    ["td", "th"]
                )

                values = [

                    cell.get_text(
                        " ",
                        strip=True
                    )

                    for cell in cells

                ]


                if len(values) < 2:

                    continue


                field = values[0]

                value = values[1]

                date = (
                    values[2]
                    if len(values) >= 3
                    else ""
                )


                status_values[field] = {

                    "value": value,

                    "date": date

                }


        # ----------------------------------------------------
        # HELPER FUNCTION
        # ----------------------------------------------------

        def get_value(
            field_name
        ):

            item = status_values.get(
                field_name,
                {}
            )

            value = item.get(
                "value"
            )

            date = item.get(
                "date",
                ""
            )

            if value is None:

                return None, ""

            try:

                numeric_value = float(
                    str(value)
                    .replace(",", "")
                    .strip()
                )

            except Exception:

                numeric_value = None


            return (
                numeric_value,
                date
            )


        # ----------------------------------------------------
        # EXTRACT VALUES
        # ----------------------------------------------------

        demand_catered, demand_date = \
            get_value(
                "DEMAND_CATERED"
            )


        monthly_peak, monthly_peak_date = \
            get_value(
                "DEMAND_CATERED_MONTH"
            )


        yearly_peak, yearly_peak_date = \
            get_value(
                "DEMAND_CATERED_YEAR"
            )


        yearly_till_date, yearly_till_date_date = \
            get_value(
                "DEMAND_CATERED_TILL"
            )


        morning_peak, morning_peak_date = \
            get_value(
                "MORNING_PEAK"
            )


        day_peak, day_peak_date = \
            get_value(
                "DAY_PEAK"
            )


        evening_peak, evening_peak_date = \
            get_value(
                "EVENING_PEAK"
            )


        night_minimum, night_minimum_date = \
            get_value(
                "NIGHT_MINIMUM"
            )


        # ----------------------------------------------------
        # VALIDATE CURRENT DATA
        # ----------------------------------------------------

        if demand_catered is None:

            return jsonify({

                "success": False,

                "error":
                    "Current MSEDCL demand could not be read."

            }), 503


        # ----------------------------------------------------
        # RETURN JSON
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "source":
                "MSEDCL Official Peak Demand",

            "source_url":
                MSEDCL_URL,

            "demand_catered":
                round(
                    demand_catered,
                    2
                ),

            "demand_date":
                demand_date,

            "monthly_peak":
                round(
                    monthly_peak,
                    2
                )
                if monthly_peak is not None
                else None,

            "monthly_peak_date":
                monthly_peak_date,

            "yearly_peak":
                round(
                    yearly_peak,
                    2
                )
                if yearly_peak is not None
                else None,

            "yearly_peak_date":
                yearly_peak_date,

            "yearly_till_date":
                round(
                    yearly_till_date,
                    2
                )
                if yearly_till_date is not None
                else None,

            "yearly_till_date_date":
                yearly_till_date_date,

            "morning_peak":
                round(
                    morning_peak,
                    2
                )
                if morning_peak is not None
                else None,

            "morning_peak_date":
                morning_peak_date,

            "day_peak":
                round(
                    day_peak,
                    2
                )
                if day_peak is not None
                else None,

            "day_peak_date":
                day_peak_date,

            "evening_peak":
                round(
                    evening_peak,
                    2
                )
                if evening_peak is not None
                else None,

            "evening_peak_date":
                evening_peak_date,

            "night_minimum":
                round(
                    night_minimum,
                    2
                )
                if night_minimum is not None
                else None,

            "night_minimum_date":
                night_minimum_date,

            "data_scope":
                "Maharashtra-wide MSEDCL grid demand"

        })


    except requests.RequestException as e:

        return jsonify({

            "success": False,

            "error":
                "Could not connect to MSEDCL: "
                + str(e)

        }), 503


    except Exception as e:

        return jsonify({

            "success": False,

            "error":
                "Error reading MSEDCL data: "
                + str(e)

        }), 500


# ============================================================
# OFFICER DASHBOARD
# ============================================================

@app.route("/officer")
def officer_dashboard():

    if not officer_required():

        return redirect(
            url_for("login")
        )

    conn = get_db()

    total_complaints = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        """
    ).fetchone()[0]

    pending_complaints = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'Pending'
        """
    ).fetchone()[0]

    resolved_complaints = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'Resolved'
        """
    ).fetchone()[0]

    total_ai_alerts = conn.execute(
        """
        SELECT COUNT(*)
        FROM ai_alerts
        """
    ).fetchone()[0]

    active_ai_alerts = conn.execute(
        """
        SELECT COUNT(*)
        FROM ai_alerts
        WHERE status = 'Active'
        """
    ).fetchone()[0]

    conn.close()

    current_demand = 0

    average_demand = 0

    maximum_demand = 0

    minimum_demand = 0

    system_status = "Data Unavailable"

    if not demand_df.empty:

        current_demand = float(
            demand_df.iloc[-1]["Power demand"]
        )

        average_demand = float(
            demand_df["Power demand"].mean()
        )

        maximum_demand = float(
            demand_df["Power demand"].max()
        )

        minimum_demand = float(
            demand_df["Power demand"].min()
        )

        system_status = "Online"

    return render_template(

        "officer_dashboard.html",

        user=current_user(),

        total_complaints=total_complaints,

        pending_complaints=pending_complaints,

        resolved_complaints=resolved_complaints,

        total_ai_alerts=total_ai_alerts,

        active_ai_alerts=active_ai_alerts,

        current_demand=round(
            current_demand,
            2
        ),

        average_demand=round(
            average_demand,
            2
        ),

        maximum_demand=round(
            maximum_demand,
            2
        ),

        minimum_demand=round(
            minimum_demand,
            2
        ),

        system_status=system_status
    )


# ============================================================
# OFFICER DASHBOARD SUMMARY API
# ============================================================

@app.route("/api/officer/summary")
def officer_summary_api():

    if not officer_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    conn = get_db()

    total_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    pending_complaints = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'Pending'
        """
    ).fetchone()[0]

    resolved_complaints = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'Resolved'
        """
    ).fetchone()[0]

    total_ai_alerts = conn.execute(
        "SELECT COUNT(*) FROM ai_alerts"
    ).fetchone()[0]

    active_ai_alerts = conn.execute(
        """
        SELECT COUNT(*)
        FROM ai_alerts
        WHERE status = 'Active'
        """
    ).fetchone()[0]

    conn.close()

    if demand_df.empty:

        current_demand = 0
        average_demand = 0
        maximum_demand = 0
        minimum_demand = 0

    else:

        current_demand = float(
            demand_df.iloc[-1]["Power demand"]
        )

        average_demand = float(
            demand_df["Power demand"].mean()
        )

        maximum_demand = float(
            demand_df["Power demand"].max()
        )

        minimum_demand = float(
            demand_df["Power demand"].min()
        )

    return jsonify({

        "total_complaints":
            total_complaints,

        "pending_complaints":
            pending_complaints,

        "resolved_complaints":
            resolved_complaints,

        "total_ai_alerts":
            total_ai_alerts,

        "active_ai_alerts":
            active_ai_alerts,

        "current_demand":
            round(current_demand, 2),

        "average_demand":
            round(average_demand, 2),

        "maximum_demand":
            round(maximum_demand, 2),

        "minimum_demand":
            round(minimum_demand, 2)

    })


# ============================================================
# ANALYTICS PAGE
# ============================================================

@app.route("/analytics")
def analytics():

    if not officer_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "analytics.html",
        user=current_user()
    )


# ============================================================
# ANALYTICS API
# ============================================================

@app.route("/api/analytics")
def analytics_api():

    if not officer_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    try:

        if demand_df.empty:

            return jsonify({

                "summary": {},

                "recent": [],

                "hourly": [],

                "daily": []

            })

        df = demand_df.copy()

        # ----------------------------------------------------
        # CLEAN DATA
        # ----------------------------------------------------

        df["datetime"] = pd.to_datetime(
            df["datetime"],
            errors="coerce"
        )

        df["Power demand"] = pd.to_numeric(
            df["Power demand"],
            errors="coerce"
        )

        df = df.dropna(
            subset=[
                "datetime",
                "Power demand"
            ]
        )

        df = df.sort_values(
            "datetime"
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        current_demand = float(
            df.iloc[-1]["Power demand"]
        )

        average_demand = float(
            df["Power demand"].mean()
        )

        maximum_demand = float(
            df["Power demand"].max()
        )

        minimum_demand = float(
            df["Power demand"].min()
        )

        # ----------------------------------------------------
        # RECENT READINGS
        # ----------------------------------------------------

        recent_df = df.tail(100)

        recent = []

        for _, row in recent_df.iterrows():

            recent.append({

                "datetime":
                    row["datetime"].strftime(
                        "%Y-%m-%d %H:%M"
                    ),

                "demand":
                    round(
                        float(
                            row["Power demand"]
                        ),
                        2
                    )

            })

        # ----------------------------------------------------
        # HOURLY AVERAGE
        # ----------------------------------------------------

        df["hour"] = (
            df["datetime"].dt.hour
        )

        hourly_df = (
            df.groupby("hour")[
                "Power demand"
            ]
            .mean()
            .reset_index()
        )

        hourly = []

        for _, row in hourly_df.iterrows():

            hourly.append({

                "hour":
                    int(row["hour"]),

                "average":
                    round(
                        float(
                            row["Power demand"]
                        ),
                        2
                    )

            })

        # ----------------------------------------------------
        # DAY OF WEEK AVERAGE
        # ----------------------------------------------------

        df["day_of_week"] = (
            df["datetime"].dt.dayofweek
        )

        day_names = [

            "Monday",

            "Tuesday",

            "Wednesday",

            "Thursday",

            "Friday",

            "Saturday",

            "Sunday"

        ]

        daily_df = (
            df.groupby("day_of_week")[
                "Power demand"
            ]
            .mean()
            .reset_index()
        )

        daily = []

        for _, row in daily_df.iterrows():

            day_number = int(
                row["day_of_week"]
            )

            daily.append({

                "day":
                    day_names[day_number],

                "average":
                    round(
                        float(
                            row["Power demand"]
                        ),
                        2
                    )

            })

        return jsonify({

            "summary": {

                "current":
                    round(
                        current_demand,
                        2
                    ),

                "average":
                    round(
                        average_demand,
                        2
                    ),

                "maximum":
                    round(
                        maximum_demand,
                        2
                    ),

                "minimum":
                    round(
                        minimum_demand,
                        2
                    )

            },

            "recent": recent,

            "hourly": hourly,

            "daily": daily

        })

    except Exception as e:

        return jsonify({

            "error":
                str(e)

        }), 500


# ============================================================
# LOAD FORECASTING PAGE
# ============================================================

@app.route("/forecasting")
def forecasting():

    if not officer_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "forecasting.html",
        user=current_user()
    )


# ============================================================
# LOAD FORECASTING API
# ============================================================

# ============================================================
# LOAD FORECASTING API
# ============================================================

@app.route(
    "/api/forecast",
    methods=["POST"]
)
def forecast_api():

    if not officer_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    if load_model is None:

        return jsonify({
            "error": "Load forecasting model is not available."
        }), 500

    if demand_df.empty:

        return jsonify({
            "error": "Electricity demand dataset is not available."
        }), 500

    try:

        data = request.get_json(silent=True) or {}

        hour = int(data.get("hour", 18))
        day = int(data.get("day", 15))
        month = int(data.get("month", 9))
        day_of_week = int(data.get("day_of_week", 0))

        if not 0 <= hour <= 23:
            raise ValueError("Hour must be between 0 and 23.")

        if not 1 <= day <= 31:
            raise ValueError("Day must be between 1 and 31.")

        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12.")

        if not 0 <= day_of_week <= 6:
            raise ValueError("Day of week must be between 0 and 6.")

        input_data = pd.DataFrame([[
            hour,
            day,
            month,
            day_of_week
        ]], columns=[
            "hour",
            "day",
            "month",
            "day_of_week"
        ])

        prediction = float(
            load_model.predict(input_data)[0]
        )

        return jsonify({
            "success": True,
            "hour": hour,
            "day": day,
            "month": month,
            "day_of_week": day_of_week,
            "predicted_demand": round(prediction, 2)
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


# ============================================================
# FESTIVAL ELECTRICITY FORECAST API
# ============================================================

@app.route(
    "/api/festival-forecast",
    methods=["POST"]
)
def festival_forecast_api():

    try:

        data = request.get_json()

        # -----------------------------
        # User inputs
        # -----------------------------

        location = data.get(
            "location",
            ""
        )

        festival = data.get(
            "festival",
            ""
        )

        people = int(
            data.get("people", 0)
        )

        extra_people = int(
            data.get("extra_people", 0)
        )

        temperature = float(
            data.get("temperature", 30)
        )

        fan = int(
            data.get("fan", 0)
        )

        ac = int(
            data.get("ac", 0)
        )

        tv = int(
            data.get("tv", 0)
        )

        fridge = int(
            data.get("fridge", 0)
        )

        pump = int(
            data.get("pump", 0)
        )

        geyser = int(
            data.get("geyser", 0)
        )

        lights = int(
            data.get("lights", 0)
        )

        usage_hours = float(
            data.get("usage_hours", 0)
        )


        # -----------------------------
        # Load festival model
        # -----------------------------

        import joblib
        import numpy as np

        FESTIVAL_MODEL_FILE = (
            "models/"
            "festival_demand_forecasting_model.pkl"
        )

        FESTIVAL_DATA_FILE = (
            "data/processed/"
            "final_forecasting_data.csv"
        )

        festival_model = joblib.load(
            FESTIVAL_MODEL_FILE
        )

        festival_df = pd.read_csv(
            FESTIVAL_DATA_FILE
        )


        # -----------------------------
        # Latest available data
        # -----------------------------

        latest = (
            festival_df
            .dropna()
            .iloc[-1]
        )


        # -----------------------------
        # Forecast time
        # -----------------------------

        hour = 19
        day = 15
        month = 9
        day_of_week = 5

        is_weekend = int(
            day_of_week >= 5
        )


        hour_sin = np.sin(
            2 * np.pi * hour / 24
        )

        hour_cos = np.cos(
            2 * np.pi * hour / 24
        )

        month_sin = np.sin(
            2 * np.pi * month / 12
        )

        month_cos = np.cos(
            2 * np.pi * month / 12
        )


        # Festival indicators

        is_festival = 1
        is_public_holiday = 1
        festival_day = 1


        # -----------------------------
        # Prepare model input
        # -----------------------------

        input_data = pd.DataFrame([{

            "hour": hour,

            "day": day,

            "month": month,

            "day_of_week": day_of_week,

            "is_weekend": is_weekend,

            "hour_sin": hour_sin,

            "hour_cos": hour_cos,

            "month_sin": month_sin,

            "month_cos": month_cos,

            "temp": temperature,

            "dwpt": latest["dwpt"],

            "rhum": latest["rhum"],

            "wdir": latest["wdir"],

            "wspd": latest["wspd"],

            "pres": latest["pres"],

            "is_festival": is_festival,

            "is_public_holiday":
                is_public_holiday,

            "festival_day":
                festival_day,

            "demand_lag_1":
                latest["demand_lag_1"],

            "demand_lag_48":
                latest["demand_lag_48"],

            "demand_lag_96":
                latest["demand_lag_96"],

            "demand_lag_336":
                latest["demand_lag_336"],

            "rolling_mean_48":
                latest["rolling_mean_48"],

            "rolling_mean_336":
                latest["rolling_mean_336"]

        }])


        # -----------------------------
        # AI baseline prediction
        # -----------------------------

        base_prediction = (
            festival_model
            .predict(input_data)[0]
        )


        # -----------------------------
        # Scenario adjustment
        # -----------------------------

        total_people = (
            people +
            extra_people
        )


        people_factor = (
            1 +
            (
                extra_people /
                max(people, 1)
            ) * 0.10
        )


        appliance_count = (

            fan +
            ac +
            tv +
            fridge +
            pump +
            geyser +
            lights

        )


        appliance_factor = (

            1 +
            (
                appliance_count *
                usage_hours *
                0.005
            )

        )


        final_prediction = (

            base_prediction *
            people_factor *
            appliance_factor

        )


        additional_demand = (

            final_prediction -
            base_prediction

        )


        # -----------------------------
        # Return result
        # -----------------------------

        return jsonify({

            "success": True,

            "location": location,

            "festival": festival,

            "normal_people":
                people,

            "extra_people":
                extra_people,

            "total_people":
                total_people,

            "temperature":
                temperature,

            "ai_baseline_demand":
                round(
                    float(base_prediction),
                    2
                ),

            "scenario_demand":
                round(
                    float(final_prediction),
                    2
                ),

            "additional_demand":
                round(
                    float(additional_demand),
                    2
                ),

            "note":
                "Extra people and appliance values "
                "are scenario inputs, not historical "
                "migration data."

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 400
# ============================================================
# ABNORMAL DETECTION PAGE
# ============================================================

@app.route("/abnormal")
def abnormal():

    if not officer_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "abnormal.html",
        user=current_user()
    )


# ============================================================
# ABNORMAL DETECTION API
# ============================================================

@app.route(
    "/api/abnormal",
    methods=["POST"]
)
def abnormal_api():

    if not officer_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    if abnormal_model is None:

        return jsonify({

            "error":
                "Abnormal detection model "
                "is not available."

        }), 500

    try:

        data = request.get_json()

        input_data = pd.DataFrame({

            "mean_consumption": [
                float(
                    data["mean_consumption"]
                )
            ],

            "max_consumption": [
                float(
                    data["max_consumption"]
                )
            ],

            "min_consumption": [
                float(
                    data["min_consumption"]
                )
            ],

            "std_consumption": [
                float(
                    data["std_consumption"]
                )
            ],

            "total_consumption": [
                float(
                    data["total_consumption"]
                )
            ]

        })

        prediction = abnormal_model.predict(
            input_data
        )

        prediction_value = int(
            prediction[0]
        )

        # ----------------------------------------------------
        # CREATE ALERT IF ABNORMAL
        # ----------------------------------------------------

        if prediction_value == 1:

            conn = get_db()

            conn.execute(

                """
                INSERT INTO ai_alerts
                (
                    alert_type,
                    message,
                    severity
                )
                VALUES (?, ?, ?)
                """,

                (

                    "Abnormal Consumption",

                    (
                        "AI model detected an "
                        "abnormal consumption pattern. "
                        "Field verification is required."
                    ),

                    "High"

                )

            )

            conn.commit()

            conn.close()

        return jsonify({

            "prediction":
                prediction_value

        })

    except Exception as e:

        return jsonify({

            "error":
                str(e)

        }), 400


# ============================================================
# ALERTS PAGE
# ============================================================

@app.route("/alerts")
def alerts():

    if not officer_required():

        return redirect(
            url_for("login")
        )

    conn = get_db()

    ai_alerts = conn.execute(

        """
        SELECT *
        FROM ai_alerts
        ORDER BY id DESC
        LIMIT 50
        """

    ).fetchall()

    complaints = conn.execute(

        """
        SELECT *
        FROM complaints
        ORDER BY id DESC
        LIMIT 50
        """

    ).fetchall()

    conn.close()

    return render_template(

        "alerts.html",

        user=current_user(),

        ai_alerts=ai_alerts,

        complaints=complaints

    )


# ============================================================
# COMPLAINTS API
# ============================================================

@app.route("/api/complaints")
def complaints_api():

    if not officer_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    conn = get_db()

    complaints = conn.execute(

        """
        SELECT *
        FROM complaints
        ORDER BY id DESC
        """

    ).fetchall()

    conn.close()

    result = []

    for complaint in complaints:

        result.append({

            "id":
                complaint["id"],

            "name":
                complaint["name"],

            "email":
                complaint["email"],

            "complaint_type":
                complaint["complaint_type"],

            "description":
                complaint["description"],

            "status":
                complaint["status"],

            "created_at":
                complaint["created_at"]

        })

    return jsonify(result)


# ============================================================
# UPDATE COMPLAINT STATUS
# ============================================================

@app.route(
    "/api/complaints/<int:complaint_id>/status",
    methods=["POST"]
)
def update_complaint_status(
    complaint_id
):

    if not officer_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    try:

        data = request.get_json()

        status = data.get(
            "status",
            "Pending"
        )

        allowed_statuses = [

            "Pending",

            "In Progress",

            "Resolved",

            "Closed"

        ]

        if status not in allowed_statuses:

            return jsonify({

                "error":
                    "Invalid status."

            }), 400

        conn = get_db()

        conn.execute(

            """
            UPDATE complaints
            SET status = ?
            WHERE id = ?
            """,

            (
                status,
                complaint_id
            )

        )

        conn.commit()

        conn.close()

        return jsonify({

            "success":
                True,

            "message":
                "Complaint status updated."

        })

    except Exception as e:

        return jsonify({

            "error":
                str(e)

        }), 400


# ============================================================
# REPORTS PAGE
# ============================================================

@app.route("/reports")
def reports():

    if not officer_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "reports.html",
        user=current_user()
    )


# ============================================================
# DEMAND CSV REPORT
# ============================================================

@app.route("/reports/demand.csv")
def demand_csv():

    if not officer_required():

        return redirect(
            url_for("login")
        )

    if demand_df.empty:

        csv_data = (
            "datetime,Power demand\n"
        )

    else:

        report_df = demand_df.copy()

        report_df = report_df[
            [
                "datetime",
                "Power demand"
            ]
        ]

        csv_data = report_df.to_csv(
            index=False
        )

    return Response(

        csv_data,

        mimetype="text/csv",

        headers={

            "Content-Disposition":
                "attachment; "
                "filename=demand_report.csv"

        }

    )


# ============================================================
# ALERT CSV REPORT
# ============================================================


@app.route("/api/alerts-summary")
def alerts_summary_api():

    if not officer_required():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()

    total_alerts = conn.execute(
        "SELECT COUNT(*) FROM ai_alerts"
    ).fetchone()[0]

    total_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    pending_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Pending'"
    ).fetchone()[0]

    resolved_complaints = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status IN ('Resolved', 'Closed')
        """
    ).fetchone()[0]

    conn.close()

    return jsonify({
        "total_alerts": total_alerts,
        "total_complaints": total_complaints,
        "pending_complaints": pending_complaints,
        "resolved_complaints": resolved_complaints
    })
# ============================================================
# COMPLAINT CSV REPORT
# ============================================================

@app.route("/reports/complaints.csv")
def complaints_csv():

    if not officer_required():

        return redirect(
            url_for("login")
        )

    conn = get_db()

    complaints_data = conn.execute(

        """
        SELECT
            id,
            name,
            email,
            complaint_type,
            description,
            status,
            created_at
        FROM complaints
        ORDER BY id DESC
        """

    ).fetchall()

    conn.close()

    rows = []

    for complaint in complaints_data:

        rows.append({

            "id":
                complaint["id"],

            "name":
                complaint["name"],

            "email":
                complaint["email"],

            "complaint_type":
                complaint["complaint_type"],

            "description":
                complaint["description"],

            "status":
                complaint["status"],

            "created_at":
                complaint["created_at"]

        })

    report_df = pd.DataFrame(rows)

    if report_df.empty:

        csv_data = (
            "id,name,email,complaint_type,"
            "description,status,created_at\n"
        )

    else:

        csv_data = report_df.to_csv(
            index=False
        )

    return Response(

        csv_data,

        mimetype="text/csv",

        headers={

            "Content-Disposition":
                "attachment; "
                "filename=complaints_report.csv"

        }

    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )



# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """

    <!DOCTYPE html>

    <html>

    <head>

        <title>Page Not Found</title>

        <style>

            body {
                font-family: Arial;
                background: #f4f7fb;
                text-align: center;
                padding: 100px;
            }

            h1 {
                font-size: 60px;
                color: #102a43;
            }

            a {
                text-decoration: none;
                background: #1976d2;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
            }

        </style>

    </head>

    <body>

        <h1>404</h1>

        <h2>Page Not Found</h2>

        <p>
            The page you requested does not exist.
        </p>

        <a href="/">
            Go Home
        </a>

    </body>

    </html>

    """, 404


# ============================================================
# 500 ERROR
# ============================================================

@app.errorhandler(500)
def internal_error(error):

    return """

    <!DOCTYPE html>

    <html>

    <head>

        <title>Server Error</title>

        <style>

            body {
                font-family: Arial;
                background: #f4f7fb;
                text-align: center;
                padding: 100px;
            }

            h1 {
                color: #b91c1c;
            }

        </style>

    </head>

    <body>

        <h1>Something went wrong</h1>

        <p>
            Please check the VS Code terminal
            for the error message.
        </p>

        <a href="/">
            Go Home
        </a>

    </body>

    </html>

    """, 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("SMART VILLAGE ELECTRICITY MANAGEMENT SYSTEM")
    print("=" * 60)

    print()

    # Initialize database
    init_db()

    # Load electricity demand dataset
    load_demand_data()

    # Load trained AI models
    load_models()

    print()
    print("Application starting...")
    print()
    print("Login page:")
    print("http://127.0.0.1:5000/login")
    print()
    print("Register page:")
    print("http://127.0.0.1:5000/register")
    print()
    print("Analytics:")
    print("http://127.0.0.1:5000/analytics")
    print()
    print("=" * 60)

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )