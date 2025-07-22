from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_session import Session
from flask_talisman import Talisman
import io
import pandas as pd

from eir import (
    comparision,
    complex_eir_calculation,    
    generate_cf_dates,
    simple_eir_calculation,   
)
from get_data import (
    get_currency,
    get_date,
    get_daycount,
    get_discount,
    get_exchange_rate,
    get_interest_freq,
    get_interest_rate,
    get_interest_type,
    get_premium,
    get_principal,
    get_setup_costs,
    get_structure,
    update_deal_data,
)

# Configure application
app = Flask(__name__)
Talisman(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.before_request
def before_request():
    if not request.is_secure and not app.debug:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)
    

@app.after_request
def after_request(response):
    """Ensure responses are not cashed"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


DEAL = {}


@app.route("/calculation", methods=["GET", "POST"])
def calculation():
    if request.method == "GET":
        return render_template("calculation.html")
    elif request.method == "POST":
        try:
            """User input"""  
            DEAL["functional_ccy"] = get_currency(request.form.get("functional_ccy"))
            DEAL["deal_id"] = request.form.get("deal_id")
            DEAL["principal_amount"] = get_principal(
                request.form.get("principal_amount")
            )
            DEAL["deal_ccy"] = get_currency(request.form.get("deal_ccy"))
            DEAL["deal_fx_rate"] = get_exchange_rate(request.form.get("deal_fx_rate"))
            DEAL["discount"] = get_discount(request.form.get("discount"))
            DEAL["premium"] = get_premium(request.form.get("premium"))
            DEAL["setup_costs"] = get_setup_costs(request.form.get("setup_costs_total"))
            DEAL["start_date"] = get_date(request.form.get("start_date"))
            DEAL["end_date"] = get_date(request.form.get("end_date"))
            DEAL["first_interest_date"] = get_date(
                request.form.get("first_interest_date")
            )
            DEAL["interest_rate"] = get_interest_rate(request.form.get("interest_rate"))
            DEAL["structure"] = get_structure(request.form.get("structure"))
            DEAL["interest_freq"] = get_interest_freq(request.form.get("interest_freq"))
            DEAL["daycount"] = get_daycount(request.form.get("daycount"))
            DEAL["interest_type"] = get_interest_type(request.form.get("interest_type"))
            update_deal_data(DEAL)

            """
            These lines are to compile the floating rate inputs into a dictionary adding the first interest as the 0th element, 
            so that the dictionary exists for fixed rate instruments as well in the complex calculation.
            """
            interest_dates = [
                get_date(date)
                for date in request.form.getlist("interest_date[]")
                if date.strip() != ""
            ]
            floating_interest_rates = [
                get_interest_rate(rate)
                for rate in request.form.getlist("interest_rate[]")
                if rate.strip() != ""
            ]
            interest_dict = [
                {
                    "date": DEAL["first_interest_date"],
                    "rate": DEAL["interest_rate"],
                }
            ] + [
                {
                    "date": date,
                    "rate": rate,
                }
                for date, rate in zip(interest_dates, floating_interest_rates)
            ]
            """These lines are for error checking"""
            dates, _ = generate_cf_dates(
                DEAL["start_date"],
                DEAL["end_date"],
                DEAL["first_interest_date"],
                DEAL["interest_freq"],
            )
            for line in interest_dict:
                if line["date"] not in dates:
                    raise ValueError(f"Date is not valid: {line['date']}")


            """These conditions operate the buttons"""
            action = request.form["action"]

            if action == "comparision":
                schedule, summary, complex_time, simple_time, efficiency = comparision(
                    DEAL, interest_dict
                )
                session["schedule"] = schedule
                session["summary"] = summary
                return render_template(
                    "comparision.html",
                    schedule=schedule,
                    summary=summary,
                    complex_time=complex_time,
                    simple_time=simple_time,
                    efficiency=efficiency,
                )
            elif action == "simple_eir_calculation":
                schedule, _, _ = simple_eir_calculation(DEAL, interest_dict)
            elif action == "complex_eir_calculation":
                schedule = complex_eir_calculation(DEAL, interest_dict)
            session["schedule"] = schedule
            return render_template("report.html", schedule=schedule)

        except ValueError as e:
            flash(str(e))
            return render_template("calculation.html", form_data=request.form)
    return render_template("calculation.html")


@app.route("/download/<report_type>")
def download_report(report_type):
    """Download any report (schedule, comparision, summary) as CSV."""
    # Map report_type to session key and default filename
    report_map = {
        "report": ("schedule", "amortization_schedule"),
        "comparision": ("schedule", "comparision_schedule"),
        "summary": ("summary", "summary_schedule"),
    }
    if report_type not in report_map:
        flash("Invalid report type.")
        return redirect(url_for("index"))
    
    session_key, default_filename = report_map[report_type]
    data = session.get(session_key)
    if not data:
        flash("No report available to download.")
        return redirect(url_for("index"))

    deal_id = None
    if len(data) > 0 and "Deal id" in data[0]:
        deal_id = data[0]["Deal id"]
    else:
        deal_id = default_filename

    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    filename = f"{deal_id}_{default_filename}.csv"
    return send_file(
        output, mimetype="text/csv", as_attachment=True, download_name=filename
    )


@app.route("/")
def index():
    """Description of usage of the application"""
    return render_template("index.html")


@app.template_filter("thousands")
def thousands(value):
    """ Format values with thousand separator """
    try:
        return "{:,.2f}".format(value)
    except (ValueError, TypeError):
        return value
