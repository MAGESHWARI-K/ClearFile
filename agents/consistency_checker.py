def compare_documents(documents: dict) -> list:
    """Compare extracted fields and explicitly show fields absent from documents."""
    fields = sorted({key for data in documents.values() for key in data.keys()})
    findings = []
    total_docs = len(documents)
    for field in fields:
        values = [(name, data[field]) for name, data in documents.items()
                  if field in data and str(data[field]).strip()]
        missing_docs = [name for name, data in documents.items()
                        if field not in data or not str(data.get(field, '')).strip()]
        if not values:
            continue
        normalized = {str(value).strip().lower().replace(',', '') for _, value in values}
        if len(normalized) > 1:
            status = 'Mismatch'
        elif missing_docs:
            status = 'Not Available'
        else:
            status = 'Match'
        findings.append({
            'field': field,
            'status': status,
            'documents': [name for name, _ in values],
            'values': dict(values),
            'missing_documents': missing_docs,
            'documents_checked': total_docs,
        })
    return findings
