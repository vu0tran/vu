# Builds the app with the Vu compiler, then copies the binary into a small image.
#   docker build -t @@NAME@@ . && docker run -p 8080:8080 -e DATABASE_URL=... @@NAME@@
FROM gcc:14 AS build
ARG VU_REF=main
RUN git clone --depth 1 --branch "$VU_REF" https://github.com/vu0tran/vu /vu && /vu/vu check /vu/examples/json.vu
WORKDIR /app
COPY . .
# optimize for a CPU every cloud machine has, not the one that builds the image
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then march=armv8.2-a; else march=x86-64-v2; fi && \
    VU_MARCH=$march /vu/vu build main.vu -o app

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates libssl3 && rm -rf /var/lib/apt/lists/* && \
    useradd --system --no-create-home app
WORKDIR /app
COPY --from=build /app/app ./app
USER app
ENV PORT=8080
# behind one proxy (the platform's), which adds the client's address to X-Forwarded-For
ENV PROXIES=1
EXPOSE 8080
CMD ["./app"]
