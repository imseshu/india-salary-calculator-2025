from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)


# ─── Indian Tax Slabs FY 2025-26 ─────────────────────────────────────────────

OLD_REGIME_SLABS = [
    (250000, 0.00),
    (500000, 0.05),
    (1000000, 0.20),
    (float("inf"), 0.30),
]

NEW_REGIME_SLABS = [  # Budget 2024 – applicable FY 2025-26
    (400000, 0.00),
    (800000, 0.05),
    (1200000, 0.10),
    (1600000, 0.15),
    (2000000, 0.20),
    (2400000, 0.25),
    (float("inf"), 0.30),
]

SURCHARGE_RATES = [
    (5000000, 0.00),
    (10000000, 0.10),
    (20000000, 0.15),
    (50000000, 0.25),
    (float("inf"), 0.37),
]

HEALTH_EDUCATION_CESS = 0.04


def compute_tax_on_slabs(income, slabs):
    tax = 0.0
    prev = 0
    for limit, rate in slabs:
        if income <= prev:
            break
        taxable = min(income, limit) - prev
        tax += taxable * rate
        prev = limit
    return tax


def get_surcharge(income, tax):
    surcharge_rate = 0.0
    for limit, rate in SURCHARGE_RATES:
        if income <= limit:
            surcharge_rate = rate
            break
    # Marginal relief simplified
    return tax * surcharge_rate


def compute_income_tax(taxable_income, regime):
    slabs = NEW_REGIME_SLABS if regime == "new" else OLD_REGIME_SLABS

    # Rebate u/s 87A
    if regime == "new" and taxable_income <= 1200000:
        tax = 0.0
        cess = 0.0
        return {"tax": 0, "surcharge": 0, "cess": 0, "total": 0}
    if regime == "old" and taxable_income <= 500000:
        return {"tax": 0, "surcharge": 0, "cess": 0, "total": 0}

    tax = compute_tax_on_slabs(taxable_income, slabs)
    surcharge = get_surcharge(taxable_income, tax)
    total_before_cess = tax + surcharge
    cess = total_before_cess * HEALTH_EDUCATION_CESS
    total = total_before_cess + cess

    return {
        "tax": round(tax, 2),
        "surcharge": round(surcharge, 2),
        "cess": round(cess, 2),
        "total": round(total, 2),
    }


# ─── Deduction Helpers ────────────────────────────────────────────────────────

def hra_exemption(basic_annual, hra_annual, rent_annual, is_metro):
    """Least of three conditions – Section 10(13A)"""
    actual_hra = hra_annual
    forty_fifty = basic_annual * (0.50 if is_metro else 0.40)
    rent_minus_10 = max(0, rent_annual - 0.10 * basic_annual)
    return min(actual_hra, forty_fifty, rent_minus_10)


def std_deduction_old():
    return 50000  # Standard deduction old regime

def std_deduction_new():
    return 75000  # Budget 2024 – new regime standard deduction


# ─── Main Calculator ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        d = request.json

        # ── Salary Components (monthly inputs) ──────────────────────────────
        basic_m = float(d.get("basic", 0))
        hra_m = float(d.get("hra", 0))
        special_allowance_m = float(d.get("special_allowance", 0))
        lta_m = float(d.get("lta", 0))
        medical_m = float(d.get("medical_allowance", 0))
        food_allowance_m = float(d.get("food_allowance", 0))
        transport_m = float(d.get("transport_allowance", 0))
        other_allowances_m = float(d.get("other_allowances", 0))

        # Variable
        variable_pay_annual = float(d.get("variable_pay_annual", 0))
        bonus_annual = float(d.get("bonus_annual", 0))

        # Deductions
        employee_pf_m = float(d.get("employee_pf", 0))
        employer_pf_m = float(d.get("employer_pf", 0))
        employee_esi_m = float(d.get("employee_esi", 0))
        employer_esi_m = float(d.get("employer_esi", 0))
        professional_tax_m = float(d.get("professional_tax", 0))
        gratuity_m = float(d.get("gratuity", 0))
        nps_employee_m = float(d.get("nps_employee", 0))
        other_deductions_m = float(d.get("other_deductions", 0))

        # Tax inputs
        regime = d.get("regime", "new")
        rent_paid_annual = float(d.get("rent_paid_annual", 0))
        is_metro = d.get("is_metro", False)

        # Old regime deductions
        sec80c = min(float(d.get("sec80c", 0)), 150000)
        sec80d = float(d.get("sec80d", 0))
        home_loan_interest = float(d.get("home_loan_interest", 0))
        nps_80ccd = min(float(d.get("nps_80ccd", 0)), 50000)
        other_80_deductions = float(d.get("other_80_deductions", 0))

        # ── Annual Gross ─────────────────────────────────────────────────────
        fixed_gross_m = (basic_m + hra_m + special_allowance_m + lta_m +
                         medical_m + food_allowance_m + transport_m + other_allowances_m)
        fixed_gross_annual = fixed_gross_m * 12
        variable_total_annual = variable_pay_annual + bonus_annual
        gross_annual = fixed_gross_annual + variable_total_annual

        # ── CTC ─────────────────────────────────────────────────────────────
        employer_pf_annual = employer_pf_m * 12
        employer_esi_annual = employer_esi_m * 12
        gratuity_annual = gratuity_m * 12
        ctc_annual = gross_annual + employer_pf_annual + employer_esi_annual + gratuity_annual

        # ── Employee Deductions from salary ─────────────────────────────────
        employee_pf_annual = employee_pf_m * 12
        employee_esi_annual = employee_esi_m * 12
        professional_tax_annual = professional_tax_m * 12
        nps_employee_annual = nps_employee_m * 12
        other_deductions_annual = other_deductions_m * 12

        total_employee_deductions_annual = (
            employee_pf_annual + employee_esi_annual + professional_tax_annual +
            nps_employee_annual + other_deductions_annual
        )

        # ── Taxable Income calculation ───────────────────────────────────────
        basic_annual = basic_m * 12
        hra_annual = hra_m * 12

        if regime == "new":
            std_ded = std_deduction_new()
            taxable_income = gross_annual - std_ded
            # NPS employer contribution deduction (Section 80CCD(2)) – allowed in new regime
            nps_employer_80ccd2 = min(employer_pf_annual * 0,
                                       basic_annual * 0.10)  # placeholder; user may enter
            taxable_income = max(0, taxable_income)
            deductions_applied = {"standard_deduction": std_ded}
        else:
            # Old regime
            std_ded = std_deduction_old()
            # HRA exemption
            hra_exempt = hra_exemption(basic_annual, hra_annual, rent_paid_annual, is_metro)
            # LTA – simplified: claim actual (up to 2 journeys in 4-year block), user provides
            lta_exempt = min(lta_m * 12, lta_m * 12)  # actual amount claimed
            # Food allowance – Rs 50/meal * 2 meals * 22 working days * 12
            food_exempt = min(food_allowance_m * 12, 26400)
            # Transport – fully taxable post 2018
            transport_exempt = 0

            taxable_income = gross_annual - std_ded - hra_exempt - food_exempt
            # Chapter VI-A
            chapter_via = sec80c + sec80d + home_loan_interest + nps_80ccd + other_80_deductions
            # Professional tax deduction
            taxable_income -= professional_tax_annual
            taxable_income -= chapter_via
            taxable_income = max(0, taxable_income)
            deductions_applied = {
                "standard_deduction": std_ded,
                "hra_exemption": round(hra_exempt, 2),
                "food_allowance_exempt": round(food_exempt, 2),
                "professional_tax": professional_tax_annual,
                "80c": sec80c,
                "80d": sec80d,
                "home_loan_interest": home_loan_interest,
                "nps_80ccd1b": nps_80ccd,
                "other_deductions": other_80_deductions,
                "total_chapter_via": round(chapter_via, 2),
            }

        # ── Tax computation ─────────────────────────────────────────────────
        tax_data = compute_income_tax(taxable_income, regime)
        tds_annual = tax_data["total"]
        tds_monthly = round(tds_annual / 12, 2)

        # ── Take-home ────────────────────────────────────────────────────────
        take_home_annual = gross_annual - total_employee_deductions_annual - tds_annual
        take_home_monthly = round(take_home_annual / 12, 2)

        # ── Suggestions / Highlights ─────────────────────────────────────────
        suggestions = generate_suggestions(
            basic_m, hra_m, basic_annual, hra_annual,
            employee_pf_m, employer_pf_m,
            gratuity_m, basic_annual,
            sec80c, nps_80ccd, food_allowance_m,
            lta_m, ctc_annual, regime,
            rent_paid_annual, professional_tax_m,
            variable_pay_annual, gross_annual,
        )

        return jsonify({
            "success": True,
            "annual": {
                "ctc": round(ctc_annual, 2),
                "gross": round(gross_annual, 2),
                "fixed_gross": round(fixed_gross_annual, 2),
                "variable": round(variable_total_annual, 2),
                "basic": round(basic_annual, 2),
                "hra": round(hra_annual, 2),
                "employee_pf": round(employee_pf_annual, 2),
                "employer_pf": round(employer_pf_annual, 2),
                "employee_esi": round(employee_esi_annual, 2),
                "gratuity": round(gratuity_annual, 2),
                "professional_tax": round(professional_tax_annual, 2),
                "nps_employee": round(nps_employee_annual, 2),
                "other_deductions": round(other_deductions_annual, 2),
                "total_employee_deductions": round(total_employee_deductions_annual, 2),
                "taxable_income": round(taxable_income, 2),
                "income_tax": round(tax_data["tax"], 2),
                "surcharge": round(tax_data["surcharge"], 2),
                "cess": round(tax_data["cess"], 2),
                "tds": round(tds_annual, 2),
                "take_home": round(take_home_annual, 2),
            },
            "monthly": {
                "ctc": round(ctc_annual / 12, 2),
                "gross": round(gross_annual / 12, 2),
                "basic": round(basic_m, 2),
                "hra": round(hra_m, 2),
                "special_allowance": round(special_allowance_m, 2),
                "other_allowances": round(lta_m + medical_m + food_allowance_m + transport_m + other_allowances_m, 2),
                "total_employee_deductions": round(total_employee_deductions_annual / 12, 2),
                "tds": round(tds_monthly, 2),
                "take_home": round(take_home_monthly, 2),
            },
            "tax_details": {
                "regime": regime,
                "taxable_income": round(taxable_income, 2),
                "income_tax": round(tax_data["tax"], 2),
                "surcharge": round(tax_data["surcharge"], 2),
                "cess": round(tax_data["cess"], 2),
                "total_tax": round(tds_annual, 2),
                "effective_rate": round((tds_annual / gross_annual * 100) if gross_annual > 0 else 0, 2),
                "deductions_applied": deductions_applied,
            },
            "suggestions": suggestions,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


def generate_suggestions(
    basic_m, hra_m, basic_annual, hra_annual,
    employee_pf_m, employer_pf_m,
    gratuity_m, _basic_annual,
    sec80c, nps_80ccd, food_allowance_m,
    lta_m, ctc_annual, regime,
    rent_paid_annual, professional_tax_m,
    variable_pay_annual, gross_annual,
):
    tips = []

    # 1. Basic salary ratio
    basic_ratio = (basic_annual / (gross_annual if gross_annual else 1)) * 100
    if basic_ratio < 40:
        tips.append({
            "type": "warning",
            "icon": "⚠️",
            "title": "Low Basic Salary Ratio",
            "body": f"Your Basic is only {basic_ratio:.0f}% of gross. Many Indian companies keep Basic at 40–50%. A very low Basic reduces your PF contribution, gratuity eligibility, and HRA tax exemption benefit.",
        })
    if basic_ratio > 60:
        tips.append({
            "type": "info",
            "icon": "ℹ️",
            "title": "High Basic Salary",
            "body": f"Basic is {basic_ratio:.0f}% of gross. While this increases PF & gratuity benefits, it also raises your taxable base. Consider restructuring if tax saving is a priority.",
        })

    # 2. PF check – statutory minimum
    statutory_pf_m = min(basic_m * 0.12, 1800)  # 12% of basic, capped at ₹15,000 basic
    if employee_pf_m > 0 and employee_pf_m < statutory_pf_m * 0.95:
        tips.append({
            "type": "danger",
            "icon": "🚨",
            "title": "PF Below Statutory Minimum",
            "body": f"Statutory minimum Employee PF is 12% of Basic. Your entered amount (₹{employee_pf_m:,.0f}/mo) appears low. Companies must contribute 12% of basic (up to ₹1,800/mo on ₹15,000 basic cap). Verify with your employer.",
        })
    if employer_pf_m == 0 and employee_pf_m > 0:
        tips.append({
            "type": "warning",
            "icon": "⚠️",
            "title": "No Employer PF Entered",
            "body": "Employer PF is mandatory if Employee PF is deducted. Employer must contribute at least 12% of basic wages. Check your offer letter or payslip.",
        })

    # 3. Gratuity check
    statutory_gratuity_m = basic_m / 26 * 15 / 12  # Approximate monthly provision
    if gratuity_m == 0 and ctc_annual > 300000:
        tips.append({
            "type": "info",
            "icon": "📋",
            "title": "Gratuity Not Mentioned",
            "body": "Gratuity is payable after 5 years of continuous service under Payment of Gratuity Act. Monthly provision ≈ (Basic × 15/26 / 12). Often included in CTC but not in monthly payslip. Clarify with HR.",
        })

    # 4. HRA check
    if hra_m == 0 and basic_m > 0:
        tips.append({
            "type": "info",
            "icon": "🏠",
            "title": "No HRA in Salary",
            "body": "HRA (House Rent Allowance) is one of the biggest tax-saving tools under Old Regime. If you're paying rent, ask your employer to restructure your CTC to include HRA for Section 10(13A) exemption.",
        })
    if hra_m > basic_m * 0.50:
        tips.append({
            "type": "warning",
            "icon": "⚠️",
            "title": "HRA Exceeds 50% of Basic",
            "body": f"HRA exemption under Section 10(13A) is limited to 50% of Basic (metro) or 40% (non-metro). HRA beyond this threshold is fully taxable. The excess is not beneficial.",
        })

    # 5. Food allowance
    if food_allowance_m > 0 and food_allowance_m > 2200:
        tips.append({
            "type": "info",
            "icon": "🍽️",
            "title": "Food Allowance Cap",
            "body": f"Tax-free meal allowance is capped at ₹50/meal × 2 meals × 22 working days = ₹2,200/month. Your ₹{food_allowance_m:,.0f}/mo has excess that is fully taxable.",
        })

    # 6. 80C utilisation
    if regime == "old" and sec80c < 150000:
        remaining = 150000 - sec80c
        tips.append({
            "type": "tip",
            "icon": "💡",
            "title": f"₹{remaining:,.0f} of 80C Limit Unused",
            "body": f"You can invest ₹{remaining:,.0f} more under Section 80C (EPF, ELSS, PPF, NSC, life insurance premium, children's tuition, home loan principal etc.) to save additional tax.",
        })

    # 7. NPS suggestion
    if regime == "old" and nps_80ccd == 0:
        tips.append({
            "type": "tip",
            "icon": "💡",
            "title": "NPS 80CCD(1B) – Extra ₹50,000 Deduction",
            "body": "Over and above 80C, you can claim ₹50,000 additional deduction under Section 80CCD(1B) for NPS contributions. This can save ₹15,000–₹16,500 in tax (depending on slab).",
        })

    # 8. Professional Tax
    if professional_tax_m == 0 and ctc_annual > 180000:
        tips.append({
            "type": "info",
            "icon": "📌",
            "title": "Professional Tax",
            "body": "Professional Tax varies by state (max ₹200/month = ₹2,500/year in Karnataka). It's deducted from salary and is deductible under Section 16. If you're in Karnataka, PT is applicable.",
        })

    # 9. Regime suggestion
    if regime == "new" and gross_annual < 1200000:
        tips.append({
            "type": "success",
            "icon": "✅",
            "title": "New Regime Tax-Free Benefit",
            "body": f"Under the New Regime (FY 2025-26), income up to ₹12,00,000 is effectively tax-free due to Section 87A rebate. Your gross is within this limit—great choice!",
        })
    if regime == "old" and gross_annual > 1500000:
        tips.append({
            "type": "tip",
            "icon": "💡",
            "title": "Compare Both Tax Regimes",
            "body": "At income above ₹15L, the New Regime is often beneficial unless you have significant 80C/80D/HRA deductions exceeding ~₹4–5L. Run the calculation under both regimes to compare.",
        })

    # 10. Variable pay risk
    if variable_pay_annual > 0:
        var_pct = (variable_pay_annual / (gross_annual if gross_annual else 1)) * 100
        if var_pct > 25:
            tips.append({
                "type": "warning",
                "icon": "📊",
                "title": f"High Variable Component ({var_pct:.0f}% of CTC)",
                "body": "A large variable component adds income uncertainty. Variable pay is fully taxable. TDS will be deducted proportionally. Ensure you receive the actual payout before financial planning.",
            })

    return tips


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
