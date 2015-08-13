#include <stdio.h>
#include <stdlib.h>

#include "messages.h"
#include "uv.h"

uv_loop_t* loop = NULL;

void alloc_buffer(uv_handle_t* handle, size_t size, uv_buf_t* buf);
void connect_cb(uv_stream_t * server, int status);
void read_cb(uv_stream_t * stream, ssize_t nread, const uv_buf_t* buf);
void write_cb(uv_write_t* req, int status);
void close_cb(uv_handle_t* handle);

int main() {
    loop = uv_default_loop();

    uv_tcp_t server;

    uv_tcp_init(loop, &server);
    
    struct sockaddr_in addr;
    uv_ip4_addr("127.0.0.1", 3000, &addr);
    uv_tcp_bind(&server, (sockaddr*)&addr, 0);
    
    if (int r = uv_listen((uv_stream_t *)&server, 128, connect_cb)) {
        fprintf(stderr, "error: %s\n", uv_strerror(r));
        return r;
    }

    printf("listening...\n");

    return uv_run(loop, UV_RUN_DEFAULT);
}

void connect_cb(uv_stream_t* server, int status) {
    if (status < 0) {
        fprintf(stderr, "error: %s\n", uv_strerror(status));
        return;
    }

    uv_tcp_t* client = (uv_tcp_t*)malloc(sizeof(uv_tcp_t));
    uv_tcp_init(loop, client);

    if (int r = uv_accept(server, (uv_stream_t*)client)) {
        fprintf(stderr, "error: %s\n", uv_strerror(r));
        uv_close((uv_handle_t*)client, close_cb);
        return;
    }

    if (int r = uv_read_start((uv_stream_t*)client, alloc_buffer, read_cb)) {
        fprintf(stderr, "error: %s\n", uv_strerror(r));
        uv_close((uv_handle_t*)client, close_cb);
    }
    
    printf("established connection\n");
}

void read_cb(uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {    
    if (nread < 0) {
        if (nread != UV_EOF) {
            fprintf(stderr, "error: %s\n", uv_strerror(nread));
        }
        uv_close((uv_handle_t*)stream, close_cb);
    } else {
        uv_write_t* req = (uv_write_t*)malloc(sizeof(uv_write_t));
        if (int r = uv_write(req, stream, buf, 1, write_cb)) {
            fprintf(stderr, "error: %s\n", uv_strerror(r));
            uv_close((uv_handle_t*)stream, close_cb);
        }
    }

    free(buf->base);
}

void write_cb(uv_write_t* req, int status) {
    free(req);
    if (status < 0) {
        fprintf(stderr, "error: %s\n", uv_strerror(status));
    }
}

void close_cb(uv_handle_t* handle) {
    free((uv_tcp_t*)handle);
}

void alloc_buffer(uv_handle_t* handle, size_t size, uv_buf_t* buf) {
    buf->base = (char*)malloc(size);
    buf->len = size;
}