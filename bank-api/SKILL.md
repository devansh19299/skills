---
name: bank-api
description: Implement or extend a bank payment API integration (Axis, ICICI, HDFC, etc.) in Frappe p2p_escrow. Use when adding a new bank, a new API endpoint, or fixing a bank API call.
arguments: [task]
---

Bank API task: $task

## Step 1 — Load Context

```bash
python3 search_corpus.py "$task bank_adapter api" --app p2p_escrow --top 15
```

Key files (already in corpus — do NOT re-read unless necessary):
- `apps/p2p_escrow/p2p_escrow/bank_adapter.py` — base adapter + all bank implementations
- `apps/p2p_escrow/p2p_escrow/api.py` — whitelisted API endpoints

## Step 2 — RFC (Discuss Only)

Identify:
- Which bank and which endpoint (Transfer / Status / Beneficiary / Balance)
- Encryption required? (Axis = JWE+JWS, ICICI = composite, HDFC = plain)
- Request/response field mapping from FSD doc
- Which existing adapter pattern to follow

**No code yet.**

## Step 3 — TODO (TDD First)

```
- [ ] TEST: verify <endpoint> sends correct payload and handles success response
      File: /workspace/development/canopi-bench/apps/p2p_escrow/p2p_escrow/tests/test_<bank>_api.py
      Logic: mock requests.post, assert payload fields, assert status mapped correctly

- [ ] IMPL: add <method> to <BankAdapter> class
      File: /workspace/development/canopi-bench/apps/p2p_escrow/p2p_escrow/bank_adapter.py
      Logic: build payload → encrypt if needed → call API → parse response → return standard dict
```

Wait for approval.

## Step 4 — Execute

Standard bank adapter pattern:
```python
def call_<endpoint>(self, payout_doc):
    payload = self._build_payload(payout_doc)
    # encrypt if required
    response = self._make_request("POST", self.base_url + "/endpoint", payload)
    return self._parse_response(response)
```

Always:
- Log request + response to `Escrow API Log`
- Map bank status codes → internal status (Initiated / Success / Failed / Pending)
- Handle network errors + bank error codes separately
- Never store raw credentials in code — use `Escrow Bank API Config`
