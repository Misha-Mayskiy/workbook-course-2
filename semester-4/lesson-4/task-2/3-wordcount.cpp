#include <iostream>
#include <string>
#include <map>
#include <algorithm>
#include <cctype>

std::string ToLower(std::string str)
{
    std::transform(str.begin(), str.end(), str.begin(),
                   [](unsigned char c)
                   { return std::tolower(c); });
    return str;
}

int main()
{
    std::map<std::string, int> word_freq;
    std::string word;

    while (std::cin >> word)
    {
        word_freq[ToLower(word)]++;
    }

    for (const auto &[key, count] : word_freq)
    {
        std::cout << key << ": " << count << "\n";
    }

    return 0;
}