---
name: approval
description: Add or fix a maker-checker approval workflow on a Frappe DocType. Use when adding approve/reject actions, pending approval status, or checker permissions.
arguments: [doctype, app]
---

Add maker-checker approval workflow to: $doctype in $app

## Step 1 — Load Context

```bash
python3 search_corpus.py "$doctype approval maker checker" --app $app --top 10
```

## Step 2 — RFC (Discuss Only)

Define:
- Status flow: Draft → Pending Approval → Approved / Rejected
- Who is Maker (submits for approval) and Checker (approves/rejects)
- Fields needed: maker_user, maker_submitted_datetime, checker_user, checker_datetime, checker_remarks
- Should rejection allow re-submission?
- Any amount/count limits that trigger approval?

**No code yet.**

## Step 3 — TODO (TDD First)

```
- [ ] TEST: maker cannot approve own submission
      File: apps/$app/$app/doctype/<snake>/test_<snake>.py
      Logic: submit as maker, try approve as same user, assert PermissionError

- [ ] TEST: checker can approve and status changes
      Logic: submit as maker, approve as checker, assert status == "Approved"

- [ ] IMPL: add approval fields to DocType JSON
      Fields: status (Select), maker_user (Link→User), maker_submitted_datetime (Datetime),
              checker_user (Link→User), checker_approved_datetime (Datetime), checker_remarks (Small Text)

- [ ] IMPL: add send_for_approval(), approve(), reject() methods to controller
      File: apps/$app/$app/doctype/<snake>/<snake>.py
```

Wait for approval.

## Step 4 — Execute

Standard pattern:
```python
def send_for_approval(self):
    if self.status != "Draft":
        frappe.throw(_("Only Draft documents can be sent for approval"))
    self.status = "Pending Approval"
    self.maker_user = frappe.session.user
    self.maker_submitted_datetime = frappe.utils.now()
    self.save()

def approve(self, remarks=""):
    self._check_checker_permission()
    if self.maker_user == frappe.session.user:
        frappe.throw(_("Maker cannot approve their own submission"))
    self.status = "Approved"
    self.checker_user = frappe.session.user
    self.checker_approved_datetime = frappe.utils.now()
    self.checker_remarks = remarks
    self.save()

def reject(self, remarks):
    self._check_checker_permission()
    if not remarks:
        frappe.throw(_("Rejection reason is required"))
    self.status = "Rejected"
    self.checker_user = frappe.session.user
    self.checker_approved_datetime = frappe.utils.now()
    self.checker_remarks = remarks
    self.save()

def _check_checker_permission(self):
    if not frappe.has_role("Checker"):
        frappe.throw(_("Only users with Checker role can approve/reject"))
```
