---
name: create-api-endpoint
description: Guidance for implementing secure, well-structured REST API endpoints. Use when adding or changing an HTTP endpoint, route handler, or API contract.
---

# Skill: Create REST API Endpoint

## Purpose

Produce a consistent, secure, and documented HTTP endpoint that meets its design contract.

## Prerequisites

- API contract (path, method, schemas) is defined in the design spec.
- Auth requirements are specified.
- The closest existing endpoint has been read; follow its layering, error shape,
  and test style rather than introducing a new pattern.

## Checklist

1.  **Route**: Use plural nouns for resources (`/users`) and correct HTTP methods (GET, POST, etc.). Match the project's existing versioning and naming.
2.  **Input Validation**: Reject invalid input immediately with a `400 Bad Request` (or the project's validation status). Use a schema validation library. Validate type, range, length, and format of body, query, path, and headers; reject unknown or oversized input where the contract is closed.
3.  **Auth**: Apply auth middleware to non-public routes. Check resource-level permissions on the specific record, not only the role, so one user cannot read or change another's data by changing an ID. Return `401` (unauthenticated) or `403` (unauthorized); follow the project's choice of `404` for hidden resources.
4.  **Business Logic**: Delegate logic to a service layer. Keep route handlers thin. Handle `404 Not Found` explicitly. Keep multi-step writes atomic (transaction or compensating action).
5.  **Idempotency and concurrency**: Make `PUT` and `DELETE` idempotent. For `POST` that can be retried, support an idempotency key or a natural unique constraint. Guard concurrent updates (version, ETag, or row lock) when lost updates matter. Return `409` on conflicts.
6.  **Collections**: Paginate list endpoints with a bounded page size and a stable sort. Avoid per-item queries inside loops (N+1).
7.  **Error Handling**: Never expose stack traces. Use a consistent error response shape. Log errors with a trace ID.
8.  **Response**: Return correct status codes (`200`, `201`, `204`, etc.). Include `Location` header for `201 Created`. Use DTOs to avoid over-exposing data; never return password hashes, tokens, or internal fields.
9.  **Documentation**: Update OpenAPI/Swagger when the public contract changes.
    Do not add story/task/AC comments to handlers; keep only durable rationale
    that cannot be expressed in code or the API contract.

## Quality Bar

- Rejects invalid input with `400`.
- Covered by integration tests: happy path, validation failure, unauthenticated, unauthorized (another user's resource), not found, and conflict where applicable.
- No internal details (secrets, stack traces) leak in responses.
- Auth is enforced and tested.
- The change is backward compatible, or the contract change was approved in the plan.
