#pragma once
#include "Dimension.h"
#include "Unit.h"

class Quantity
{
private:
    double valueSI;
    Dimension dim;

public:
    Quantity(double valueSI, Dimension dim);
    Quantity(double userValue, const Unit &unit);

    Quantity operator+(const Quantity &other) const;
    Quantity operator-(const Quantity &other) const;
    Quantity operator*(const Quantity &other) const;
    Quantity operator/(const Quantity &other) const;

    void print() const;
    void printIn(const Unit &unit) const;
};