#include <iostream>
#include <vector>
#include <numeric>
#include <algorithm>
#include <iomanip>

// Чтение чисел. При ошибке формата возвращает false.
bool ReadNumbers(std::vector<double> &numbers)
{
    double val;
    while (std::cin >> val)
    {
        numbers.push_back(val);
    }
    // Если чтение прервалось не из-за конца файла (EOF), значит встретился мусор (буквы)
    if (!std::cin.eof() && std::cin.fail())
    {
        return false;
    }
    return true;
}

// Обработка вектора по заданию (вычитание медианы)
void ProcessNumbers(std::vector<double> &numbers)
{
    if (numbers.empty())
        return;

    // Копируем вектор, так как nth_element меняет порядок элементов
    std::vector<double> temp = numbers;
    size_t n = temp.size();
    double median = 0.0;

    if (n % 2 != 0)
    {
        // Нечетное количество: медиана точно посередине
        std::nth_element(temp.begin(), temp.begin() + n / 2, temp.end());
        median = temp[n / 2];
    }
    else
    {
        // Четное количество: среднее двух центральных
        std::nth_element(temp.begin(), temp.begin() + n / 2, temp.end());
        std::nth_element(temp.begin(), temp.begin() + (n / 2 - 1), temp.begin() + n / 2);
        median = (temp[n / 2] + temp[n / 2 - 1]) / 2.0;
    }

    // std::transform для изменения каждого элемента (вычитаем медиану)
    std::transform(numbers.begin(), numbers.end(), numbers.begin(),
                   [median](double x)
                   { return x - median; });
}

// Вывод без изменения исходного вектора
void PrintSortedNumbers(std::vector<double> numbers)
{
    std::sort(numbers.begin(), numbers.end());
    std::cout << std::fixed << std::setprecision(3);
    for (size_t i = 0; i < numbers.size(); ++i)
    {
        std::cout << numbers[i] << (i == numbers.size() - 1 ? "" : " ");
    }
    std::cout << "\n";
}

int main()
{
    std::vector<double> numbers;
    if (!ReadNumbers(numbers))
    {
        std::cout << "ERROR\n";
        return 0; // Требование Яндекс.Контест
    }
    ProcessNumbers(numbers);
    PrintSortedNumbers(numbers);
    return 0;
}