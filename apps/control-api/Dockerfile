# MeshMind v2 - Control API
# Build from repo root: docker build -f apps/control-api/Dockerfile .
FROM rust:1-bookworm AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock* ./
COPY apps/control-api ./apps/control-api

RUN cargo build -p meshmind-control-api --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/meshmind-control-api /usr/local/bin/
EXPOSE 3000
CMD ["meshmind-control-api"]
