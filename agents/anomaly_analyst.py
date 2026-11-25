def analyse(findings: list) -> list:
    anomalies = []
    for item in findings:
        if item.get("status") == "Mismatch":
            anomalies.append({"field": item["field"], "severity": "Review required", "message": f"Conflicting {item['field'].lower()} values were found across the supplied documents.", "documents": item["documents"], "values": item["values"]})
    return anomalies
