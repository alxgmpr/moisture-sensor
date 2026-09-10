FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends openems octave-openems python3 python3-numpy python3-scipy python3-matplotlib && rm -rf /var/lib/apt/lists/*
WORKDIR /work
