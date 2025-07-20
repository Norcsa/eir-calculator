from datetime import datetime
from forex_python.converter import CurrencyCodes

c = CurrencyCodes()

"""These functions are for user input validation and formatting the input when necessary."""


def get_currency(s: str) -> str:
    code = s.strip().upper()
    if c.get_currency_name(code):
        return code
    else:
        raise ValueError("Invalid currency code")


def get_date(d: str) -> datetime:
    try:
        date = datetime.strptime(d.strip(), "%Y-%m-%d")
        return date.date()
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
    

def get_daycount(s: str) -> str:
    if s not in ["actual_actual", "actual_365", "actual_360", "thirty_360"]:
        raise ValueError("Invalid daycount")
    else:
        return s
    

def get_discount(s: str) -> float:
    if not s:
        return 0.0
    else:
        try:
            s = round(float(s.strip()), 2)
        except ValueError:
            return f"Invalid input for discount"
        if s >= 100:
            raise ValueError("Discount must be provided in %")
        else:
            return s
        

def get_exchange_rate(s: str) -> float:
    if s is None or s.strip() == "":
        return 1.0
    try:
        rate = float(s.strip())
        if rate <= 0:
            raise ValueError("Exchange rate must be positive")
        return rate
    except (ValueError, TypeError):
        raise ValueError("Invalid exchange rate")


def get_interest_freq(s: str) -> int:
    interest_frequency = {
        "monthly": 1,
        "quarterly": 3,
        "semi_annual": 6,
        "annual": 12,
    }
    try:
        return int(interest_frequency[s])
    except KeyError:
        raise ValueError("Invalid interest frequency")


def get_interest_rate(s: str) -> float:
    interest_rate = round(float(s)/100, 6)
    if not interest_rate:
        raise ValueError("Invalid interest rate")
    else:
        return interest_rate


def get_interest_type(s: str) -> str:
    if s not in ["fixed", "floating"]:
        raise ValueError("Invalid interest type")
    else:
        return s
    

def get_premium(s: str) -> float:
    if not s:
        return 0.0
    else:
        try:
            s = round(float(s.strip()), 2)
        except ValueError:
            return f"Invalid input for premium"
        if s >= 100:
            raise ValueError("Premium must be provided in %")
        else:
            return s
        

def get_principal(s: str) -> float:
    try:
        return round(float(s.strip().replace(",", "")), 2)
    except ValueError:
        return f"Invalid principal amount"


def get_setup_costs(s: str) -> float:
    if not s:
        return 0.0
    else:
        try:
            return round(float(s.strip().replace(",", "")), 2)
        except ValueError:
            return f"Invalid input for setup costs"

        
        
def get_structure(s: str) -> str:
    if s not in ["bullet", "amortizing"]:
        raise ValueError("Invalid structure")
    else:
        return s


def update_deal_data(d: dict) -> None:
    """
    This function updates some of the user input to be readily used in the various calculations and
    called right after the inputs are submitted.
    """
    if d["functional_ccy"] != d["deal_ccy"]:
        d["principal_amount"] = d["principal_amount"] / d["deal_fx_rate"]

    d["discount"] = (d["discount"] * d["principal_amount"]) / 100
    d["premium"] = (d["premium"] * d["principal_amount"]) / 100
    d["capitalized_finance_costs"] = d["setup_costs"] + d["discount"] - d["premium"]

    if d["discount"] and d["premium"]:
        raise ValueError(
            "Instrument cannot have discount and premium at the same time"
                    )