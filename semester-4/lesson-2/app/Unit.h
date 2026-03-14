#pragma once
#include <string>
#include "Dimension.h"

class Unit
{
private:
    std::string name;
    double factor;
    Dimension dim;

public:
    Unit() : name(""), factor(1.0), dim() {}
    Unit(std::string name, double factor, Dimension dim);

    std::string getName() const;
    double getFactor() const;
    Dimension getDimension() const;
};