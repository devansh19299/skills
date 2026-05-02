---
name: debug
description: Debug a Frappe error or unexpected behaviour. Use when there is a traceback, wrong output, or something not working as expected.
arguments: [issue]
---

Debug this Frappe issue: $issue

## Step 1 — Reproduce & Locate

Run these to get the full picture:
```bash
# Get last 100 lines of frappe logs
tail -100 logs/frappe.log | grep -A 10 "Error\|Traceback\|Exception"

# Check worker logs if background job
tail -50 logs/worker.log

# Check the bench console for quick queries
bench --site <site> console
```

## Step 2 — Identify Type

Classify the error:
- **ValidationError** → check `validate()` method in the controller
- **DoesNotExist** → the linked document doesn't exist; check field value
- **PermissionError** → check user roles and DocType permissions
- **TypeError / AttributeError** → check method signature and None values
- **IntegrityError** → check DB constraints, duplicate unique fields

## Step 3 — Trace the Stack

1. Read the full traceback top-to-bottom — the **last frame** is where it broke
2. Open that exact file + line number
3. Check what value each variable holds at that point using `frappe.logger().debug()`

## Step 4 — Fix

- Make the minimal change that fixes the root cause
- Do NOT add broad try/except to hide the error
- Do NOT add workarounds without understanding the cause

## Step 5 — Verify

```bash
bench run-tests --app <app> --doctype "<DocType>"
bench --site <site> console
# reproduce the original steps manually
```

Report: what was the root cause, what was changed, and how it was verified.
