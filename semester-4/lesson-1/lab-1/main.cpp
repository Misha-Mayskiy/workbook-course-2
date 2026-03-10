#include <iostream>
using namespace std;

class Vector2D
{
private: // По заданию переменные приватные
    float x, y;

public:
    // Конструктор
    Vector2D(float x_val = 0, float y_val = 0)
    {
        x = x_val;
        y = y_val;
    }

    // Шаг 1: Метод print
    void print()
    {
        cout << "(" << this->x << ", " << this->y << ")" << endl;
    }

    // Шаг 2: Сложение и вычитание
    Vector2D operator+(const Vector2D &other) const
    {
        return Vector2D(this->x + other.x, this->y + other.y);
    }

    Vector2D operator-(const Vector2D &other) const
    {
        return Vector2D(this->x - other.x, this->y - other.y);
    }

    // Шаг 3: Умножение на число
    Vector2D operator*(float scalar) const
    {
        return Vector2D(this->x * scalar, this->y * scalar);
    }

    // Шаг 4: Сравнение
    bool operator==(const Vector2D &other) const
    {
        return (this->x == other.x) && (this->y == other.y);
    }

    bool operator!=(const Vector2D &other) const
    {
        return !(*this == other);
    }

    // Шаг 5: Вывод в консоль
    friend std::ostream &operator<<(std::ostream &os, const Vector2D &v)
    {
        os << "(" << v.x << ", " << v.y << ")";
        return os;
    }
};

int main()
{
    Vector2D playerPos(10.0, 5.0);
    Vector2D velocity(2.5, -1.0);
    float time = 2.0;

    Vector2D newPos = playerPos + (velocity * time);

    cout << "Start position: " << playerPos << endl;
    cout << "Velocity: " << velocity << endl;
    cout << "Position after 2 seconds: " << newPos << endl;

    Vector2D target(15.0, 3.0);
    if (newPos == target)
    {
        cout << "Target reached!" << endl;
    }
    else
    {
        cout << "Missed the target." << endl;
    }

    return 0;
}