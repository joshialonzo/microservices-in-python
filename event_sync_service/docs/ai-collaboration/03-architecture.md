# 03 — Architecture

## Stack

| Layer | Choice |
|---|---|
| API | FastAPI (Python 3.12), Pydantic models |
| Frontend | Next.js (App Router, TypeScript) |
| Storage | DynamoDB |
| Compute | AWS Lambda behind API Gateway (HTTP API) |
| IaC | AWS CDK (TypeScript) |
| Local dev | Docker Compose + DynamoDB Local |

**Why this stack.** The reconciliation logic is the substance of the assessment, and Python is the
right language for it. FastAPI gives typed request/response models and a free OpenAPI page at `/docs`
— useful when the deliverable includes "expose the reconciled data through a REST API," because the
reviewer gets an interactive contract without reading the code. Next.js keeps the frontend typed
against the same shapes.

**Honest note on the serverless choice.** For 42 records read from two static JSON files, Lambda +
DynamoDB + CDK is more infrastructure than the problem requires; a single process with an in-memory
store would satisfy every functional requirement. It is here to demonstrate production
architecture, and the design below is written so that ambition does not compromise the two things the
statement actually grades: the single-command start and the README.

---

## The single-command requirement

The statement requires: *"The service should start with a single command (document it)."* A serverless
stack does not naturally satisfy this, so the local path is the primary documented one:

```bash
docker compose up
```

Brings up three containers: DynamoDB Local, the FastAPI app (via Uvicorn, hot-reload), and Next.js.
An init container runs table creation and the ingest job, so the app is populated the moment it is
reachable. No AWS account, no credentials, no network needed to evaluate this project.

Deployment is the secondary path, documented separately:

```bash
npm --prefix infra run deploy
```

**The design constraint that follows:** the business logic must not know whether it is running in
Lambda or Uvicorn, and the repository layer must not know whether it is talking to DynamoDB Local or
real DynamoDB. Both are satisfied by a `Settings`-driven endpoint override and a repository interface,
so the identical container image runs in both places. If local and deployed could diverge, the local
path would rot and the reviewer would be the one to discover it.

---

## Layout

```
event_sync_service/
├── data/                          # provided source files (unmodified)
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app + Mangum adapter for Lambda
│   │   ├── config.py              # Settings (env-driven)
│   │   ├── api/routes.py          # HTTP layer only — no logic
│   │   ├── models/                # Pydantic: NormalizedEvent, UnifiedMeeting, ProvenanceField…
│   │   ├── ingest/                # source adapters: crm.py, calendar.py
│   │   ├── reconcile/
│   │   │   ├── normalize.py       # parsing + quality flags
│   │   │   ├── dedupe.py          # intra-source
│   │   │   ├── matcher.py         # scoring + assignment
│   │   │   └── merge.py           # precedence + provenance
│   │   ├── repository/            # DynamoDBRepository + InMemoryRepository
│   │   └── jobs/sync.py           # the pipeline entrypoint
│   └── tests/
├── frontend/                      # Next.js
├── infra/                         # CDK app
├── docs/ai-collaboration/         # this folder
├── docker-compose.yml
└── README.md
```

**Why `reconcile/` is four files.** They are four independently testable decisions from
[02-reconciliation-design.md](02-reconciliation-design.md). Collapsing them into one `reconcile.py`
would make the interesting part of this project a single 400-line function, and the pipeline stages
are exactly the seams a reviewer will want to inspect.

The pure functions in `reconcile/` take and return plain models — no I/O, no AWS, no framework. That
is what lets the correctness fixture run in milliseconds with no containers.

---

## Data model (DynamoDB single-table)

One table, `EventSyncTable`:

| Entity | PK | SK |
|---|---|---|
| Unified meeting | `MEETING#<id>` | `META` |
| Raw source record | `MEETING#<id>` | `SOURCE#CRM#CRM-1001` |
| Sync run summary | `SYNC#<run_id>` | `META` |

GSI1 (`GSI1PK = DATE#<yyyy-mm-dd>`, `GSI1SK = <start_time>#<id>`) serves the primary list view in
date order.

**Why single-table.** The dominant access pattern is "fetch a meeting with all of its source records,"
which is one query on a shared partition key. Storing the raw source records adjacent to the merged
record is also what makes the provenance UI cheap: the detail view is one query, not a join.

**Why store raw records at all.** The frontend must show the user what each source said. Keeping the
raw payload means the merge can be re-run with different precedence rules without re-ingesting, and
the API can always answer "what did the CRM actually say?" — which is the whole provenance feature.

**Consistency.** A sync run writes a new generation and flips a pointer, so readers never observe a
half-written dataset. At 24 items this is theatre; it is the correct pattern at scale and costs
nothing to express.

---

## API surface

| Endpoint | Purpose |
|---|---|
| `GET /api/meetings` | Unified list. Filters: `origin` (`both`/`crm_only`/`calendar_only`), `has_conflicts`, `date_from`/`date_to`, `owner`. |
| `GET /api/meetings/{id}` | One meeting with full provenance, match evidence, and both raw source records. |
| `GET /api/stats` | Counts: total, matched, source-only, conflicts by kind, data-quality flags by code, records in vs. out. |
| `POST /api/sync` | Re-run the pipeline (idempotent). |
| `GET /api/health` | Liveness. |
| `GET /docs` | OpenAPI UI. |

`GET /api/stats` exists because it is how a reviewer verifies the reconciliation in five seconds
without reading a line of code: 42 records in, 24 meetings out, 17 matched, 4 conflicts.

---

## Frontend

Three views:

1. **Meeting list** — date-ordered, each row badged `Both` / `CRM only` / `Calendar only`, with a
   conflict indicator and a data-quality indicator. Filter controls map 1:1 to the API's query params.
2. **Meeting detail** — merged record on top; below it, a side-by-side of the raw CRM and Calendar
   records with conflicting fields highlighted and the match evidence (per-signal score breakdown)
   shown. This is the view that answers "where did this come from and why do you think these are the
   same meeting?"
3. **Sync overview** — the `/api/stats` numbers, plus the data-quality flag list linking to the
   affected records.

Visual design is explicitly not being evaluated, so styling stays minimal and the effort goes into
making provenance and conflicts legible.

---

## What is deliberately out of scope

Auth, pagination, real upstream API clients with retry/backoff, DynamoDB streams, CloudWatch alarms,
CI/CD. Each is a paragraph in the README explaining what would change, which is more useful to a
reviewer than a half-built version of any of them.
