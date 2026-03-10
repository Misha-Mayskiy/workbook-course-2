#include <iostream>
using namespace std;

class Inventory
{
private:
    int *data;
    int size;
    int capacity;

public:
    // Базовый конструктор
    Inventory(int cap = 5)
    {
        this->capacity = cap;
        this->size = 0;
        this->data = new int[this->capacity];
    }

    // Конструктор копирования
    Inventory(const Inventory &other)
    {
        this->size = other.size;
        this->capacity = other.capacity;
        this->data = new int[this->capacity];

        for (int i = 0; i < this->size; i++)
        {
            this->data[i] = other.data[i];
        }
    }

    // Деструктор
    ~Inventory()
    {
        delete[] data;
    }

    void print() const
    {
        cout << "[ ";
        for (int i = 0; i < size; i++)
        {
            cout << data[i] << " ";
        }
        cout << "]" << endl;
    }

    // Метод добавления
    void add(int itemID)
    {
        if (size < capacity)
        {
            data[size] = itemID;
            size++;
        }
        else if (size == capacity)
        {
            int *newData = new int[capacity * 2];

            // 2. ИСПРАВЛЕНИЕ: добавили int i, убрали len(data) и заменили на size
            for (int i = 0; i < size; i++)
            {
                newData[i] = data[i];
            }

            delete[] data;
            data = newData;
            capacity *= 2;
            data[size] = itemID;
            size++;
        }
    }

    // Оператор присваивания
    Inventory &operator=(const Inventory &other)
    {
        if (this == &other)
        {
            return *this;
        }

        delete[] this->data;

        this->size = other.size;
        this->capacity = other.capacity;
        this->data = new int[this->capacity];

        for (int i = 0; i < this->size; i++)
        {
            this->data[i] = other.data[i];
        }

        return *this;
    }
};

int main()
{
    Inventory arthur(2);
    arthur.add(10); // Золото
    arthur.add(20); // Зелье
    arthur.add(30); // Меч (тут массив расширится)

    std::cout << "Arthur's inventory: ";
    arthur.print();

    // Тест конструктора копирования
    Inventory lancelot = arthur;
    lancelot.add(99); // Даем Ланселоту уникальный предмет

    std::cout << "Lancelot's inventory: ";
    lancelot.print();

    Inventory merlin(10);
    merlin.add(777); // Посох

    // Тест оператора присваивания
    merlin = arthur;

    std::cout << "Merlin's inventory (copied from Arthur): ";
    merlin.print();

    // Проверка независимости:
    std::cout << "Original Arthur remains unchanged: ";
    arthur.print();

    std::cout << "Success! No crashes!" << std::endl;
    return 0;
}