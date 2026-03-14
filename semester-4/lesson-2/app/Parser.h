#pragma once
#include <string>
#include <map>
#include "Quantity.h"

class Parser
{
private:
    std::string input;
    size_t pos;
    std::map<std::string, Unit> units; // Словарь известных единиц

    char peek();
    char get();
    Quantity parseExpression(); // Сложение и вычитание
    Quantity parseTerm();       // Умножение и деление
    Quantity parseFactor();     // Числа, скобки и единицы
    void skipWhitespace();

public:
    Parser(const std::map<std::string, Unit> &unitDict);
    Quantity calculate(std::string str);
};