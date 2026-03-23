#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <queue>

void printErrorAndExit(bool isStdinMode)
{
    std::cout << "ERROR\n";
    exit(isStdinMode ? 0 : 1);
}

int main(int argc, char *argv[])
{
    bool isStdinMode = (argc == 1);

    if (argc == 2 && std::string(argv[1]) == "-h")
    {
        std::cout << "Usage: fill.exe <input file> <output file>\n";
        std::cout << "Or run without arguments to use stdin/stdout.\n";
        return 0;
    }

    if (!isStdinMode && argc != 3)
        printErrorAndExit(false);

    std::istream *in = &std::cin;
    std::ostream *out = &std::cout;
    std::ifstream fileIn;
    std::ofstream fileOut;

    if (!isStdinMode)
    {
        fileIn.open(argv[1]);
        if (!fileIn.is_open())
            printErrorAndExit(false);
        in = &fileIn;

        fileOut.open(argv[2]);
        if (!fileOut.is_open())
            printErrorAndExit(false);
        out = &fileOut;
    }

    std::vector<std::string> grid(100, std::string(100, ' '));
    std::string line;
    int rowCount = 0;

    while (std::getline(*in, line) && rowCount < 100)
    {
        for (int i = 0; i < line.length() && i < 100; ++i)
        {
            grid[rowCount][i] = line[i];
        }
        rowCount++;
    }

    std::queue<std::pair<int, int>> q;

    for (int r = 0; r < 100; ++r)
    {
        for (int c = 0; c < 100; ++c)
        {
            if (grid[r][c] == 'O')
            {
                grid[r][c] = '.';
                q.push({r, c});
            }
        }
    }

    int dr[] = {-1, 1, 0, 0};
    int dc[] = {0, 0, -1, 1};

    while (!q.empty())
    {
        auto [r, c] = q.front();
        q.pop();

        for (int i = 0; i < 4; ++i)
        {
            int nr = r + dr[i];
            int nc = c + dc[i];

            if (nr >= 0 && nr < 100 && nc >= 0 && nc < 100)
            {
                if (grid[nr][nc] == ' ' || grid[nr][nc] == 'O')
                {
                    grid[nr][nc] = '.';
                    q.push({nr, nc});
                }
            }
        }
    }

    int max_r = -1;
    for (int i = 0; i < 100; ++i)
    {
        bool hasChar = false;
        for (int j = 0; j < 100; ++j)
        {
            if (grid[i][j] != ' ')
                hasChar = true;
        }
        if (hasChar || i < rowCount)
            max_r = i; // Сохраняем исходные границы + выливание
    }

    for (int i = 0; i <= max_r; ++i)
    {
        int last_char = -1;
        for (int j = 0; j < 100; ++j)
        {
            if (grid[i][j] != ' ')
                last_char = j;
        }
        if (last_char == -1)
            *out << "\n";
        else
            *out << grid[i].substr(0, last_char + 1) << "\n";
    }

    return 0;
}