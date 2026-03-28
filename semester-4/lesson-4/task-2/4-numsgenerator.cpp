#include <iostream>
#include <set>
#include <vector>
#include <string>

std::set<int> GeneratePrimeNumbersSet(int upperBound)
{
    std::set<int> primes;
    if (upperBound < 2)
        return primes;

    // Решето Эратосфена. vector<bool> оптимизирован по памяти (1 бит на значение)
    std::vector<bool> is_prime(upperBound + 1, true);
    is_prime[0] = is_prime[1] = false;

    for (int p = 2; p * p <= upperBound; ++p)
    {
        if (is_prime[p])
        {
            for (int i = p * p; i <= upperBound; i += p)
            {
                is_prime[i] = false;
            }
        }
    }

    // ОПТИМИЗАЦИЯ: используем hint для вставки в конец дерева за O(1)
    auto hint = primes.end();
    for (int p = 2; p <= upperBound; ++p)
    {
        if (is_prime[p])
        {
            hint = primes.emplace_hint(hint, p);
        }
    }

    return primes;
}

int main(int argc, char *argv[])
{
    if (argc != 2)
    {
        std::cerr << "Usage: " << argv[0] << " <upper_bound>\n";
        return 1;
    }

    try
    {
        int bound = std::stoi(argv[1]);
        if (bound < 2 || bound > 100000000)
        {
            std::cout << "ERROR\n";
            return 0;
        }

        std::set<int> primes = GeneratePrimeNumbersSet(bound);

        for (int prime : primes)
        {
            std::cout << prime << " ";
        }
        std::cout << "\n";
    }
    catch (...)
    {
        std::cout << "ERROR\n";
        return 0;
    }

    return 0;
}