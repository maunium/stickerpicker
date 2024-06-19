FROM golang:1-alpine AS builder

RUN apk add --no-cache ca-certificates
WORKDIR /build/giphyproxy
COPY . /build/giphyproxy
ENV CGO_ENABLED=0
RUN go build -o /usr/bin/giphyproxy

FROM scratch

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/bin/giphyproxy /usr/bin/giphyproxy

VOLUME /data
WORKDIR /data
CMD ["/usr/bin/giphyproxy"]
