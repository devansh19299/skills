---
name: read-spec
description: Parse a bank FSD, BRD, or API spec document and extract field mappings, payload structure, and implementation notes. Use when given a new API spec document to implement.
arguments: [spec]
---

Parse spec: $spec

## Step 1 — Extract Key Information

Read the spec and extract into a structured table:

**API Endpoints:**
| Endpoint | Method | URL | Auth |
|---|---|---|---|
| | | | |

**Request Fields:**
| Field Name | Type | Required | Description | Maps To (internal field) |
|---|---|---|---|---|
| | | | | |

**Response Fields:**
| Field Name | Type | Description | Maps To (internal field) |
|---|---|---|---|
| | | | |

**Status/Error Codes:**
| Code | Meaning | Internal Status |
|---|---|---|
| | | |

## Step 2 — Encryption / Auth Details

- Auth type: (API Key / OAuth / JWE+JWS / mTLS / Basic)
- Headers required:
- Encryption algorithm: (if any)
- Signature algorithm: (if any)

## Step 3 — Implementation Notes

- Which existing bank adapter pattern is closest?
- Any special handling (polling for status? webhooks? retries?)
- Sandbox vs production URL differences
- Rate limits or timeouts mentioned

## Step 4 — Output RFC

Produce a concise RFC summarising:
1. What endpoints to implement (priority order)
2. Field mapping table (spec field → internal Frappe field)
3. Any blockers or missing information in the spec

Do NOT write code yet — this is input for `/bank-api` or `/dev`.
