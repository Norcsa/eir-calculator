// Validate Setup Costs
function calculateSetupCostsTotal() {
    let total = 0;
    let validRowFound = false;
    const rows = document.querySelectorAll('.setup-cost-row');
    rows.forEach(function (row) {
        const amountInput = row.querySelector('.setup-cost-amount');
        const fxInput = row.querySelector('.setup-cost-fx');
        let amount = parseFloat(amountInput.value.replace(/,/g, ''));
        let fx = parseFloat(fxInput.value.replace(',', '.'));
        let rowHasError = false;

        if (isNaN(amount) || amount <= 0) {
            rowHasError = true;
            amountInput.classList.add('is-invalid');
        } else {
            amountInput.classList.remove('is-invalid');
        }
        if (isNaN(fx) || fx <= 0) {
            fx = 1; // Default FX to 1 if not provided or invalid
        }
        if (!rowHasError) {
            total += amount / fx;
            validRowFound = true;
        }
    });
    document.getElementById('setup_costs_total').value = validRowFound ? total : '';
}
let errors = [];

window.addEventListener('DOMContentLoaded', function () {

    // On input change
    document.addEventListener('input', function (e) {
        if (e.target.classList.contains('setup-cost-amount') || e.target.classList.contains('setup-cost-fx')) {
            calculateSetupCostsTotal();
        }
    });

    // Setup Costs input
    document.getElementById('add-setup-cost-btn').addEventListener('click', function () {
        const container = document.getElementById('setup-costs-container');
        const row = document.createElement('div');
        row.className = 'row setup-cost-row';
        row.innerHTML = `
                <div class="col-4 col-sm-2">
                    <label for="setup_costs" class="col-form-label">Setup Costs</label>
                </div>
                <div class="col-4 col-sm-2">
                    <input autocomplete="off" type="text" id="setup_costs" name="setup_cost_amount" class="form-control setup-cost-amount" step="any">
                </div>
                <div class="col-4 col-sm-2">
                    <label for="setupcosts_ccy" class="col-form-label">Currency</label>
                </div>
                <div class="col-auto">
                    <input autocomplete="off" type="text" id="setupcosts_ccy" name="setupcosts_ccy" class="form-control" maxlength="3" pattern="[A-Za-z]{3}">
                </div>
                <div class="col-auto">
                    <label for="setupcost_fx_rate" class="col-form-label">Exchange rate</label>
                </div>
                <div class="col-auto">
                    <input autocomplete="off" type="number" id="setupcost_fx_rate" name="setup_cost_fx" class="form-control setup-cost-fx" placeholder="1" step="any">
                </div>
            `;
        container.appendChild(row);
        calculateSetupCostsTotal();
    });

    // Validate Exchange Rate for Setup Costs
    document.querySelectorAll('.setup-cost-row').forEach(function(row) {
        const setupCcyInput = row.querySelector('.setup-cost-amount').closest('.row').querySelector('.setup-cost-row input[name="setupcosts_ccy"]');
        const setupFxInput = row.querySelector('.setup-cost-fx');
        if (setupCcyInput && setupFxInput) {
            const setupCcy = setupCcyInput.value.trim();
            const setupFx = setupFxInput.value.trim();
            if (setupCcy && functionalCcy && setupCcy.toUpperCase() !== functionalCcy.toUpperCase()) {
                if (!setupFx || parseFloat(setupFx) === 1) {
                    errors.push("Exchange rate is required for foreign currency instruments (setup costs).");
                    setupFxInput.classList.add('is-invalid');
                } else {
                    setupFxInput.classList.remove('is-invalid');
                }
            } else {
                setupFxInput.classList.remove('is-invalid');
            }
        }
    });

    // Floating rate section
    document.querySelector('form').addEventListener('submit', function (e) {
        errors = []

        function updateFloatingInterestSection() {
            const floatingRadio = document.getElementById('floating');
            const section = document.getElementById('floating-interest-section');
            if (floatingRadio.checked) {
                section.style.display = '';
            } else {
                section.style.display = 'none';
            }
        }

        // Validate Functional Currency
        const functionalCcy = document.getElementById('functional_ccy').value.trim();
        if (!functionalCcy) {
            errors.push("Functional Currency is required.");
        }

        // Validate Deal ID
        const dealId = document.getElementById('deal_id').value.trim();
        if (!dealId) {
            errors.push("Deal ID is required.");
        }

        // Validate Principal Amount
        const principalAmount = parseFloat(document.getElementById('principal_amount').value.replace(/,/g, ''));
        if (!principalAmount) {
            errors.push("Principal Amount is required.");
        }

        // Validate Principal Currency
        const dealCurrency = document.getElementById('deal_ccy').value.trim();
        if (!dealCurrency) {
            errors.push("Deal currency is required.");
        }

        // Validate Exchange Rate for Deal Currency
        const dealFxRate = document.getElementById('deal_fx_rate').value.trim();
        if (dealCurrency && functionalCcy && dealCurrency.toUpperCase() !== functionalCcy.toUpperCase()) {
            if (!dealFxRate || parseFloat(dealFxRate) === 1) {
                errors.push("Exchange rate is required for foreign currency instruments.");
                document.getElementById('deal_fx_rate').classList.add('is-invalid');
            } else {
                document.getElementById('deal_fx_rate').classList.remove('is-invalid');
            }
        }

        // Validate date inputs
        const dateFields = [
            { input: document.getElementById('start_date'), label: 'Start Date' },
            { input: document.getElementById('end_date'), label: 'End Date' },
            { input: document.getElementById('first_interest_date'), label: 'First Interest Date' },
            { input: document.getElementById('interest_date[]'), label: 'Interest Date' }
        ];
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

        dateFields.forEach(function (field) {
            if (field.input && !dateRegex.test(field.input.value.trim())) {
                errors.push(`Invalid date format for ${field.label}. Please use YYYY-MM-DD.`);
                field.input.classList.add('is-invalid');
            } else if (field.input) {
                field.input.classList.remove('is-invalid');
            }
        });

        // Validate all interest rate fields (for floating rates)
        document.querySelectorAll('.interest-rate').forEach(function (input) {
            const value = input.value.replace(',', '.').trim();
            const interestRate = parseFloat(value);
            if (value && isNaN(interestRate)) {
                errors.push("Interest Rate must be a valid number (use dot or comma as decimal separator).");
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });

        // If there are errors, prevent submission and show all messages
        if (errors.length > 0) {
            e.preventDefault();
            alert(errors.join('\n'));
            return false;
        }
    });

    function updateFloatingInterestSection() {
        const floatingRadio = document.getElementById('floating');
        const section = document.getElementById('floating-interest-section');
        if (floatingRadio.checked) {
            section.style.display = '';
        } else {
            section.style.display = 'none';
        }
    }

    // Run on page load
    updateFloatingInterestSection();

    // Add event listeners to interest type radios
    document.querySelectorAll('input[name="interest_type"]').forEach(function (radio) {
        radio.addEventListener('change', updateFloatingInterestSection);
    });
    document.getElementById('add-interest-rate-btn').addEventListener('click', function () {
        const container = document.getElementById('interest-rate-container');
        const row = document.createElement('div');
        row.className = 'row mb-2 interest-rate-row';
        row.innerHTML = `
            <div class="col-4 col-sm-2">
                <label for="date" class="col-form-label">Interest Payment Date</label>
            </div>
            <div class="col-4 col-sm-2">
                <input autocomplete="off" type="text"  name="interest_date[]" class="form-control interest-date">
            </div>
            <div class="col-4 col-sm-2">
                <label for="rate" class="col-form-label">Interest Rate (%)</label>
            </div>
            <div class="col-4 col-sm-2">
                <input autocomplete="off" type="text"  name="interest_rate[]" class="form-control interest-rate">
            </div>
        `;
        container.appendChild(row);
    });
});