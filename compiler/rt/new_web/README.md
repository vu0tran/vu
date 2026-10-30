# @@NAME@@

A web app in [Vu](https://github.com/vu0tran/vu), made by `vu new web @@NAME@@`. (`vu` is the script at the
top of the Vu repository.)

```
vu run main.vu                  # http://localhost:8080 (PORT=3000 vu run main.vu for another port)
vu check main.vu                # every compile error, in milliseconds
vu build main.vu -o app         # the optimized binary: copy it and public/ anywhere and run ./app
```

- `main.vu`: the routes and handlers (see "web" in Vu's SPEC.md).
- `public/`: files served at `/static/...` (hidden files and anything outside the folder are 404).

## Deploy

With Docker (any host that runs containers):

```
docker build -t @@NAME@@ .
docker run -p 8080:8080 @@NAME@@
```

On [Railway](https://railway.com): push this folder to a GitHub repository and create a project from it
(or, with the CLI, `railway init` and `railway up` here). `railway.json` tells it to build the Dockerfile
and check `/health`; it gives the app a `PORT` and, under Settings, a domain with HTTPS.

On [Fly.io](https://fly.io), after `fly auth login`:

```
fly launch --copy-config --no-deploy   # once: creates the app (rename it if the name is taken)
fly deploy                             # builds the Dockerfile and starts it, with HTTPS
```

Without containers: `vu build main.vu -o app` needs the server to have OpenSSL 3 (`libssl3`); `vu build
main.vu -o app --static` links everything in, so it runs on any Linux with the same CPU type (with
glibc, looking up host names then needs glibc's own libraries there: fine for a server that only
listens). Copy `app` and `public/` to the server and run `./app` behind a reverse proxy that does HTTPS.
