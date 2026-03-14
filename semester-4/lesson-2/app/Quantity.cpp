#include "Quantity.h"
#include <iostream>
#include <stdexcept>
#include <cmath>

using namespace std;

// Конструкторы
Quantity::Quantity(double valueSI, Dimension dim) : valueSI(valueSI), dim(dim) {}

Quantity::Quantity(double userValue, const Unit &unit)
    : valueSI(userValue * unit.getFactor()), dim(unit.getDimension()) {}

// Операторы
Quantity Quantity::operator+(const Quantity &other) const
{
    if (dim != other.dim)
        throw runtime_error("Нельзя складывать величины разных размерностей!");
    return Quantity(valueSI + other.valueSI, dim);
}

Quantity Quantity::operator-(const Quantity &other) const
{
    if (dim != other.dim)
        throw runtime_error("Нельзя вычитать величины разных размерностей!");
    return Quantity(valueSI - other.valueSI, dim);
}

Quantity Quantity::operator*(const Quantity &other) const
{
    return Quantity(valueSI * other.valueSI, dim * other.dim);
}

Quantity Quantity::operator/(const Quantity &other) const
{
    if (abs(other.valueSI) < 1e-9)
        throw runtime_error("Деление на ноль!");
    return Quantity(valueSI / other.valueSI, dim / other.dim);
}

// Вывод
void Quantity::print() const
{
    cout << valueSI << " [";
    dim.print();
    cout << "]";
}

void Quantity::printIn(const Unit &unit) const
{
    if (dim != unit.getDimension())
    {
        throw runtime_error("Нельзя вывести величину в несовместимой единице!");
    }
    cout << (valueSI / unit.getFactor()) << " " << unit.getName();
}