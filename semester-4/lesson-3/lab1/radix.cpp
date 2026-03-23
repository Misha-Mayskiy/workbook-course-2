#include <iostream>
#include <string>
#include <algorithm>
#include <climits>

int StringToInt(const std::string &str, int radix, bool &wasError)
{
    wasError = false;
    if (str.empty() || radix < 2 || radix > 36)
    {
        wasError = true;
        return 0;
    }

    bool isNegative = (str[0] == '-');
    size_t start = isNegative ? 1 : 0;
    if (start == str.length())
    {
        wasError = true;
        return 0;
    }

    long long result = 0; // Используем long long для безопасной проверки переполнения
    for (size_t i = start; i < str.length(); ++i)
    {
        char c = str[i];
        int digit = -1;
        if (c >= '0' && c <= '9')
            digit = c - '0';
        else if (c >= 'A' && c <= 'Z')
            digit = c - 'A' + 10;
        else if (c >= 'a' && c <= 'z')
            digit = c - 'a' + 10;

        if (digit == -1 || digit >= radix)
        {
            wasError = true;
            return 0;
        }

        result = result * radix + digit;

        if (isNegative && -result < INT_MIN)
        {
            wasError = true;
            return 0;
        }
        if (!isNegative && result > INT_MAX)
        {
            wasError = true;
            return 0;
        }
    }

    return static_cast<int>(isNegative ? -result : result);
}

std::string IntToString(int n, int radix, bool &wasError)
{
    wasError = false;
    if (radix < 2 || radix > 36)
    {
        wasError = true;
        return "";
    }
    if (n == 0)
        return "0";

    std::string result;
    bool isNegative = (n < 0);
    long long num = std::abs(static_cast<long long>(n)); // Защита от INT_MIN

    while (num > 0)
    {
        int digit = num % radix;
        if (digit < 10)
            result += static_cast<char>('0' + digit);
        else
            result += static_cast<char>('A' + (digit - 10));
        num /= radix;
    }

    if (isNegative)
        result += '-';
    std::reverse(result.begin(), result.end());
    return result;
}

int main(int argc, char *argv[])
{
    if (argc != 4)
    {
        std::cout << "Usage: radix.exe <source notation> <destination notation> <value>\n";
        return 1;
    }

    try
    {
        int srcRadix = std::stoi(argv[1]);
        int dstRadix = std::stoi(argv[2]);
        std::string value = argv[3];

        bool wasError = false;
        int intValue = StringToInt(value, srcRadix, wasError);

        if (wasError)
        {
            std::cout << "ERROR\n";
            return 1;
        }

        std::string result = IntToString(intValue, dstRadix, wasError);
        if (wasError)
        {
            std::cout << "ERROR\n";
            return 1;
        }

        std::cout << result << "\n";
    }
    catch (...)
    {
        std::cout << "ERROR\n";
        return 1;
    }

    return 0;
}