---
name: test
description: Run Frappe tests, show failures clearly, and suggest fixes. Use when running bench run-tests or checking why tests fail.
arguments: [app, doctype]
---

Run tests for app: $app doctype: $doctype

## Step 1 — Run Tests

```bash
cd /workspace/development/canopi-bench

# Run specific doctype tests
bench run-tests --app $app --doctype "$doctype" 2>&1 | tail -60

# Run all tests for app
bench run-tests --app $app 2>&1 | tail -80

# Run a specific test method
bench run-tests --app $app --test test_method_name
```

## Step 2 — Parse Results

For each FAIL or ERROR:
1. Show the test name
2. Show the exact assertion that failed
3. Show the relevant traceback frame (not the whole stack)
4. State what the test expected vs what it got

## Step 3 — Root Cause

For each failure, classify:
- **Wrong implementation** → fix the controller/service code
- **Wrong test** → the test assertion is incorrect
- **Missing data** → test setup (`setUp`) doesn't create required records
- **DB state** → leftover data from previous test; add `frappe.db.rollback()` in tearDown

## Step 4 — Fix & Re-run

Fix the root cause, then:
```bash
bench run-tests --app $app --doctype "$doctype"
```

Confirm all pass before reporting done.
