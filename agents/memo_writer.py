def create_memo(application_id: str, findings: list, anomalies: list, documents: list) -> str:
    matches = sum(1 for x in findings if x['status'] == 'Match')
    mismatches = sum(1 for x in findings if x['status'] == 'Mismatch')
    unavailable = sum(1 for x in findings if x['status'] == 'Not Available')
    lines = [f"VERIFICATION MEMO — {application_id}", "", "Summary", f"Documents processed: {len(documents)}", f"Fields compared: {len(findings)}", f"Full matches: {matches}", f"Potential inconsistencies: {mismatches}", f"Fields missing from one or more documents: {unavailable}", "", "Findings"]
    if not findings: lines.append("No shared fields were available for comparison.")
    for f in findings:
        details = "; ".join(f"{k}: {v}" for k,v in f['values'].items())
        if f.get('missing_documents'):
            details += "; Not available in: " + ", ".join(f['missing_documents'])
        lines.append(f"- {f['field']} — {f['status']}: " + details)
    lines += ["", "Officer action", "Review original source documents and resolve any flagged inconsistencies before making a decision.", "", "ClearFile supports human review and does not approve or reject applications automatically."]
    return "\n".join(lines)
