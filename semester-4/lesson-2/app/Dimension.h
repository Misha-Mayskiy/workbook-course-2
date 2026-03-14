#pragma once

class Dimension
{
private:
    int m, l, t, i;

public:
    // Конструктор
    Dimension(int m = 0, int l = 0, int t = 0, int i = 0);

    // Операторы
    bool operator==(const Dimension &other) const;
    bool operator!=(const Dimension &other) const;
    Dimension operator*(const Dimension &other) const;
    Dimension operator/(const Dimension &other) const;

    // Вывод
    void print() const;
};