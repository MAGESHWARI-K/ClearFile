import re

# Deliberately transparent rule-based extraction for the prototype.
PATTERNS = {
    "Name": r"(?:applicant\s+name|employee\s+name|name)\s*[:\-]\s*([A-Za-z][A-Za-z .'-]+)",
    "Employer": r"(?:employer|company|organization)\s*[:\-]\s*([A-Za-z0-9 &.,'-]+)",
    "Monthly Salary": r"(?:monthly\s+salary|net\s+salary|gross\s+salary|salary|net\s+pay)\s*[:\-]\s*(?:INR|Rs\.?|₹)?\s*([0-9,]+(?:\.\d{1,2})?)",
    "Tax ID": r"(?:PAN|tax\s*id|tax\s*identification\s*number)\s*[:\-]\s*([A-Z]{5}[0-9]{4}[A-Z])",
    "Account Number": r"account\s*(?:no|number)\s*[:\-]\s*([0-9Xx*-]{6,})",
    "Date of Birth": r"(?:date\s+of\s+birth|DOB)\s*[:\-]\s*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})",
    "Address": r"(?:residential\s+address|address)\s*[:\-]\s*([^\n]+)",
    "IFSC Code": r"IFSC(?:\s+code)?\s*[:\-]\s*([A-Z]{4}0[A-Z0-9]{6})",
    "Employment Type": r"employment\s+type\s*[:\-]\s*([A-Za-z -]+)",
}

def extract_fields(text: str) -> dict:
    result = {}
    for field, pattern in PATTERNS.items():
        match = re.search(pattern, text, re.I)
        if match:
            value = match.group(1).strip().rstrip(".,;")
            if field == "Monthly Salary":
                value = value.replace(",", "")
            if field in {"Tax ID", "IFSC Code"}:
                value = value.upper()
            result[field] = value
    return result
