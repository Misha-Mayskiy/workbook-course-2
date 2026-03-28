#include <iostream>
#include <string>
#include <cctype>

std::string RemoveExtraSpaces(std::string const &arg)
{
    std::string result;
    result.reserve(arg.size());

    bool in_space = false;
    for (char c : arg)
    {
        if (std::isspace(static_cast<unsigned char>(c)))
        {
            if (!result.empty() && !in_space)
            {
                result.push_back(' ');
                in_space = true;
            }
        }
        else
        {
            result.push_back(c);
            in_space = false;
        }
    }

    // Удаляем висячий пробел в конце, если он есть
    if (!result.empty() && result.back() == ' ')
    {
        result.pop_back();
    }

    return result;
}

int main()
{
    std::string line;
    while (std::getline(std::cin, line))
    {
        std::cout << RemoveExtraSpaces(line) << "\n";
    }
    return 0;
}