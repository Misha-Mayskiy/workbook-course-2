#include "Unit.h"

using namespace std;

Unit::Unit(string name, double factor, Dimension dim)
    : name(name), factor(factor), dim(dim) {}

string Unit::getName() const { return name; }
double Unit::getFactor() const { return factor; }
Dimension Unit::getDimension() const { return dim; }