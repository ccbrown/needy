#include <string>

#include "uv.h"

enum class MessageType : uint8_t {
    String,
    GameState,
};

typedef uint16_t MessageLength;

namespace {
    void WriteCallback(uv_write_t* req, int status) {
        delete req;
        if (status < 0) {
            fprintf(stderr, "error: %s\n", uv_strerror(status));
        }
    }
}

struct String : std::string {
    using std::string::string;
    
    bool message(uv_stream_t* stream) {
        MessageType type = MessageType::String;
        MessageLength length = htons(size());
        uv_buf_t bufs[] = {
            {reinterpret_cast<char*>(&type), sizeof(type)},
            {reinterpret_cast<char*>(&length), sizeof(length)},
            {const_cast<char*>(data()), size()},
        };
        auto req = new uv_write_t();
        if (auto r = uv_write(req, stream, bufs, sizeof(bufs) / sizeof(*bufs), WriteCallback)) {
            fprintf(stderr, "error: %s\n", uv_strerror(r));
            return false;
        }
        return true;
    }
};

struct GameState {
    uint8_t rows[3]{0};

    enum class Player : uint8_t {
        None = 0, One = 1, Two = 2,
    };
    
    Player owner(int x, int y) {
        return static_cast<Player>((rows[y] >> (x << 1)) & 3);
    }

    void assign(int x, int y, Player player) {
        rows[y] |= static_cast<uint8_t>(player) << (x << 1);
    }
    
    bool isOver() {
        if (winner() != Player::None) {
            return true;
        }
        for (int x = 0; x < 3; ++x) {
            for (int y = 0; y < 3; ++y) {
                if (owner(x, y) == Player::None) {
                    return false;
                }
            }
        }
        return true;
    }
    
    Player winner() {
        for (int x = 0; x < 3; ++x) {
            auto p = owner(x, 0);
            if (p != Player::None && p == owner(x, 1) && p == owner(x, 2)) {
                return p;
            }
        }
        for (int y = 0; y < 3; ++y) {
            auto p = owner(0, y);
            if (p != Player::None && p == owner(1, y) && p == owner(2, y)) {
                return p;
            }
        }
        auto p = owner(1, 1);
        if (p != Player::None && ((p == owner(0, 0) && p == owner(2, 2)) || (p == owner(0, 2) && p == owner(2, 0)))) {
            return p;
        }
        return Player::None;
    }

    bool message(uv_stream_t* stream) {
        MessageType type = MessageType::GameState;
        MessageLength length = htons(sizeof(*this));
        uv_buf_t bufs[] = {
            {reinterpret_cast<char*>(&type), sizeof(type)},
            {reinterpret_cast<char*>(&length), sizeof(length)},
            {reinterpret_cast<char*>(this), sizeof(*this)},
        };
        auto req = new uv_write_t();
        if (auto r = uv_write(req, stream, bufs, sizeof(bufs) / sizeof(*bufs), WriteCallback)) {
            fprintf(stderr, "error: %s\n", uv_strerror(r));
            return false;
        }
        return true;
    }
};
