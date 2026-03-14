#include "Parser.h"
#include <stdexcept>
#include <cctype>

Parser::Parser(const std::map<std::string, Unit> &unitDict) : units(unitDict), pos(0) {}

char Parser::peek() { return pos < input.size() ? input[pos] : 0; }
char Parser::get() { return pos < input.size() ? input[pos++] : 0; }
void Parser::skipWhitespace()
{
    while (isspace(peek()))
        pos++;
}

Quantity Parser::calculate(std::string str)
{
    input = str;
    pos = 0;
    return parseExpression();
}

Quantity Parser::parseExpression()
{
    Quantity result = parseTerm();
    skipWhitespace();
    while (peek() == '+' || peek() == '-')
    {
        char op = get();
        Quantity nextTerm = parseTerm();
        if (op == '+')
            result = result + nextTerm;
        else
            result = result - nextTerm;
        skipWhitespace();
    }
    return result;
}

Quantity Parser::parseTerm()
{
    Quantity result = parseFactor();
    skipWhitespace();
    while (peek() == '*' || peek() == '/')
    {
        char op = get();
        Quantity nextFactor = parseFactor();
        if (op == '*')
            result = result * nextFactor;
        else
            result = result / nextFactor;
        skipWhitespace();
    }
    return result;
}

Quantity Parser::parseFactor()
{
    skipWhitespace();

    // 1. Обработка скобок
    if (peek() == '(')
    {
        get();
        Quantity result = parseExpression();
        skipWhitespace();
        if (get() != ')')
            throw std::runtime_error("Пропущена )");
        return result;
    }

    // 2. Читаем число
    std::string numStr;
    while (isdigit(peek()) || peek() == '.')
        numStr += get();
    double val = (numStr.empty()) ? 1.0 : std::stod(numStr);

    // 3. Читаем сложную единицу (например: kg*m/s^2)
    skipWhitespace();
    std::string unitPart;
    while (isalnum(peek()) || peek() == '*' || peek() == '/' || peek() == '^' || peek() == '-')
    {
        unitPart += get();
    }

    if (unitPart.empty())
    {
        return Quantity(val, Dimension(0, 0, 0, 0)); // Просто число
    }

    // Здесь должна быть логика разбора unitPart (например, "m/s^2")
    // Для лабы проще всего искать готовые сочетания в словаре:
    if (units.count(unitPart))
    {
        return Quantity(val, units.at(unitPart));
    }
    else
    {
        // Если сложной единицы нет в словаре, можно выдать ошибку
        throw std::runtime_error("Неизвестная единица: " + unitPart);
    }
}