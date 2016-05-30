#include <boost/program_options.hpp>

#include <iostream>
#include <string>

namespace po = boost::program_options;

int main(int argc, const char* argv[]) {
    try {
        po::options_description desc("Allowed options");
        desc.add_options()
            ("help", "produce help message")
            ("name", po::value<std::string>()->required(), "your name")
        ;

        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);

        if (vm.count("help")) {
            std::cout << desc << "\n";
            return 1;
        }

        po::notify(vm);

        std::cout << "Hello, " << vm["name"].as<std::string>() << "!\n";
    } catch (std::exception& e) {
        std::cerr << e.what() << "\n";
        return 1;
    }

    return 0;
}
