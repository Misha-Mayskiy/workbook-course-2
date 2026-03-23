#include <iostream>
#include <fstream>
#include <string>
#include <vector>

void printErrorAndExit(bool isStdinMode)
{
    std::cout << "ERROR\n";
    exit(isStdinMode ? 0 : 1);
}

std::string replaceString(const std::string &subject, const std::string &search, const std::string &replace)
{
    if (search.empty())
        return subject;
    std::string result;
    size_t pos = 0, lastPos = 0;
    while ((pos = subject.find(search, lastPos)) != std::string::npos)
    {
        result += subject.substr(lastPos, pos - lastPos);
        result += replace;
        lastPos = pos + search.length();
    }
    result += subject.substr(lastPos);
    return result;
}

int main(int argc, char *argv[])
{
    bool isStdinMode = (argc == 1);

    if (argc == 2 && std::string(argv[1]) == "-h")
    {
        std::cout << "Usage: replace.exe <input file> <output file> <search string> <replace string>\n";
        std::cout << "Or run without arguments to use stdin/stdout.\n";
        return 0;
    }

    std::string search_str, replace_str;

    if (isStdinMode)
    {
        if (!std::getline(std::cin, search_str))
            printErrorAndExit(true);
        if (!std::getline(std::cin, replace_str))
            printErrorAndExit(true);

        std::string line;
        while (std::getline(std::cin, line))
        {
            std::cout << replaceString(line, search_str, replace_str) << "\n";
        }
    }
    else
    {
        if (argc != 5)
            printErrorAndExit(false);
        std::string input_file = argv[1];
        std::string output_file = argv[2];
        search_str = argv[3];
        replace_str = argv[4];

        std::ifstream in(input_file);
        if (!in.is_open())
            printErrorAndExit(false);

        std::ofstream out(output_file);
        if (!out.is_open())
            printErrorAndExit(false);

        std::string line;
        while (std::getline(in, line))
        {
            out << replaceString(line, search_str, replace_str) << "\n";
        }
    }

    return 0;
}