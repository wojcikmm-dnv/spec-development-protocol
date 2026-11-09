---
name: error-handling
description: Guidance for implementing consistent, observable error handling. Use when adding error handling, failure logging, retries, timeouts, or user-facing error messages.
---

# Skill: Error Handling

## Purpose

Implement error handling that is observable, safe for users, and actionable for developers.

## Prerequisites

- Error categories are understood (user error, system error, etc.).
- Logging stack is defined in `TECH.md`.
- The project's existing error types and response shape have been read; reuse them.

## Checklist

1.  **Classify Errors**: Distinguish between user errors (4xx), system errors (5xx), programmer errors, and transient errors.
2.  **Backend/API**: Validate input at the entry point. Use a consistent error response shape. Never expose stack traces. Return correct HTTP status codes. Log system errors with a trace ID.
3.  **Service/Domain**: Return explicit error types (e.g., Result objects) or the project's established exception types instead of throwing generic exceptions. Don't swallow errors; re-throw or convert them while preserving the cause. Never turn a failure into a success-shaped value such as an empty list or `null`.
4.  **Frontend/UI**: Handle loading, success, and error states for every async call. Show user-friendly messages with a way to recover or retry. Use the framework's error boundary mechanism to prevent page crashes. Log UI errors to the project's tracking service.
5.  **Retries & Timeouts**: Set explicit timeouts on all external calls. Retry only idempotent operations, using exponential backoff with jitter and a retry cap. Use a circuit breaker for unreliable dependencies.
6.  **Cleanup**: Release resources (connections, handles, locks) on every error path, and leave state consistent when an operation fails midway.
7.  **Logging**: Log each failure once, at the layer that handles it, with context but without secrets or personal data.
8.  **Comments**: Explain only durable, non-obvious failure or compatibility
    rationale. Do not leave task identifiers or implementation-session notes.

## Quality Bar

- Every async call has an explicit error handler.
- No internal error details leak to API responses or UI.
- All errors are logged with sufficient context for debugging, and none twice.
- Error paths, including timeouts and partial failures, are covered by tests.
