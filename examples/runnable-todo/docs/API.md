# Task API contract

All requests use JSON. Protected endpoints require `Authorization: Bearer <token>`.

| Method | Path | Body | Expected status |
|---|---|---|---|
| POST | `/api/register` | `{ "email":"a@b.com", "password":"long-password" }` | 201; returns token |
| POST | `/api/login` | same fields | 200; returns token |
| GET | `/api/tasks` | — | 200; returns tasks owned by caller |
| POST | `/api/tasks` | `{ "title":"Buy milk" }` | 201 |
| PATCH | `/api/tasks/{id}` | `{ "done": true }` | 200 |
| DELETE | `/api/tasks/{id}` | — | 200 |

Cross-user task access responds 404; unauthorized requests respond 401. This is a local educational implementation and does not claim full production security.
