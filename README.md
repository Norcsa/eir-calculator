# Effective Interest Rate Calculation App

This web application performs **Effective Interest Rate (EIR)** calculations for fixed-rate and floating-rate financial instruments. It supports initial recognition and subsequent measurement under IFRS and US GAAP and is designed to mirror audit-compliant methodologies, including recalculation upon interest rate resets.

---

## Features

- **Cash Flow Schedule Generation**: Automatically creates payment dates with support for stub periods.
- **Interest Cash Flow Calculation**: Supports various day count conventions (`30/360`, `ACT/360`, `ACT/365`, and leap-year-aware `actual/actual`).
- **Fixed & Floating Rate Instruments**: Accurately models both types using appropriate logic.
- **Amortized Cost and EIR Calculation**: Uses `scipy.optimize` for least-squares minimization to accurately solve for the effective interest rate.
- **Comparative Analysis**: Provides side-by-side comparison of "simple" and "complex" methods for effective interest.
- **Efficiency Metrics**: Measures and compares performance time between calculation methods.
- **Yearly Summaries and Periodic Comparisons**: Summarizes interest costs and rate differences by period and year-end.

---

## How It Works

There are two core approaches:

### Simple EIR Calculation
- Calculates a full amortization schedule once using the first user-provided interest rate.
- Best for **perfomance improvementn** for **floating-rate instruments**.

### Complex EIR Calculation
- Recalculates the schedule on every new interest reset date.
- Fixes past periods and updates only future periods.
- This is the method usually tought in accounting schools.

Both methods generate schedules containing:
- Nominal and effective interest
- Principal balances
- Amortization schedules
- Total cash flows and capitalized costs

A comparison module aggregates these results by year and by period to identify differences.

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Norcsa/eir-calculator.git
cd eircalculator
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

You can run the app locally (assuming Flask-based UI):

```bash
python app.py
```

Or you can import the calculation functions directly in another Python script:

```python
from eir_calculator import simple_eir_calculation, complex_eir_calculation, comparision
```

Prepare your deal dictionary (`d`) and interest dictionary (`interest_dict`), then call:

```python
report = complex_eir_calculation(d, interest_dict)
```

---

## Requirements

- Python 3.9+
- `Flask`
- `Flask-Session`
- `forex-python`
- `pandas`
- `pytest`
- `python-dateutil`
- `scipy`

---

## Example Input

```python
d = {
    "functional_ccy": "USD",
    "deal_id": "ABC123",
    "principal_amount": 400_000_000,
    "deal_ccy": "USD",
    "deal_fx_rate": "",
    "discount": "",
    "premium": "",
    "setup_costs": 10_000_000,
    "start_date": date(2021, 4, 7),
    "end_date": date(2025, 4, 7),
    "first_interest_date": date(2021, 10, 7),
    "interest_rate": 5.46,
    "structure": "amortizing",
    "interest_freq": "semi_annual,
    "daycount": "actual_actual",
    "interest_type": "floating",
}

interest_dict = [
    {"date": date(2021, 10, 7), "rate": 5.46},
    {"date": date(2022, 4, 7), "rate": 5.129},
    {"date": date(2022, 10, 7), "rate": 5.92},
    {"date": date(2023, 4, 7), "rate": 5.239},
    {"date": date(2023, 10, 7), "rate": 5.676},
    {"date": date(2024, 4, 7), "rate": 5.469},
    {"date": date(2024, 10, 7), "rate": 5.726},
    {"date": date(2025, 4, 7), "rate": 5.122},
]
```

---

## Output

Returns a list of dictionaries representing the amortization schedule, including fields such as:

- `Dates`
- `Nominal interest rate`
- `Effective interest`
- `Amortized cost`
- `Effective interest rate`
- `Capitalized finance costs`
- And more

Also returns performance metrics (`complex_time`, `simple_time`, `efficiency`).

---

## License

This project is licensed under the MIT License.

You are free to use, modify, and distribute this software in personal and commercial projects.
See the LICENSE file for more details.

---

## Support

For feedback, issues, or contributions, please open an [issue](https://github.com/Norcsa/eir-calculator/issues) or a pull request.