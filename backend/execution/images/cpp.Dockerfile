# C++ runner for student code. Only a compiler: no shell tools beyond
# BusyBox, no network clients, nothing from the host.
FROM alpine:3.20
RUN apk add --no-cache g++
