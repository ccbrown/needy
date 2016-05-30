#include <fmt/format.h>

#include <iostream>

int main(int argc, const char* argv[]) {
    std::cout << fmt::format("{} {}!\n", "It", "worked");
    return 0;
}
