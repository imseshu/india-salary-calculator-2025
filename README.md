# 🇮🇳 India Salary Calculator — FY 2025-26

A production-grade Python/Flask web application to calculate **take-home salary** from CTC with full Indian tax compliance for **Financial Year 2025-26 (AY 2026-27)**.

---

## ✨ Features

- **Complete salary breakup** — Basic, HRA, Special Allowance, LTA, Food, Transport, NPS, PF, ESI, Gratuity
- **Variable pay & Bonus** support
- **New Tax Regime** (default — Budget 2024) and **Old Tax Regime** side-by-side
- **Section 87A rebate** — effective zero tax up to ₹12L (New Regime)
- **HRA exemption** (Section 10(13A)) — metro/non-metro, 3-condition test
- **Chapter VI-A deductions** — 80C, 80D, 80CCD(1B), Section 24(b) Home Loan Interest
- **Surcharge + Health & Education Cess (4%)** computation
- **Monthly and Annual** breakdown views
- **Smart Highlights** — 10+ compliance checks and tax-saving suggestions
- Beautiful, responsive UI with dark navy/saffron theme

---

## 🚀 Running Locally

### Option 1: Python directly

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```
Open http://localhost:5000

### Option 2: Docker

```bash
# Build the image
docker build -t india-salary-calc .

# Run the container
docker run -p 5000:5000 india-salary-calc
```

### Option 3: Docker Compose

```bash
docker compose up --build
```

---

## 📁 Project Structure

```
india-salary-calc/
├── app.py                 # Flask backend + tax calculation engine
├── templates/
│   └── index.html         # Single-page frontend (HTML/CSS/JS)
├── static/                # Static assets (if any)
├── requirements.txt       # Python dependencies
├── Dockerfile             # Multi-stage production Docker build
├── docker-compose.yml     # Compose for easy deployment
└── README.md
```

---

## 🧮 Tax Computation Logic

### New Regime Slabs (FY 2025-26)
| Income Range | Rate |
|---|---|
| Up to ₹4,00,000 | 0% |
| ₹4,00,001 – ₹8,00,000 | 5% |
| ₹8,00,001 – ₹12,00,000 | 10% |
| ₹12,00,001 – ₹16,00,000 | 15% |
| ₹16,00,001 – ₹20,00,000 | 20% |
| ₹20,00,001 – ₹24,00,000 | 25% |
| Above ₹24,00,000 | 30% |

> Section 87A rebate makes income up to ₹12,00,000 effectively tax-free under New Regime.

### Old Regime Slabs
| Income Range | Rate |
|---|---|
| Up to ₹2,50,000 | 0% |
| ₹2,50,001 – ₹5,00,000 | 5% |
| ₹5,00,001 – ₹10,00,000 | 20% |
| Above ₹10,00,000 | 30% |

---

## ⚠️ Disclaimer

This tool is for **indicative purposes only**. Tax calculations are based on publicly known FY 2025-26 provisions. For precise TDS or ITR computations, consult a qualified Chartered Accountant or tax professional.

---

## 📦 Production Notes

- Uses **Gunicorn** WSGI server (2 workers, 4 threads) in Docker
- Runs as **non-root user** inside the container
- Multi-stage Docker build keeps image slim
- Resource limits configured in docker-compose.yml
