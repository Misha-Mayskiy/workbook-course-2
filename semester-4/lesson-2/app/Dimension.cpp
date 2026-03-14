#include "Dimension.h"
#include <iostream>

using namespace std;

Dimension::Dimension(int m, int l, int t, int i) : m(m), l(l), t(t), i(i) {}

bool Dimension::operator==(const Dimension &other) const
{
    return m == other.m && l == other.l && t == other.t && i == other.i;
}

bool Dimension::operator!=(const Dimension &other) const
{
    return !(*this == other);
}

Dimension Dimension::operator*(const Dimension &other) const
{
    return Dimension(m + other.m, l + other.l, t + other.t, i + other.i);
}

Dimension Dimension::operator/(const Dimension &other) const
{
    return Dimension(m - other.m, l - other.l, t - other.t, i - other.i);
}

void Dimension::print() const
{
    cout << "M^" << m << " L^" << l << " T^" << t;
    if (i != 0)
        cout << " I^" << i;
}