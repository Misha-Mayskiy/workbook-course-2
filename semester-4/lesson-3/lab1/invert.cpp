#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <cmath>

using Matrix = std::vector<std::vector<double>>;

void printMatrix(const Matrix &m)
{
    for (int i = 0; i < 3; ++i)
    {
        for (int j = 0; j < 3; ++j)
        {
            double val = m[i][j];
            if (std::abs(val) < 1e-9)
                val = 0.0; // Убираем -0.000
            std::cout << std::fixed << std::setprecision(3) << val;
            if (j < 2)
                std::cout << "\t";
        }
        std::cout << "\n";
    }
}

int main(int argc, char *argv[])
{
    if (argc == 2 && std::string(argv[1]) == "-h")
    {
        std::cout << "Usage: invert.exe [matrix file]\n";
        return 0;
    }

    std::istream *in = &std::cin;
    std::ifstream fileIn;

    if (argc == 2)
    {
        fileIn.open(argv[1]);
        if (!fileIn.is_open())
        {
            std::cout << "Invalid matrix\n";
            return 1;
        }
        in = &fileIn;
    }

    Matrix m;
    std::string line;

    while (std::getline(*in, line))
    {
        if (line.empty())
            continue;
        std::stringstream ss(line);
        std::string token;
        std::vector<double> row;

        while (ss >> token)
        {
            try
            {
                size_t pos;
                double val = std::stod(token, &pos);
                if (pos != token.length())
                    throw std::invalid_argument("");
                row.push_back(val);
            }
            catch (...)
            {
                std::cout << "Invalid matrix\n";
                return 1;
            }
        }
        if (!row.empty())
            m.push_back(row);
    }

    if (m.size() != 3)
    {
        std::cout << "Invalid matrix format\n";
        return 1;
    }
    for (const auto &r : m)
    {
        if (r.size() != 3)
        {
            std::cout << "Invalid matrix format\n";
            return 1;
        }
    }

    double det = m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
                 m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) +
                 m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);

    if (std::abs(det) < 1e-9)
    {
        std::cout << "Non-invertible\n";
        return 1;
    }

    Matrix res(3, std::vector<double>(3));
    res[0][0] = (m[1][1] * m[2][2] - m[1][2] * m[2][1]) / det;
    res[0][1] = -(m[0][1] * m[2][2] - m[0][2] * m[2][1]) / det;
    res[0][2] = (m[0][1] * m[1][2] - m[0][2] * m[1][1]) / det;

    res[1][0] = -(m[1][0] * m[2][2] - m[1][2] * m[2][0]) / det;
    res[1][1] = (m[0][0] * m[2][2] - m[0][2] * m[2][0]) / det;
    res[1][2] = -(m[0][0] * m[1][2] - m[0][2] * m[1][0]) / det;

    res[2][0] = (m[1][0] * m[2][1] - m[1][1] * m[2][0]) / det;
    res[2][1] = -(m[0][0] * m[2][1] - m[0][1] * m[2][0]) / det;
    res[2][2] = (m[0][0] * m[1][1] - m[0][1] * m[1][0]) / det;

    printMatrix(res);
    return 0;
}