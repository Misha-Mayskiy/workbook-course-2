#include <QMainWindow>
#include <QLineEdit>
#include <QPushButton>
#include <QLabel>
#include <QVBoxLayout>
#include "Parser.h"

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    MainWindow(QWidget *parent = nullptr) : QMainWindow(parent)
    {
        // Настройка словаря единиц
        std::map<std::string, Unit> dict;
        dict["m"] = Unit("m", 1.0, Dimension(0, 1, 0, 0));
        dict["kg"] = Unit("kg", 1.0, Dimension(1, 0, 0, 0));
        dict["s"] = Unit("s", 1.0, Dimension(0, 0, 1, 0));
        // ... добавить остальные ...

        parser = new Parser(dict);

        // UI элементы
        inputField = new QLineEdit();
        inputField->setPlaceholderText("Введите формулу, например: (10kg * 5m) / 2s");
        calcButton = new QPushButton("Рассчитать");
        resultLabel = new QLabel("Результат появится здесь");

        auto *layout = new QVBoxLayout();
        layout->addWidget(inputField);
        layout->addWidget(calcButton);
        layout->addWidget(resultLabel);

        auto *central = new QWidget();
        central->setLayout(layout);
        setCentralWidget(central);

        connect(calcButton, &QPushButton::clicked, this, &MainWindow::onCalculate);
    }

private slots:
    void onCalculate()
    {
        try
        {
            Quantity res = parser->calculate(inputField->text().toStdString());
            // Нам нужно добавить метод в Quantity, который возвращает строку для вывода
            resultLabel->setText(QString::fromStdString("Успех!"));
            // Тут можно вывести res.print() в строку
        }
        catch (const std::exception &e)
        {
            resultLabel->setText(QString("Ошибка: ") + e.what());
        }
    }

private:
    Parser *parser;
    QLineEdit *inputField;
    QPushButton *calcButton;
    QLabel *resultLabel;
};