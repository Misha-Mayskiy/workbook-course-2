#include <iostream>
#include <string>
#include <map>
#include <cstdlib>
#include "Quantity.h"
#include "Parser.h"

using namespace std;

int main()
{
    system("chcp 65001 > nul");

    // Создаем словарь единиц
    map<string, Unit> dict;
    Dimension d_mass(1, 0, 0, 0), d_len(0, 1, 0, 0), d_time(0, 0, 1, 0);

    dict["m"] = Unit("m", 1.0, d_len);
    dict["cm"] = Unit("cm", 0.01, d_len);
    dict["kg"] = Unit("kg", 1.0, d_mass);
    dict["g"] = Unit("g", 0.001, d_mass);
    dict["s"] = Unit("s", 1.0, d_time);
    dict["N"] = Unit("N", 1.0, Dimension(1, 1, -2, 0));

    Parser parser(dict);
    string formula;

    cout << "=== ФИЗИЧЕСКИЙ КАЛЬКУЛЯТОР ===" << endl;
    cout << "Введите формулу (например: 5kg * 2m/s/s) или 'exit':" << endl;

    while (true)
    {
        cout << "> ";
        if (!getline(cin, formula) || formula == "exit")
            break;
        if (formula.empty())
            continue;

        try
        {
            Quantity result = parser.calculate(formula);
            cout << "Результат в СИ: ";
            result.print();
            cout << endl;
        }
        catch (const exception &e)
        {
            cout << "Ошибка: " << e.what() << endl;
        }
    }

    return 0;
}