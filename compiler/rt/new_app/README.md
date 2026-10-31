# @@NAME@@

A web app with accounts in [Vu](https://github.com/vu0tran/vu), rendered on the server, made by
`vu new app @@NAME@@`. (`vu` is the script at the top of the Vu repository.)

```
export DATABASE_URL=postgresql://user:password@localhost:5432/@@NAME@@
export SECRET=$(head -c 24 /dev/urandom | base64)   # signs the CSRF tokens in forms
vu run main.vu                  # http://localhost:8080; it applies migrations/*.sql on start
vu check main.vu                # every compile error, in milliseconds
```

- `main.vu`: the pages (templates written in the file: every value they show is escaped), the
  forms and their handlers.
- `migrations/`: the tables. Each `.sql` file runs once, in name order, when the app starts; to
  change them, add `002_something.sql` (don't edit one that has run).
- `public/`: files served at `/static/...`.

What's taken care of: passwords are stored as PBKDF2 hashes (Django's format), sessions are
cookies (HttpOnly, Secure, SameSite=Lax) whose tokens the database keeps only as hashes, every form
carries a CSRF token, requests from other sites that would change something are refused, sign-ins
are limited to 20 a minute per address, and SQL takes values only as parameters.

## Deploy

On [Railway](https://railway.com): push this folder to a GitHub repository, create a project from it,
add a PostgreSQL database, and give the app the variables `DATABASE_URL = ${{Postgres.DATABASE_URL}}`
and `SECRET` (32 random characters). `railway.json` tells Railway to build the Dockerfile and check
`/health`.

With Docker: `docker build -t @@NAME@@ .` and `docker run -p 8080:8080 -e DATABASE_URL=... -e SECRET=... @@NAME@@`.
