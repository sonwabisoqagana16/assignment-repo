import os
from datetime import date, timedelta
import pandas as pd

REPORT_DIR = "/var/clinic/reports"

def reporting_period(run_date: date) -> tuple[date, date]:
    end = run_date - timedelta(days=(run_date.weekday() + 1) % 7)
    return end - timedelta(days=6), end

def compute_metrics(appts, encounters, billing, patients, start, end) -> dict:
    return {
        "total_appointments": len(appts),
        "completed_visits": int((encounters["status"] == "completed").sum()),
        "cancelled": int((appts["status"] == "cancelled").sum()),
        "no_shows": int((appts["status"] == "no-show").sum()),
        "unique_patients": patients["patient_id"].nunique(),
        "new_patients": int((patients["first_visit_date"].dt.date >= start).sum()),
        "total_revenue": round(float(billing["amount_paid"].sum()), 2),
        "outstanding_balance": round(float((billing["amount_due"] - billing["amount_paid"]).sum()), 2),
        "visits_by_day": encounters.groupby(encounters["encounter_date"].dt.date).size().to_dict(),
        "top_visit_reasons": encounters["visit_reason"].value_counts().head(5).to_dict(),
    }

def generate_weekly_report(run_date: date = date.today()) -> None:
    start, end = reporting_period(run_date)
    label = f"{start}_to_{end}"

    appts = get_appointments(start, end).drop_duplicates("appointment_id")
    encounters = get_encounters(start, end).drop_duplicates("encounter_id")
    billing = get_billing(start, end).drop_duplicates("transaction_id")
    patients = get_patients_seen(start, end)

    metrics = compute_metrics(appts, encounters, billing, patients, start, end)

    rows = [{"metric": k, "value": v} for k, v in metrics.items() if not isinstance(v, dict)]
    pd.DataFrame(rows).to_csv(os.path.join(REPORT_DIR, f"clinic_weekly_{label}.csv"), index=False)
    write_pdf(metrics, os.path.join(REPORT_DIR, f"clinic_weekly_{label}.pdf"))

if __name__ == "__main__":
    generate_weekly_report