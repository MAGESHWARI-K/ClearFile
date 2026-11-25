# Test suite

Run from `ClearFile_Complete`:

```powershell
python -m unittest discover -s tests -v
```

The suite checks supervisor dispatch/checkpointing, mismatch and missing-evidence flags, Pydantic validation, independent mutable defaults, human-decision guardrails, and background queue claim/retry transitions.
