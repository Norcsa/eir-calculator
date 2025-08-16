import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
from scipy.optimize import least_squares
import timeit


def complex_eir_calculation(d: dict, interest_dict: list) -> list:
    """
    This function calculates the effective interest in the way recommended by auditors.
    Various lists are generated from the user input, where each list represents a column of the output report.
    For all deals the amortization schedule needs to be calculated at least once, at initial recognition.
    For floating rate deals the schedule needs to be recalculated in each period when a new interest rate is set.
    The recommneded way to do the recalculation is to "fix" the values in the periods that have already passed and
    recalculate the nominal interest and the cash flows based on the new interest rate for future periods.
    Then use these new cash flows to recalculate the effective interest and overwrite the schedule for future periods.

    The first 3 columns are universal in a sense that they only need to be calculated once on each user input.
    """

    dates, number_of_payments = generate_cf_dates(
        d["start_date"], d["end_date"], d["first_interest_date"], d["interest_freq"]
    )
    principal_balance = generate_principal_balances(
        d["structure"], d["principal_amount"], number_of_payments
    )
    final_interest_rates = interest_rates(interest_dict, number_of_payments)

    """
    The following lists need to be recalculated for each period with a new interest rate.
    For fixed rate instruments the lists are only generated once.
    For floating rate instruments the lists are regenerated for each interest rate provided by the user.

    The total cash flow and the capitalized costs start with an initial value from the deal inputs,
    so that the functions updating the lists can reference the 0th element in those lists.
    """
    final_nominal_interest = list()
    final_total_cash_flow = [d["capitalized_finance_costs"] - d["principal_amount"]]
    final_effective_interest = list()
    final_amortized_cost = list()
    final_amortization_schedule = list()
    final_eir = list()
    final_capitalized_costs = [d["capitalized_finance_costs"]]

    """
    The list of interest_dict comes from user input. For fixed rate instruments it contains one item,
    for floating rate instuments it can contain a number of items between one and the number of payments.
    The actual length depends on how many rates the user input.
    """
    for i in range(len(interest_dict)):
        floating_interest_rate = [
            interest_dict[i]["rate"] for _ in range(number_of_payments - i)
        ]
        floating_coupon = interest_cf(
            dates[i:],
            floating_interest_rate,
            d["daycount"],
            d["interest_freq"],
            principal_balance[i:],
            (number_of_payments - i),
        )
        floating_total_cf = generate_total_cf(
            principal_balance[i],
            final_capitalized_costs[i],
            d["structure"],
            floating_coupon,
            (number_of_payments - i),
        )
        (
            floating_effective_interest,
            floating_amortized_cost,
            floating_amortization_schedule,
            floating_eir,
            floating_capitalized_costs,
        ) = calculate_effective_interest(
            final_interest_rates[i],
            dates[(i):],
            floating_total_cf,
            floating_coupon,
            final_capitalized_costs[i],
            (number_of_payments - i),
        )
        """
        This conditional ensures that the values for the periods that have already passed are fixed and
        only the periods that are affected by the new interest rate are updated.
        The total cash flow and the capitalised costs are updated with index 1 as index 0 was set above.
        """
        if i < (len(interest_dict) - 1):
            final_nominal_interest.append(floating_coupon[0])
            final_total_cash_flow.append(floating_total_cf[1])
            final_effective_interest.append(floating_effective_interest[0])
            final_amortized_cost.append(floating_amortized_cost[0])
            final_amortization_schedule.append(floating_amortization_schedule[0])
            final_eir.append(floating_eir[0])
            final_capitalized_costs.append(floating_capitalized_costs[1])
        else:
            final_nominal_interest.extend(floating_coupon)
            final_total_cash_flow.extend(floating_total_cf[1:])
            final_effective_interest.extend(floating_effective_interest)
            final_amortized_cost.extend(floating_amortized_cost)
            final_amortization_schedule.extend(floating_amortization_schedule)
            final_eir.extend(floating_eir)
            final_capitalized_costs.extend(floating_capitalized_costs[1:])

    """
    These empty items at the start of these lists are purley for presentation purposes, 
    to make the lists equal in length and aligned to the correct dates.
    """
    final_interest_rates = [""] + [
        round(float(rate * 100), 2) for rate in final_interest_rates
    ]
    final_nominal_interest.insert(0, "")
    final_effective_interest.insert(0, "")
    final_amortization_schedule.insert(0, "")
    final_eir.insert(0, "")

    """
    The output report is a list of dictionaries, where each dictionary is a row in the output report.
    The +1 in the range represents the 0th row, which is not included in the number of payments.
    """
    complex_report = list()
    for i in range(number_of_payments + 1):
        complex_report.append(
            {
                "Deal id": d["deal_id"],
                "Dates": dates[i],
                "Currency": d["functional_ccy"],
                "Principal balance": principal_balance[i],
                "Nominal interest rate": final_interest_rates[i],
                "Nominal interest": final_nominal_interest[i],
                "Total cash flow": final_total_cash_flow[i],
                "Capitalized finance costs": final_capitalized_costs[i],
                "Amortized cost": final_amortized_cost[i],
                "Effective interest": final_effective_interest[i],
                "Amortization schedule": final_amortization_schedule[i],
                "Effective interest rate": final_eir[i],
            }
        )
    return complex_report


def simple_eir_calculation(
    d: dict, interest_dict: list
) -> tuple[list, float, float]:
    """
    The simple calculation uses as a different approach to calculate the same schedule as above.
    First an initial schedule is calculated, which is necessary for each instrument at initial recognition.

    This funciton only calcultes a full schedule once, using the first interest rate provided by the user.
    Initally all columns are updated directly from the deal details without iteration.
    """

    dates, number_of_payments = generate_cf_dates(
        d["start_date"], d["end_date"], d["first_interest_date"], d["interest_freq"]
    )
    principal_balance = generate_principal_balances(
        d["structure"], d["principal_amount"], number_of_payments
    )
    interest_rate = [interest_dict[0]["rate"] for _ in range(number_of_payments)]

    nominal_interest = interest_cf(
        dates,
        interest_rate,
        d["daycount"],
        d["interest_freq"],
        principal_balance,
        number_of_payments,
    )
    total_cash_flow = generate_total_cf(
        d["principal_amount"],
        d["capitalized_finance_costs"],
        d["structure"],
        nominal_interest,
        number_of_payments,
    )
    """
    The timeit function is used to measure the efficiency of the actual effective interest calculation.
    It is measured here, as within the simple calcualtion this funciton is only called once, 
    whereas within the complex calcualtion it is called as many times as many interest rates are provided by the user.
    """
    complex_time = timeit.timeit(
        lambda: calculate_effective_interest(
            d["interest_rate"],
            dates,
            total_cash_flow,
            nominal_interest,
            d["capitalized_finance_costs"],
            number_of_payments,
        ),
        number=1,
    )
    (
        effective_interest,
        amortized_cost,
        amortization_schedule,
        eir,
        capitalized_finance_costs,
    ) = calculate_effective_interest(
        d["interest_rate"],
        dates,
        total_cash_flow,
        nominal_interest,
        d["capitalized_finance_costs"],
        number_of_payments,
    )

    """
    In case the interest type is floating, the columns calculated above are reset by using the floating rates and
    the floating effective interest function, which is the essence of the simple calculation.
    In case of a fixed rate instrument the complex and the simple calcualtion yield the same result.
    """
    if d["interest_type"] == "floating":
        interest_rate = interest_rates(
            interest_dict,
            number_of_payments,
        )
        nominal_interest = interest_cf(
            dates,
            interest_rate,
            d["daycount"],
            d["interest_freq"],
            principal_balance,
            number_of_payments,
        )
        total_cash_flow = generate_total_cf(
            d["principal_amount"],
            d["capitalized_finance_costs"],
            d["structure"],
            nominal_interest,
            number_of_payments,
        )
        simple_time = timeit.timeit(
            lambda: calculate_floating_effective_interest(
                dates,
                d["interest_type"],
                nominal_interest,
                amortization_schedule,
                amortized_cost,
                number_of_payments,
            ),
            number=1,
        )
        effective_interest, eir = calculate_floating_effective_interest(
            dates,
            d["interest_type"],
            nominal_interest,
            amortization_schedule,
            amortized_cost,
            number_of_payments,
        )
    else:
        """In case of a fixed rate instrument the complex and the simple calcualtion yield the same result."""
        simple_time = complex_time

    """
    As above, these empty items at the start of these lists are purley for presentation purposes, 
    to make the lists equal in length and aligned to the correct dates.
    """
    interest_rate = [""] + [round(float((rate * 100)), 2) for rate in interest_rate]
    nominal_interest.insert(0, "")
    effective_interest.insert(0, "")
    amortization_schedule.insert(0, "")
    eir.insert(0, "")

    """The final output is compiled using list comprehension into a list of dictionaries."""
    report = list()
    for i in range(number_of_payments + 1):
        report.append(
            {
                "Deal id": d["deal_id"],
                "Dates": dates[i],
                "Currency": d["functional_ccy"],
                "Principal balance": principal_balance[i],
                "Nominal interest rate": interest_rate[i],
                "Nominal interest": nominal_interest[i],
                "Total cash flow": total_cash_flow[i],
                "Capitalized finance costs": capitalized_finance_costs[i],
                "Amortized cost": amortized_cost[i],
                "Effective interest": effective_interest[i],
                "Amortization schedule": amortization_schedule[i],
                "Effective interest rate": eir[i],
            }
        )
    """Apart from the actual report the function also returns the timings of the complex and 
    simple effective interest calculations to be able to display them on the webpage."""
    return report, complex_time, simple_time


def comparision(d: dict, interest_dict: list) -> tuple[list, float, float, float]:
    """
    The purpose of this function is to be able to display the difference between the two versions of effective interest.
    There are 2 reports, one is a summary by year and the other is for the comparision by period.
    """
    simple, complex_time, simple_time = simple_eir_calculation(d, interest_dict)
    complex = complex_eir_calculation(d, interest_dict)

    """
    These two lines convert the empty elements at 0th index into a float to be able to calculate with it without having to change the length.
    """
    simple[0]["Effective interest"] = float(0.00)
    complex[0]["Effective interest"] = float(0.00)

    """This list finds the years apparent in the list of dates relevant to the deal"""
    years = list(dict.fromkeys(date["Dates"].year for date in simple))

    """
    Here I am creating two lists to be able to add up the effecitve interests within the years in both reports.
    I initialized the lists to the lenght of the years list with all elements as a float 0.00.
    Then I add the items from the reports where the year of the dates match the year in the years list.
    """
    complex_effective_interest = [float(0.00)] * len(years)
    simple_effective_interest = [float(0.00)] * len(years)

    for i in range(len(years)):
        for j in range(len(simple)):
            if simple[j]["Dates"].year == years[i]:
                simple_effective_interest[i] += simple[j]["Effective interest"]
                complex_effective_interest[i] += complex[j]["Effective interest"]

    """
    The following loops are used to take the items for the relevant columns from the reports 
    that correspond to the last date of the given year (ie. year end balance)
    """
    last_date_in_year = {}
    for row in simple:
        year = row["Dates"].year
        if year not in last_date_in_year or row["Dates"] > last_date_in_year[year]:
            last_date_in_year[year] = row["Dates"]

    last_dates = [
        {"Year": year, "Last date": last_date_in_year[year]} for year in last_date_in_year
    ]

    """
    As the report shows figures on a cash flow basis, if there is no interest cash flow in the first year
    the zero interests and the first year is being removed. It also avoids the zero division error.
    """
    if simple_effective_interest[0] == 0:
        simple_effective_interest.pop(0)
        complex_effective_interest.pop(0)
        last_dates.pop(0)
        years.pop(0)


    last_simple_eir = list()
    last_complex_eir = list()
    last_principal = list()
    last_nominal_interest_rate = list()


    for year in last_dates:
        for i in range(len(simple)):
            if simple[i]["Dates"] == year["Last date"]:
                last_principal.append(simple[i]["Principal balance"])
                last_nominal_interest_rate.append(simple[i]["Nominal interest rate"])
                last_simple_eir.append(simple[i]["Effective interest rate"])
                last_complex_eir.append(complex[i]["Effective interest rate"])


    """
    The length of this report is basically the number of payments as most of the lists used in this report has an empty item at 0th index, 
    however as the cf_dates functions is not called here, the same value is calculated by deducting 1 from the length of the complex report.
    """
    comparision_report = list()
    for i in range(len(complex)-1):
        comparision_report.append(
            {
                "Deal id": d["deal_id"],
                "Dates": complex[i + 1]["Dates"],
                "Principal balance": complex[i]["Principal balance"],
                "Nominal interest rate": complex[i + 1]["Nominal interest rate"],
                "Complex effective interest": complex[i + 1]["Effective interest"],
                "Simple effective interest": simple[i + 1]["Effective interest"],
                "Complex EIR": complex[i + 1]["Effective interest rate"],
                "Simple EIR": simple[i + 1]["Effective interest rate"],
                "Absolute int. diff": (
                    complex[i + 1]["Effective interest"]
                    - simple[i + 1]["Effective interest"]
                ),
                "Relative int. diff": (
                    (
                        (
                            complex[i + 1]["Effective interest"]
                            - simple[i + 1]["Effective interest"]
                        )
                        / complex[i + 1]["Effective interest"]
                    )
                    * 100
                ),
                "EIR difference": (
                    complex[i + 1]["Effective interest rate"]
                    - simple[i + 1]["Effective interest rate"]
                ),
            }
        )
    
    summary = list()
    for i in range(len(years)):
        summary.append(
            {
                "Deal id": d["deal_id"],
                "Years": years[i],
                "Principal balance": last_principal[i],
                "Nominal interest rate": last_nominal_interest_rate[i],
                "Complex effective interest": complex_effective_interest[i],
                "Simple effective interest": simple_effective_interest[i],
                "Complex EIR": last_complex_eir[i],
                "Simple EIR": last_simple_eir[i],
                "Absolute int. diff": (
                    complex_effective_interest[i]
                    - simple_effective_interest[i]
                ),
                "Relative int. diff": (
                    (
                        (
                            complex_effective_interest[i]
                            - simple_effective_interest[i]
                        )
                        / complex_effective_interest[i]
                    )
                    * 100
                ),
                "EIR difference": (
                    last_complex_eir[i]
                    - last_simple_eir[i]
                ),
            }
        )

    efficiency = (complex_time / simple_time) - 1
    return comparision_report, summary, complex_time, simple_time, efficiency


def generate_cf_dates(
    start_date: date, end_date: date, first_interest_date: date, interest_frequency: int
) -> tuple[list, int]:
    """
    Generates a schedule for the payment dates including period 0 and calculates the number of payments excluding period 0.

    List comprehension to create the date schedule using relativedelta module.
    Based on the interest frequency it adds a certain number of months to the previous date.
    The first interest date is manually inserted to allow for an initial stub period.
    A stub period means that the length of the first period could differ from the general interest frequency of the deal.
    """
    cf_dates = [start_date, first_interest_date]
    i = 1
    while (cf_dates[i] + relativedelta(months=interest_frequency)) <= end_date:
        cf_dates.append((cf_dates[i] + relativedelta(months=interest_frequency)))
        i += 1

    """
    This is the calculation for the number of payments excluding the initial one in period zero.
    """
    number_of_payments = len(cf_dates) - 1
    return cf_dates, number_of_payments


def generate_principal_balances(
    structure: str, principal_amount: float, number_of_payments: int
) -> list:
    """
    Generates the principal balances per period, starting with period 0.
    For instruments with "Bullet" structure the balance stays the same until repayment in the last period.
    For instruments with "Amortizing" structure the balance reduces each period by a partial payment.
    The amount of partial payments are equal at each period and is arrived at by dividing the initial balance by the number of payments.
    The amount 0.00 is added as the last element in both cases to represent the balance after full repayment.
    """

    if structure == "bullet":
        principal_balance = [float(principal_amount)] * number_of_payments + [
            float(0.00)
        ]
    else:
        principal_balance = [
            float(principal_amount) - (i * float(principal_amount) / number_of_payments)
            for i in range(number_of_payments)
        ] + [float(0.00)]

    return principal_balance


def interest_rates(
    rates_dict: list,
    number_of_payments: int,
) -> list:
    """
    The interest rates come from the interest dictionary.
    As the ditionary can be of any length upto the number of payments,
    in case the length of the dictionary is less than the number of payments,
    the list is padded with the last rate to the correct length.
    """
    interest_rate = [date["rate"] for date in rates_dict]
    interest_rate = interest_rate + [interest_rate[-1]] * (
        number_of_payments - len(interest_rate)
    )
    return interest_rate


def interest_cf(
    dates: list,
    rates: list,
    daycount: str,
    interest_frequency: int,
    principal_balance: list,
    number_of_payments: int,
) -> list:
    """
    This function calculates a periodic interest rate based on the day count convention provided and the actual dates.
    This periodic interest rate is then used to calculate the interest cashflows by multiplying it with the periodic principal balance
    """
    interest_cashflow = list()
    for i in range(number_of_payments):
        if daycount == "thirty_360":
            periodic_interest_rate = rates[i] / 12 * interest_frequency
        elif daycount == "actual_360":
            periodic_interest_rate = rates[i] / 360 * (dates[i + 1] - dates[i]).days
        elif daycount == "actual_365":
            periodic_interest_rate = rates[i] / 365 * (dates[i + 1] - dates[i]).days
        else:
            if dates[i].month < 3:
                days_in_year = 366 if calendar.isleap(dates[i].year) else 365
            elif dates[i].month > 2 and calendar.isleap(dates[i + 1].year):
                days_in_year = 366
            else:
                days_in_year = 365
            periodic_interest_rate = (
                rates[i] / days_in_year * (dates[i + 1] - dates[i]).days
            )
        interest_cashflow.append(principal_balance[i] * periodic_interest_rate)
    return interest_cashflow


def generate_total_cf(
    principal_amount: float,
    capitalized_finance_cost: float,
    structure: str,
    interest_cashflow: list,
    number_of_payments: int,
) -> list:
    """
    Generates the total cash flows for the start date and each subsequent payment date.
    The first item in period 0 is negative, representing an outflow, while the rest of the cash flows are inflows as required for net present value calculations.
    For readablity all instruments are represented as if they were assets,
    however the calculation would be the exact same for liabilities as well where all values are of the opposite magnitude.
    The cash flows are the sum of principal movements (adjusted to initial setup costs at start date) and interest payments.
    The premium and discount are usually netted with the setup costs.
    In case of the "Bullet" structure, for the principal there are cash flows only in two periods, at start date and at end date
    """

    total_cash_flow = [(principal_amount * -1) + capitalized_finance_cost]
    if structure == "bullet":
        total_cash_flow = (
            total_cash_flow
            + interest_cashflow[:-1]
            + [interest_cashflow[-1] + principal_amount]
        )
    else:
        total_cash_flow = total_cash_flow + [
            round(((principal_amount / number_of_payments) + interest_cashflow[i]), 2)
            for i in range(number_of_payments)
        ]
    return total_cash_flow


def calculate_effective_interest(
    first_interest: float,
    dates: list,
    total_cash_flow: list,
    interest_cashflow: list,
    capitalized_finance_cost: float,
    number_of_payments: int,
) -> tuple[list, list, list, list, list]:
    """
    Calculates the amortized cost and effective interest.
    At inception amortized cost = original principal amount - setup costs (the same as the 0th item in total cash flows with opposit magnitude).
    In subsequent periods it is calculated as follows:
    amortized cost from previous period - total cash flow for current period + effective interest for current period.

    For this, effective interest also needs to be calculated by the optimize_eir_least_squares:
    amortized cost from previous period multiplied by the periodic effective interest rate.

    The variable guess is set the same as the current nominal interest rate as the effective interest rate should be relatively close to the nominal interest,
    so this should reduce the runing time.
    """
    guess = first_interest
    capitalized_finance_costs = [capitalized_finance_cost]

    """
    This function is required for the optimazition. The goal is to get the last item in the list of amortized cost to zero by updating the effective interest rate.
    Originally I tried numpy-financial's IRR and pyxirr's XIRR funcitons, but they were both inaccurate in this case.
    """

    def final_amortized_cost(
        first_interest: float,
        dates: list,
        total_cash_flow: list,
        number_of_payments: int,
    ) -> float:
        amortized_cost = [float(total_cash_flow[0] * (-1))]

        for i in range(number_of_payments):
            """EIR is always calculated on a 365 day basis regardless of the market or currency of the cash flows.
            ACT - CertRM Study Unit 2 - 2.1.2 Interest rate mathematics"""
            effective_interest = (
                amortized_cost[i]
                * first_interest
                * ((dates[i + 1] - dates[i]).days / 365)
            )
            amortized_cost.append(
                amortized_cost[i] - total_cash_flow[i + 1] + effective_interest
            )
        return amortized_cost[-1]

    def optimize_eir_least_squares(
        dates: list, total_cash_flow: list, number_of_payments: int, guess=0.05
    ) -> float:
        res = least_squares(
            lambda r: final_amortized_cost(
                r[0], dates, total_cash_flow, number_of_payments
            ),
            x0=[guess],
            bounds=(0, 1),
        )
        return res.x[0]

    effective_interest_rate = optimize_eir_least_squares(
        dates, total_cash_flow, number_of_payments, guess=guess
    )

    amortized_cost = [float(total_cash_flow[0] * (-1))]
    effective_interest = list()
    amortization_schedule = list()
    eir = list()

    for i in range(number_of_payments):
        effective_interest.append(
            round(
                (
                    amortized_cost[i]
                    * effective_interest_rate
                    * (dates[i + 1] - dates[i]).days
                    / 365
                ),
                2,
            )
        )
        amortized_cost.append(
            round(
                (amortized_cost[i] - total_cash_flow[i + 1] + effective_interest[i]), 2
            )
        )
        amortization_schedule.append(
            round((effective_interest[i] - interest_cashflow[i]), 2)
        )
        eir.append(
            round(
                float(
                    (
                        (interest_cashflow[i] + amortization_schedule[i])
                        / amortized_cost[i]
                        / ((dates[i + 1] - dates[i]).days)
                        * 365
                    )
                    * 100
                ),
                2,
            )
        )
        capitalized_finance_costs.append(
            (float(capitalized_finance_costs[i]) - amortization_schedule[i])
        )
    return (
        effective_interest,
        amortized_cost,
        amortization_schedule,
        eir,
        capitalized_finance_costs,
    )


def calculate_floating_effective_interest(
    dates: list,
    interest_type: str,
    floating_nominal_interest: list,
    amortization_schedule: list,
    amortized_cost: list,
    number_of_payments: int,
) -> tuple[list, list]:
    """
    This function basically does the same as the calculate_effective_interest, except it does not change the amortized cost,
    the amortization schedule and the capitalized finance costs.
    It does create new floating lists for the effective interest, and the eir.
    The effective interest is simply calculated by rearranging the formula for the amortization_schedule as follows:
    effective interest = nominal interest + amortization schedule
    """
    if interest_type == "floating":
        floating_effective_interest = [
            float(floating_nominal_interest[i] + amortization_schedule[i])
            for i in range(number_of_payments)
        ]
        floating_eir = [
            round(
                float(
                    (
                        (floating_effective_interest[i] / amortized_cost[i])
                        / ((dates[i + 1] - dates[i]).days)
                        * 365
                    )
                    * 100
                ),
                2,
            )
            for i in range(number_of_payments)
        ]

        return floating_effective_interest, floating_eir
