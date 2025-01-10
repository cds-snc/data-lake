ARG BASE_IMAGE="python:3.13.1-alpine3.21@sha256:b6f01a01e34091438a29b6dda4664199e34731fb2581ebb6fe255a2ebf441099"
FROM ${BASE_IMAGE} as builder

RUN apk add --no-cache \
    autoconf \
    automake \
    build-base \
    gcc \
    libc-dev \
    libcurl \
    libstdc++ \
    libtool \
    make \
    cmake \
    python3-dev

COPY ./requirements.txt /
RUN mkdir -p /pymodules \
    && pip install -r /requirements.txt --target /pymodules

# Lambda API image
FROM ${BASE_IMAGE} as lambda

COPY --from=builder /pymodules /pymodules

# Build variables
ARG FUNCTION_DIR="/function"
ARG GIT_SHA
ENV GIT_SHA=$GIT_SHA
ENV PYTHONPATH="/pymodules"

RUN apk upgrade --no-cache \
    && apk add --no-cache \
    binutils \
    libstdc++

# Copy function code
WORKDIR ${FUNCTION_DIR}
COPY main.py ${FUNCTION_DIR}

ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric", "main.handler" ]
