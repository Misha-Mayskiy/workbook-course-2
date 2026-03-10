#include <iostream>
#include <cstdlib>

using namespace std;

struct Player
{
    int x = 1;
    int y = 1;
    int hp = 100;
    int gold = 0;
};

class Cell
{
public:
    virtual char getSymbol() const = 0;
    virtual void onStep(Player &p) = 0;
    virtual bool canWalk() const { return true; }
    virtual ~Cell() {}
};

class Floor : public Cell
{
public:
    char getSymbol() const override { return '.'; }
    void onStep(Player &p) override {}
};

class Wall : public Cell
{
public:
    char getSymbol() const override { return '#'; }
    void onStep(Player &p) override {}
    bool canWalk() const override { return false; }
};

class Gold : public Cell
{
private:
    bool isCollected = false;

public:
    char getSymbol() const override
    {
        if (isCollected)
        {
            return '.';
        }
        else
        {
            return '$';
        }
    }
    void onStep(Player &p) override
    {
        if (!isCollected)
        {
            p.gold += 10;
            isCollected = true;
        }
    }
};

class Map
{
private:
    Cell *grid[10][10];

public:
    // Конструктор: заполняем карту
    Map()
    {
        for (int y = 0; y < 10; y++)
        {
            for (int x = 0; x < 10; x++)
            {
                // Если это края карты то ставим стены
                if (x == 0 || x == 9 || y == 0 || y == 9)
                {
                    grid[y][x] = new Wall();
                }
                // Иначе обычный Пол
                else
                {
                    grid[y][x] = new Floor();
                }
            }
        }
        // Кладем золота
        delete grid[5][5];
        grid[5][5] = new Gold();

        delete grid[2][8];
        grid[2][8] = new Gold();
    }

    ~Map()
    {
        for (int y = 0; y < 10; y++)
        {
            for (int x = 0; x < 10; x++)
            {
                delete grid[y][x];
            }
        }
    }

    // Отрисовка карты
    void draw(const Player &p) const
    {
        for (int y = 0; y < 10; y++)
        {
            for (int x = 0; x < 10; x++)
            {
                // Если координаты совпадают с игроком то рисуем его
                if (x == p.x && y == p.y)
                {
                    cout << '@';
                }
                // Иначе просим клетку саму вернуть свой символ
                else
                {
                    cout << grid[y][x]->getSymbol();
                }
            }
            cout << endl;
        }
    }

    // Логика движения
    void movePlayer(Player &p, int dx, int dy)
    {
        int nx = p.x + dx;
        int ny = p.y + dy;

        // Проверка
        if (nx >= 0 && nx < 10 && ny >= 0 && ny < 10)
        {
            if (grid[ny][nx]->canWalk())
            {
                p.x = nx;
                p.y = ny;
                grid[ny][nx]->onStep(p);
            }
        }
    }
};

int main()
{
    Player player;
    Map gameMap;
    char input;

    while (player.hp > 0)
    {
        system("cls");

        std::cout << "HP: " << player.hp << " | Gold: " << player.gold << "\n";
        gameMap.draw(player);
        std::cout << "Move (w/a/s/d) and press Enter: ";
        std::cin >> input;

        if (input == 'w')
            gameMap.movePlayer(player, 0, -1);
        if (input == 's')
            gameMap.movePlayer(player, 0, 1);
        if (input == 'a')
            gameMap.movePlayer(player, -1, 0);
        if (input == 'd')
            gameMap.movePlayer(player, 1, 0);
        if (input == 'q')
            break; // Выход
    }

    std::cout << "Game Over!\n";
    return 0;
}