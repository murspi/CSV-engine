import os
from schemas import ProcessResponse
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("report.html")

def generate_report(result: ProcessResponse) -> str:
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("data/reports", exist_ok=True)
    output_path = os.path.join("data", "reports", "report.html")
    context = {
        "timestamp": timestamp,
        "success": result.success_or_failure,
        "rows_in": result.rows_in,
        "rows_out": result.rows_out,
        "duplicates_dropped": result.duplicates_dropped,
        "violations_dropped": result.required_field_violations_dropped,
        "columns_validated": result.columns_validated
    }
    html = template.render(context)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path