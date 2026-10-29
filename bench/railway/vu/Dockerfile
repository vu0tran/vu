# The Vu app: the binary is built by the workflow (vu build, on Ubuntu 24.04) and copied in.
FROM ubuntu:24.04
COPY shortener /app/shortener
ENV PORT=8080
CMD ["/app/shortener"]
