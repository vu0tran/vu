# Runs the benchmark once, inside Railway's private network, and prints the results to its log.
FROM ubuntu:24.04
RUN apt-get update -q && apt-get install -y -q --no-install-recommends wrk curl python3 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY mix.lua run.sh /bench/
CMD ["/bin/bash", "/bench/run.sh"]
