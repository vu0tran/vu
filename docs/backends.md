# Backends in Vu: from nothing to deployed

This is the path from an empty folder to an app with accounts running on Railway. Each step says
what to run and what you get. Everything here is checked by the test suites named at the end.

## 1. Start from a template

```
vu new app notes        # pages rendered on the server, with accounts
vu new api notes        # or: a JSON API with accounts (cookies for browsers, Bearer tokens for others)
cd notes
```

You get `main.vu`, `migrations/001_init.sql`, a `Dockerfile`, `railway.json` and a README. The app
already has sign-up, sign-in, sign-out, sessions, a page (or API) of notes for each user, CSRF
checks, a limit on sign-in attempts, and `/health`.

## 2. Run it

It needs PostgreSQL. With Docker:

```
docker run -d --name pg -e POSTGRES_PASSWORD=pw -p 5432:5432 postgres:16
export DATABASE_URL=postgresql://postgres:pw@localhost:5432/postgres
export SECRET=$(head -c 24 /dev/urandom | base64)      # vu new app only: signs the forms' CSRF tokens
vu run main.vu                                          # http://localhost:8080
```

On start it applies `migrations/*.sql` it hasn't applied yet. `vu check main.vu` gives every compile
error in milliseconds; run it after each change.

## 3. Change it

- **A table or column**: add `migrations/002_what.sql` (plain SQL). Never edit a file that has run;
  the app refuses to start if one changed.
- **A route**: write a handler and add it in `main`. A handler that needs the database takes
  `var db: pg.Db` and is routed with `route(net, os, env, handler)`, which lends it a connection
  from the pool.
- **SQL**: `pg.query(net, &db, "select ... where id = $1", [id])?`. The SQL must be text written in
  the program; values go as `$1`, `$2`. Building SQL from values doesn't compile, so SQL injection
  can't be written.
- **A page**: `web.render("<p>{{name}}</p>", [web.v("name", name)])`. Every value is escaped; to
  insert HTML you made, use `web.h(name, html)` with a `web.Html` from another `render`.
- **Background work** (emails, reports, anything that may fail and must be retried):
  `jobs.enqueue(net, &db, os, "kind", payload, 0.0)?` and a worker, `jobs.work(...)`, in a task.
  Jobs live in PostgreSQL, so a restart doesn't lose them.
- **Email**: `mail.send_resend(net, key, m)?` or `mail.send_smtp(net, os, cfg, m)?`.
- **Payments**: `stripe.checkout(...)` for a Checkout page, and `stripe.verify_webhook(secret, req,
  os.time())` in the webhook route before believing anything in it.
- **Files**: `s3.presign(bucket, "PUT", key, 600, os.time())` gives the browser a URL to upload to
  directly; `s3.get`, `s3.put` and `s3.delete` for the app itself.

`examples/saas` uses all of these together.

## 4. Deploy on Railway

1. Push the folder to a GitHub repository.
2. On railway.com: New Project, Deploy from GitHub repo, pick it. Railway builds the `Dockerfile`
   (`railway.json` says so) and checks `/health`.
3. In the project: New, Database, PostgreSQL.
4. In the app's Variables: `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`, and for `vu new app`,
   `SECRET` = 32 random characters.
5. In the app's Settings, Networking: Generate Domain. That's your HTTPS URL.

The Dockerfile builds the app with the Vu compiler from GitHub, for a CPU every cloud machine has,
and copies the binary (a few MB) into a small Debian image. It sets `PROXIES=1`: Railway's proxy
stands in front of the app, so the sign-in limit counts the client's address from
`X-Forwarded-For`, not the proxy's.

## 5. What you didn't have to get right

| | how |
|---|---|
| passwords | PBKDF2-SHA256, 600,000 iterations, Django's format (`std/auth`); hashing doesn't stall other requests |
| sessions | 32 random bytes; the database keeps only their SHA-256; cookies HttpOnly, Secure, SameSite=Lax |
| CSRF | tokens in forms (`vu new app`), and cross-site requests that change things refused (`web.same_origin`) |
| password guessing | 20 sign-ins a minute per client (`web.limit`) |
| SQL injection | SQL is text in the program; values only as parameters |
| XSS | templates escape every value |
| memory safety | Vu has no null pointers, no use-after-free, no data races between tasks |

## How it's tested

`tests/run_auth.sh` (accounts, both templates over HTTP, against Django's hashes),
`tests/run_jobs.sh` (jobs and migrations), `tests/run_saas.sh` (the example, against fake Stripe and
Resend and moto's S3), `tests/run_stripe.sh`, `tests/run_s3.sh`, `tests/run_mail.sh`, all against
a real PostgreSQL where they need one.
