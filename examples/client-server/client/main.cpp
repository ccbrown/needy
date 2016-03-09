#include <stdio.h>
#include <stdlib.h>

#include <iostream>

#include "messages.hpp"
#include "uv.h"

namespace {

void AllocBuffer(uv_handle_t* handle, size_t size, uv_buf_t* buf) {
    buf->base = reinterpret_cast<char*>(malloc(size));
    buf->len = size;
}

void CloseCallback(uv_handle_t* handle) {
    printf("\nconnection closed\n");
}

char PlayerCharacter(GameState::Player player, char none = ' ') {
    switch (player) {
        case GameState::Player::None:
            return none;
        case GameState::Player::One:
            return 'X';
        case GameState::Player::Two:
            return 'O';
    }
    return '?';
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
            case MessageType::String:
                printf("%.*s\n", static_cast<int>(length), data);
                break;
            case MessageType::GameState: {
                if (length != sizeof(GameState)) {
                    fprintf(stderr, "error: %s\n", "malformed gamestate message");
                    shouldCloseConnection = true;
                    break;
                }

                auto game = reinterpret_cast<GameState*>(data);
                constexpr auto opponent = GameState::Player::One;
                constexpr auto self = GameState::Player::Two;
                
                while (true) {
                    printf("\n");
                    printf("     %c | %c | %c \n", PlayerCharacter(game->owner(0, 0), '1'), PlayerCharacter(game->owner(1, 0), '2'), PlayerCharacter(game->owner(2, 0), '3'));
                    printf("    ---+---+---\n");
                    printf("     %c | %c | %c \n", PlayerCharacter(game->owner(0, 1), '4'), PlayerCharacter(game->owner(1, 1), '5'), PlayerCharacter(game->owner(2, 1), '6'));
                    printf("    ---+---+---\n");
                    printf("     %c | %c | %c \n", PlayerCharacter(game->owner(0, 2), '7'), PlayerCharacter(game->owner(1, 2), '8'), PlayerCharacter(game->owner(2, 2), '9'));
                    
                    if (game->isOver()) {
                        shouldCloseConnection = true;
                        break;
                    }
                    
                    printf("\nPick a square: ");
                    std::string input;
                    std::cin >> input;
                    int square = atoi(input.c_str());
                    if (square < 1 || square > 9) {
                        printf("The squares are numbered 1 through 9.\n");
                        continue;
                    }
                    int x = (square - 1) % 3;
                    int y = (square - 1) / 3;
                    if (game->owner(x, y) != GameState::Player::None) {
                        printf("That square is occupied.\n");
                        continue;
                    }
                    game->assign(x, y, self);
                    if (game->winner() == self) {
                        printf("Congratulations! You're a winner!\n");
                        shouldCloseConnection = true;
                    } else if (!game->message(stream)) {
                        shouldCloseConnection = true;
                    }
                    break;
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

void ConnectCallback(uv_connect_t* connection, int status) {
    if (status < 0) {
        fprintf(stderr, "error: %s\n", uv_strerror(status));
        return;
    }

    if (auto r = uv_read_start(connection->handle, AllocBuffer, ReadCallback)) {
        fprintf(stderr, "error: %s\n", uv_strerror(r));
        uv_close(reinterpret_cast<uv_handle_t*>(connection->handle), CloseCallback);
        return;
    }

    printf("connection established\n\n");
}

} // namespace

int main(int argc, const char* argv[]) {
    auto ip   = argc > 1 ? argv[1] : "127.0.0.1";
    auto port = argc > 2 ? atoi(argv[2]) : 3000;
    
    printf("connecting to %s on port %d...\n", ip, port);

    uv_tcp_t socket;
    uv_tcp_init(uv_default_loop(), &socket);
    
    sockaddr_in addr;
    uv_ip4_addr(ip, port, &addr);
    
    uv_connect_t connection;
    uv_tcp_connect(&connection, &socket, reinterpret_cast<sockaddr*>(&addr), ConnectCallback);

    return uv_run(uv_default_loop(), UV_RUN_DEFAULT);
}
