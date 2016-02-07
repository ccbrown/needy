#include <stdio.h>
#include <stdlib.h>

#include <random>

#include "messages.hpp"
#include "uv.h"

namespace {

void AssignRandom(GameState* game) {
    constexpr auto player = GameState::Player::One;
    auto seed = std::chrono::system_clock::now().time_since_epoch().count();
    std::mt19937 rng{static_cast<unsigned int>(seed)};
    std::uniform_int_distribution<int> distribution{0, 2};
    while (true) {
        int x = distribution(rng);
        int y = distribution(rng);
        if (game->owner(x, y) == GameState::Player::None) {
            game->assign(x, y, player);
            return;
        }
    }
}

void AllocBuffer(uv_handle_t* handle, size_t size, uv_buf_t* buf) {
    buf->base = reinterpret_cast<char*>(malloc(size));
    buf->len = size;
}

void CloseCallback(uv_handle_t* handle) {
    printf("connection closed\n");
    delete reinterpret_cast<uv_tcp_t*>(handle);
}

void ReadCallback(uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {    
    bool shouldCloseConnection = false;

    if (nread < 0) {
        if (nread != UV_EOF) {
            fprintf(stderr, "error: %s\n", uv_strerror(nread));
        }
        shouldCloseConnection = true;
    }    

    auto data = buf->base;
    size_t remaining = nread;

    while (remaining && !shouldCloseConnection) {
        if (remaining < sizeof(MessageType) + sizeof(MessageLength)) {
            fprintf(stderr, "error: %s\n", "incomplete message prefix");
            break;
        }

        auto type = *reinterpret_cast<MessageType*>(data);
        data += sizeof(MessageType);
        remaining -= sizeof(MessageType);

        size_t length = ntohs(*reinterpret_cast<MessageLength*>(data));
        data += sizeof(MessageLength);
        remaining -= sizeof(MessageLength);

        if (remaining < length) {
            fprintf(stderr, "error: %s\n", "incomplete message");
            break;
        }

        switch (type) {
            case MessageType::GameState: {
                if (length != sizeof(GameState)) {
                    fprintf(stderr, "error: %s\n", "malformed gamestate message");
                    shouldCloseConnection = true;
                    break;
                }

                auto game = reinterpret_cast<GameState*>(data);
                if (game->isOver()) {
                    shouldCloseConnection = true;
                    break;
                }
                
                constexpr auto self = GameState::Player::One;
                AssignRandom(game);
                
                if (false
                    || (game->winner() == self && !String{"You lose!"}.message(stream))
                    || !game->message(stream)
                    || game->winner() != GameState::Player::None
                ) {
                    shouldCloseConnection = true;
                }

                break;
            }
            default:
                fprintf(stderr, "error: %s\n", "unknown message type");
                shouldCloseConnection = true;
        }

        data += length;
        remaining -= length;
    }

    if (shouldCloseConnection) {
        uv_close(reinterpret_cast<uv_handle_t*>(stream), CloseCallback);
    }
    if (buf) {
        free(buf->base);
    }
}

void ConnectCallback(uv_stream_t* stream, int status) {
    if (status < 0) {
        fprintf(stderr, "error: %s\n", uv_strerror(status));
        return;
    }

    auto client = new uv_tcp_t();
    uv_tcp_init(uv_default_loop(), client);

    auto clientStream = reinterpret_cast<uv_stream_t*>(client);

    if (auto r = uv_accept(stream, clientStream)) {
        fprintf(stderr, "error: %s\n", uv_strerror(r));
        uv_close(reinterpret_cast<uv_handle_t*>(client), CloseCallback);
        return;
    }

    printf("connection established\n");

    if (auto r = uv_read_start(clientStream, AllocBuffer, ReadCallback)) {
        fprintf(stderr, "error: %s\n", uv_strerror(r));
        uv_close(reinterpret_cast<uv_handle_t*>(client), CloseCallback);
        return;
    }
    
    String string{"Go easy on me, okay?"};
    
    GameState game;
    AssignRandom(&game);

    if (!string.message(clientStream) || !game.message(clientStream)) {
        uv_close(reinterpret_cast<uv_handle_t*>(client), CloseCallback);
    }
}

} // namespace

int main(int argc, const char* argv[]) {
    auto port = argc > 1 ? atoi(argv[1]) : 3000;
    
    uv_tcp_t socket;
    uv_tcp_init(uv_default_loop(), &socket);
    
    sockaddr_in addr;
    uv_ip4_addr("127.0.0.1", port, &addr);
    uv_tcp_bind(&socket, (sockaddr*)&addr, 0);
    
    if (auto r = uv_listen((uv_stream_t*)&socket, 128, ConnectCallback)) {
        fprintf(stderr, "error: %s\n", uv_strerror(r));
        return r;
    }

    printf("listening on port %d...\n", port);

    return uv_run(uv_default_loop(), UV_RUN_DEFAULT);
}
