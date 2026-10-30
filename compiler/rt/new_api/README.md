# @@NAME@@

A JSON API in [Vu](https://github.com/vu0tran/vu) with accounts and PostgreSQL, made by `vu new api @@NAME@@`.
(`vu` is the script at the top of the Vu repository.)

```
export DATABASE_URL=postgresql://user:password@localhost:5432/@@NAME@@
vu run main.vu                  # http://localhost:8080; it makes its tables on start
vu check main.vu                # every compile error, in milliseconds
vu build main.vu -o app         # the optimized binary
```

Try it:

```
curl -s localhost:8080/signup -d '{"email": "ada@example.com", "password": "correct horse battery"}'
# {"id": 1, "email": "ada@example.com", "token": "..."}
curl -s localhost:8080/notes -H "Authorization: Bearer TOKEN" -d '{"text": "first note"}'
curl -s localhost:8080/notes -H "Authorization: Bearer TOKEN"
```

| route | does |
|---|---|
| `POST /signup {email, password}` | makes an account and signs in: 201 with a token, and a session cookie |
| `POST /login {email, password}` | signs in: 200 with a token and a cookie; 401 for a wrong email or password |
| `POST /logout` | ends the session |
| `GET /me` | the signed-in user |
| `GET /notes`, `POST /notes {text}`, `DELETE /notes/:id` | the user's notes |
| `GET /health` | `{"ok": true}`, for the platform's health check |

Browsers send the cookie (HttpOnly, Secure, SameSite=Lax); other clients send `Authorization: Bearer
TOKEN`. Passwords are stored as PBKDF2 hashes in Django's format, and sessions as SHA-256 hashes of
their tokens. Every SQL statement is written in the program, so values reach the database only as
parameters. Requests from other sites that would change something are refused (`web.same_origin`).

## Deploy

On [Railway](https://railway.com): push this folder to a GitHub repository, create a project from it,
add a PostgreSQL database, and give the app the variable `DATABASE_URL = ${{Postgres.DATABASE_URL}}`.
`railway.json` tells Railway to build the Dockerfile and check `/health`. With the CLI, from this
folder: `railway init`, `railway add --database postgres`, `railway up`.

With Docker (any host that runs containers):

```
docker build -t @@NAME@@ .
docker run -p 8080:8080 -e DATABASE_URL=... @@NAME@@
```

The app reads `PORT` (default 8080) and `DATABASE_URL` (`postgresql://user:password@host:port/db`,
with `?sslmode=require` for TLS).
