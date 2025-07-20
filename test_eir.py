from datetime import date
from eir import (
    calculate_effective_interest,
    complex_eir_calculation,
    generate_cf_dates,
    generate_principal_balances,
    generate_total_cf,
    interest_cf,
    interest_rates,
    simple_eir_calculation,
)

deal1 = {
    "functional_ccy": "USD",
    "deal_id": "DN0000",
    "principal_amount": 400000000,
    "deal_ccy": "USD",
    "deal_fx_rate": "",
    "discount": "",
    "premium": "",
    "setup_costs": 10000000,
    "start_date": date(2021, 4, 7),
    "end_date": date(2025, 4, 7),
    "first_interest_date": date(2021, 10, 7),
    "interest_rate": 0.0546,
    "structure": "amortizing",
    "interest_freq": 6,
    "daycount": "actual_actual",
    "interest_type": "floating",
    "capitalized_finance_costs": 10000000,
}

interest_dict = [
    {"date": date(2021, 10, 7), "rate": 0.0546},
    {"date": date(2022, 4, 7), "rate": 0.05129},
    {"date": date(2022, 10, 7), "rate": 0.0592},
    {"date": date(2023, 4, 7), "rate": 0.05239},
    {"date": date(2023, 10, 7), "rate": 0.05676},
    {"date": date(2024, 4, 7), "rate": 0.05469},
    {"date": date(2024, 10, 7), "rate": 0.05726},
    {"date": date(2025, 4, 7), "rate": 0.05122},
]


def test_calculate_effective_interest():
    dates, n = generate_cf_dates(
        deal1["start_date"],
        deal1["end_date"],
        deal1["first_interest_date"],
        deal1["interest_freq"],
    )
    principal_balance = generate_principal_balances(
        deal1["structure"], deal1["principal_amount"], n
    )
    interest_rate = interest_rates(interest_dict, n)
    interest_cashflow = interest_cf(
        dates,
        interest_rate,
        deal1["daycount"],
        deal1["interest_freq"],
        principal_balance,
        n,
    )
    total_cash_flow = generate_total_cf(
        deal1["principal_amount"],
        deal1["capitalized_finance_costs"],
        deal1["structure"],
        interest_cashflow,
        n,
    )
    (
        effective_interest,
        amortized_cost,
        amortization_schedule,
        eir,
        capitalized_finance_costs,
    ) = calculate_effective_interest(
        deal1["interest_rate"],
        dates,
        total_cash_flow,
        interest_cashflow,
        deal1["capitalized_finance_costs"],
        n,
    )
    assert len(effective_interest) == 8
    assert -1 < amortized_cost[-1] < 1
    assert len(amortized_cost) == 9
    assert amortized_cost[0] == 390000000
    assert round(amortization_schedule[-1], 1) == round(
        capitalized_finance_costs[-2], 1
    )
    assert len(amortization_schedule) == 8
    assert len(eir) == 8
    assert len(capitalized_finance_costs) == 9
    assert -1 < capitalized_finance_costs[-1] < 1


def test_complex_eir_calculation():
    complex = complex_eir_calculation(deal1, interest_dict)
    assert len(complex) == 9
    assert complex[-1]["Principal balance"] == 0.00
    assert complex[0]["Total cash flow"] == complex[0]["Amortized cost"] * (-1)
    assert -1 < complex[-1]["Amortized cost"] < 1
    assert -1 < complex[-1]["Capitalized finance costs"] < 1
    assert round(complex[-1]["Amortization schedule"], 1) == round(
        complex[-2]["Capitalized finance costs"], 1
    )
    assert complex[0]["Nominal interest rate"] == ""
    assert complex[0]["Nominal interest"] == ""
    assert complex[0]["Effective interest"] == ""
    assert complex[0]["Amortization schedule"] == ""
    assert complex[0]["Effective interest rate"] == ""


def test_generate_cf_dates():
    dates, n = generate_cf_dates(
        deal1["start_date"],
        deal1["end_date"],
        deal1["first_interest_date"],
        deal1["interest_freq"],
    )
    assert len(dates) == 9
    assert n == 8
    assert dates[-1] == deal1["end_date"]


def test_generate_principal_balances():
    n = 8
    principal_balance = generate_principal_balances(
        deal1["structure"], deal1["principal_amount"], n
    )
    assert len(principal_balance) == 9
    assert principal_balance[-1] == 0.00


def test_generate_total_cf():
    dates, n = generate_cf_dates(
        deal1["start_date"],
        deal1["end_date"],
        deal1["first_interest_date"],
        deal1["interest_freq"],
    )
    principal_balance = generate_principal_balances(
        deal1["structure"], deal1["principal_amount"], n
    )
    interest_rate = interest_rates(interest_dict, n)
    interest_cashflow = interest_cf(
        dates,
        interest_rate,
        deal1["daycount"],
        deal1["interest_freq"],
        principal_balance,
        n,
    )
    total_cash_flow = generate_total_cf(
        deal1["principal_amount"],
        deal1["capitalized_finance_costs"],
        deal1["structure"],
        interest_cashflow,
        n,
    )
    assert total_cash_flow[0] < 0
    assert len(total_cash_flow) == 9


def test_interest_cf():
    dates, n = generate_cf_dates(
        deal1["start_date"],
        deal1["end_date"],
        deal1["first_interest_date"],
        deal1["interest_freq"],
    )
    principal_balance = generate_principal_balances(
        deal1["structure"], deal1["principal_amount"], n
    )
    interest_rate = interest_rates(interest_dict, n)
    interest_cashflow = interest_cf(
        dates,
        interest_rate,
        deal1["daycount"],
        deal1["interest_freq"],
        principal_balance,
        n,
    )
    assert len(interest_cashflow) == 8


def test_interest_rates():
    n = 8
    interest_rate = interest_rates(interest_dict, n)
    assert len(interest_rate) == 8
    assert interest_rate[0] == deal1["interest_rate"]


def test_simple_eir_calculation():
    simple, _, _ = simple_eir_calculation(deal1, interest_dict)
    assert len(simple) == 9
    assert simple[-1]["Principal balance"] == 0.00
    assert simple[0]["Total cash flow"] == simple[0]["Amortized cost"] * (-1)
    assert -1 < simple[-1]["Amortized cost"] < 1
    assert -1 < simple[-1]["Capitalized finance costs"] < 1
    assert round(simple[-1]["Amortization schedule"], 1) == round(
        simple[-2]["Capitalized finance costs"], 1
    )
    assert simple[0]["Nominal interest rate"] == ""
    assert simple[0]["Nominal interest"] == ""
    assert simple[0]["Effective interest"] == ""
    assert simple[0]["Amortization schedule"] == ""
    assert simple[0]["Effective interest rate"] == ""
