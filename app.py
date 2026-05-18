"""
CalcMaster - Python Flask Calculator App
Supports: Basic Math, EMI, BMI, Percentage, Compound Interest, Age, Unit Converter, Tip
"""

from flask import Flask, render_template, request, jsonify
from datetime import date, datetime
import math
import os

app = Flask(__name__)


# ─── CALCULATOR FUNCTIONS ────────────────────────────────────────────

def calc_emi(principal: float, annual_rate: float, months: int) -> dict:
    """Calculate Equated Monthly Installment."""
    if principal <= 0 or annual_rate < 0 or months <= 0:
        raise ValueError("All values must be positive.")
    if annual_rate == 0:
        emi = principal / months
        return {
            "emi": round(emi, 2),
            "total_amount": round(emi * months, 2),
            "total_interest": 0.0,
            "principal": principal,
        }
    r = annual_rate / 12 / 100
    emi = (principal * r * math.pow(1 + r, months)) / (math.pow(1 + r, months) - 1)
    total_amount = emi * months
    return {
        "emi": round(emi, 2),
        "total_amount": round(total_amount, 2),
        "total_interest": round(total_amount - principal, 2),
        "principal": round(principal, 2),
        "principal_pct": round(principal / total_amount * 100, 1),
        "interest_pct": round((total_amount - principal) / total_amount * 100, 1),
    }


def calc_bmi(weight: float, height: float, unit: str = "metric") -> dict:
    """Calculate BMI. Metric: kg/cm, Imperial: lb/in."""
    if weight <= 0 or height <= 0:
        raise ValueError("Weight and height must be positive.")
    if unit == "metric":
        bmi = weight / ((height / 100) ** 2)
    else:
        bmi = (703 * weight) / (height ** 2)
    if bmi < 18.5:
        category, color = "Underweight", "#378add"
    elif bmi < 25:
        category, color = "Normal Weight", "#3b6d11"
    elif bmi < 30:
        category, color = "Overweight", "#ba7517"
    else:
        category, color = "Obese", "#e24b4a"
    ideal_min = round(18.5 * ((height / 100) ** 2) if unit == "metric" else 18.5 * height ** 2 / 703, 1)
    ideal_max = round(24.9 * ((height / 100) ** 2) if unit == "metric" else 24.9 * height ** 2 / 703, 1)
    return {
        "bmi": round(bmi, 1),
        "category": category,
        "color": color,
        "ideal_min": ideal_min,
        "ideal_max": ideal_max,
    }


def calc_percentage(mode: str, a: float, b: float) -> dict:
    """Calculate various percentage operations."""
    if mode == "of_num":
        result = (a / 100) * b
        label = f"{a}% of {b}"
    elif mode == "what_pct":
        if b == 0:
            raise ValueError("Denominator cannot be zero.")
        result = (a / b) * 100
        label = f"{a} is ?% of {b}"
    elif mode == "increase":
        if a == 0:
            raise ValueError("Original value cannot be zero.")
        result = ((b - a) / a) * 100
        label = f"% increase from {a} to {b}"
    elif mode == "decrease":
        if a == 0:
            raise ValueError("Original value cannot be zero.")
        result = ((a - b) / a) * 100
        label = f"% decrease from {a} to {b}"
    else:
        raise ValueError("Invalid mode.")
    suffix = "%" if mode in ("what_pct", "increase", "decrease") else ""
    return {"result": round(result, 6), "label": label, "suffix": suffix}


def calc_compound_interest(principal: float, rate: float, time: float, n: int) -> dict:
    """Calculate compound interest."""
    if principal <= 0 or rate < 0 or time <= 0 or n <= 0:
        raise ValueError("All values must be positive.")
    amount = principal * math.pow(1 + rate / 100 / n, n * time)
    return {
        "amount": round(amount, 2),
        "interest": round(amount - principal, 2),
        "principal": round(principal, 2),
    }


def calc_age(dob_str: str) -> dict:
    """Calculate age from date of birth string (YYYY-MM-DD)."""
    birth = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = date.today()
    if birth > today:
        raise ValueError("Date of birth cannot be in the future.")
    years = today.year - birth.year
    months = today.month - birth.month
    days = today.day - birth.day
    if days < 0:
        months -= 1
        prev_month_last = (today.replace(day=1) - __import__("datetime").timedelta(days=1)).day
        days += prev_month_last
    if months < 0:
        years -= 1
        months += 12
    total_days = (today - birth).days
    next_bday = birth.replace(year=today.year)
    if next_bday < today:
        next_bday = next_bday.replace(year=today.year + 1)
    days_to_bday = (next_bday - today).days
    return {
        "years": years, "months": months, "days": days,
        "total_days": total_days,
        "days_to_birthday": days_to_bday,
        "is_birthday": days_to_bday == 0,
    }


UNIT_CONVERSIONS = {
    "length": {
        "units": ["Meter", "Kilometer", "Mile", "Foot", "Inch", "Centimeter", "Millimeter", "Yard"],
        "to_base": {"Meter": 1, "Kilometer": 1000, "Mile": 1609.344, "Foot": 0.3048,
                    "Inch": 0.0254, "Centimeter": 0.01, "Millimeter": 0.001, "Yard": 0.9144},
    },
    "weight": {
        "units": ["Kilogram", "Gram", "Pound", "Ounce", "Ton"],
        "to_base": {"Kilogram": 1, "Gram": 0.001, "Pound": 0.453592, "Ounce": 0.0283495, "Ton": 1000},
    },
    "area": {
        "units": ["sq meter", "sq kilometer", "sq foot", "sq mile", "acre", "hectare"],
        "to_base": {"sq meter": 1, "sq kilometer": 1e6, "sq foot": 0.092903,
                    "sq mile": 2589988.1, "acre": 4046.856, "hectare": 10000},
    },
    "speed": {
        "units": ["m/s", "km/h", "mph", "knot"],
        "to_base": {"m/s": 1, "km/h": 1/3.6, "mph": 0.44704, "knot": 0.514444},
    },
    "volume": {
        "units": ["Liter", "Milliliter", "Gallon", "Quart", "Cup", "Fluid Oz"],
        "to_base": {"Liter": 1, "Milliliter": 0.001, "Gallon": 3.78541,
                    "Quart": 0.946353, "Cup": 0.236588, "Fluid Oz": 0.0295735},
    },
}


def calc_unit(category: str, from_unit: str, to_unit: str, value: float) -> dict:
    """Convert between units."""
    if category == "temperature":
        if from_unit == to_unit:
            result = value
        elif from_unit == "Celsius":
            result = value * 9/5 + 32 if to_unit == "Fahrenheit" else value + 273.15
        elif from_unit == "Fahrenheit":
            c = (value - 32) * 5/9
            result = c if to_unit == "Celsius" else c + 273.15
        else:  # Kelvin
            c = value - 273.15
            result = c if to_unit == "Celsius" else c * 9/5 + 32
    else:
        cat = UNIT_CONVERSIONS.get(category)
        if not cat:
            raise ValueError(f"Unknown category: {category}")
        in_base = value * cat["to_base"][from_unit]
        result = in_base / cat["to_base"][to_unit]
    return {"result": round(float(result), 8), "from_unit": from_unit, "to_unit": to_unit, "value": value}


def calc_tip(bill: float, tip_pct: float, people: int) -> dict:
    """Calculate tip split."""
    if bill <= 0:
        raise ValueError("Bill must be positive.")
    if tip_pct < 0:
        raise ValueError("Tip cannot be negative.")
    people = max(1, people)
    tip_amount = bill * tip_pct / 100
    total = bill + tip_amount
    return {
        "tip_amount": round(tip_amount, 2),
        "total": round(total, 2),
        "per_person": round(total / people, 2),
        "tip_per_person": round(tip_amount / people, 2),
        "people": people,
    }


def safe_eval(expression: str) -> float:
    """Safely evaluate a basic math expression."""
    allowed = set("0123456789.+-*/() ")
    if not all(c in allowed for c in expression):
        raise ValueError("Invalid characters in expression.")
    if len(expression) > 200:
        raise ValueError("Expression too long.")
    try:
        result = eval(expression, {"__builtins__": {}}, {})  # noqa: S307
        if not isinstance(result, (int, float)):
            raise ValueError("Invalid result type.")
        if math.isinf(result) or math.isnan(result):
            raise ValueError("Result is undefined (division by zero or overflow).")
        return float(result)
    except ZeroDivisionError:
        raise ValueError("Division by zero.")
    except Exception:
        raise ValueError("Invalid expression.")


# ─── ROUTES ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/basic", methods=["POST"])
def api_basic():
    try:
        data = request.get_json(force=True)
        expr = str(data.get("expression", "")).strip()
        if not expr:
            return jsonify({"error": "Empty expression."}), 400
        result = safe_eval(expr)
        formatted = f"{result:.10g}"
        return jsonify({"result": formatted})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Calculation failed."}), 500


@app.route("/api/emi", methods=["POST"])
def api_emi():
    try:
        data = request.get_json(force=True)
        result = calc_emi(float(data["principal"]), float(data["rate"]), int(data["months"]))
        return jsonify(result)
    except (KeyError, TypeError):
        return jsonify({"error": "Missing or invalid fields."}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/bmi", methods=["POST"])
def api_bmi():
    try:
        data = request.get_json(force=True)
        result = calc_bmi(float(data["weight"]), float(data["height"]), data.get("unit", "metric"))
        return jsonify(result)
    except (KeyError, TypeError):
        return jsonify({"error": "Missing or invalid fields."}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/percentage", methods=["POST"])
def api_percentage():
    try:
        data = request.get_json(force=True)
        result = calc_percentage(data["mode"], float(data["a"]), float(data["b"]))
        return jsonify(result)
    except (KeyError, TypeError):
        return jsonify({"error": "Missing or invalid fields."}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/compound", methods=["POST"])
def api_compound():
    try:
        data = request.get_json(force=True)
        result = calc_compound_interest(
            float(data["principal"]), float(data["rate"]),
            float(data["time"]), int(data["n"])
        )
        return jsonify(result)
    except (KeyError, TypeError):
        return jsonify({"error": "Missing or invalid fields."}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/age", methods=["POST"])
def api_age():
    try:
        data = request.get_json(force=True)
        result = calc_age(data["dob"])
        return jsonify(result)
    except (KeyError, TypeError):
        return jsonify({"error": "Missing or invalid fields."}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/unit", methods=["POST"])
def api_unit():
    try:
        data = request.get_json(force=True)
        result = calc_unit(data["category"], data["from_unit"], data["to_unit"], float(data["value"]))
        return jsonify(result)
    except (KeyError, TypeError):
        return jsonify({"error": "Missing or invalid fields."}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/tip", methods=["POST"])
def api_tip():
    try:
        data = request.get_json(force=True)
        result = calc_tip(float(data["bill"]), float(data["tip_pct"]), int(data.get("people", 1)))
        return jsonify(result)
    except (KeyError, TypeError):
        return jsonify({"error": "Missing or invalid fields."}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/unit_meta")
def api_unit_meta():
    meta = {cat: data["units"] for cat, data in UNIT_CONVERSIONS.items()}
    meta["temperature"] = ["Celsius", "Fahrenheit", "Kelvin"]
    return jsonify(meta)


# ─── ENTRY POINT ────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
