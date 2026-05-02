---
name: doctype
description: Create a new Frappe DocType with TDD boilerplate, controller, and bench scaffold. Use when building a new DocType from scratch.
arguments: [name, app]
---

Create DocType: $name in app: $app

## Step 1 — Load Context

```bash
python3 search_corpus.py "$name $app" --top 10
```

Check for similar existing DocTypes to follow the same pattern.

## Step 2 — RFC (Discuss Only)

Define:
- Fields (fieldname, fieldtype, label, required, options for Link/Select)
- Is it submittable? Child table? Track changes?
- Which DocTypes does it link to?
- Permissions (roles that can read/write/submit)
- Controller hooks needed (validate, on_submit, on_cancel, before_save)

**No code yet.**

## Step 3 — TODO (TDD First)

```
- [ ] TEST: verify <validation rule>
      File: /workspace/development/canopi-bench/apps/$app/$app/doctype/<snake_name>/test_<snake_name>.py
      Logic: create doc, set invalid value, assert frappe.ValidationError raised

- [ ] SCAFFOLD: run bench new-doctype
      Command: cd /workspace/development/canopi-bench && bench new-doctype "$name" --app $app

- [ ] IMPL: define fields in <snake_name>.json
      File: apps/$app/$app/doctype/<snake_name>/<snake_name>.json

- [ ] IMPL: add validate() and hooks to controller
      File: apps/$app/$app/doctype/<snake_name>/<snake_name>.py
```

Wait for approval.

## Step 4 — Execute

```bash
cd /workspace/development/canopi-bench
bench new-doctype "$name" --app $app
```

Controller pattern:
```python
import frappe
from frappe.model.document import Document

class <ClassName>(Document):
    def validate(self):
        self._validate_<rule>()

    def _validate_<rule>(self):
        if <condition>:
            frappe.throw(_("<message>"))
```

After implementation:
```bash
bench run-tests --app $app --doctype "$name"
bench migrate  # if schema changed
```
