#include "raylib.h"
#include "Parser.h"
#include <iostream>
#include <string>
#include <cmath>

using namespace std;

// Функция для красивой отрисовки векторов (стрелок)
void DrawArrow(Vector2 start, Vector2 end, Color color)
{
    DrawLineEx(start, end, 3.0f, color);
    Vector2 dir = {end.x - start.x, end.y - start.y};
    float length = sqrt(dir.x * dir.x + dir.y * dir.y);
    if (length > 0)
    {
        dir.x /= length;
        dir.y /= length;
        Vector2 left = {end.x - dir.x * 10 - dir.y * 10, end.y - dir.y * 10 + dir.x * 10};
        Vector2 right = {end.x - dir.x * 10 + dir.y * 10, end.y - dir.y * 10 - dir.x * 10};
        DrawTriangle(end, left, right, color);
    }
}

int main()
{
    const int screenWidth = 1000;
    const int screenHeight = 600;
    SetConfigFlags(FLAG_MSAA_4X_HINT);
    InitWindow(screenWidth, screenHeight, "Interactive Physics Lab v2.0");
    SetTargetFPS(60);

    map<string, Unit> dict;
    Dimension d_mass(1, 0, 0, 0), d_len(0, 1, 0, 0), d_time(0, 0, 1, 0), d_force(1, 1, -2, 0);
    dict["kg"] = Unit("kg", 1.0, d_mass);
    dict["m"] = Unit("m", 1.0, d_len);
    dict["s"] = Unit("s", 1.0, d_time);
    dict["N"] = Unit("N", 1.0, d_force);
    Parser parser(dict);

    const float PIXELS_PER_METER = 50.0f;
    float mass = 2.0f;      // кг
    float positionX = 2.0f; // в метрах
    float velocityX = 0.0f; // в м/с

    char formulaInput[256] = "";
    int letterCount = 0;
    string statusMsg = "Awaiting input...";
    Color statusColor = GRAY;
    float currentForce = 0.0f;

    // Для графика скорости
    float speedHistory[200] = {0};
    int historyIndex = 0;
    float timer = 0.0f;

    while (!WindowShouldClose())
    {
        // --- ОБРАБОТКА ВВОДА ---
        int key = GetCharPressed();
        while (key > 0)
        {
            // Теперь пробел (32) разрешен для ввода!
            if ((key >= 32) && (key <= 125) && (letterCount < 255))
            {
                formulaInput[letterCount] = (char)key;
                formulaInput[letterCount + 1] = '\0';
                letterCount++;
            }
            key = GetCharPressed();
        }

        if (IsKeyPressed(KEY_BACKSPACE) && letterCount > 0)
        {
            letterCount--;
            formulaInput[letterCount] = '\0';
        }

        // Сброс сцены теперь на ENTER
        if (IsKeyPressed(KEY_ENTER))
        {
            positionX = 2.0f;
            velocityX = 0.0f;
            for (int i = 0; i < 200; i++)
                speedHistory[i] = 0; // Очистка графика
        }

        // --- ФИЗИЧЕСКИЙ РАСЧЕТ ---
        currentForce = 0.0f;
        if (letterCount > 0)
        {
            try
            {
                // Парсер пробует посчитать то, что мы ввели
                Quantity res = parser.calculate(formulaInput);
                if (res.getDimension() == d_force)
                {
                    currentForce = (float)res.getValueSI();
                    statusMsg = "Valid Force: " + to_string(currentForce) + " N";
                    statusColor = GREEN;
                }
                else
                {
                    statusMsg = "Formula is valid, but NOT a Force (N)!";
                    statusColor = ORANGE;
                }
            }
            catch (...)
            {
                statusMsg = "Syntax Error (e.g. missing unit or bracket)";
                statusColor = RED;
            }
        }
        else
        {
            statusMsg = "Type force (e.g., -10 N or 5kg * 2m / 1s / 1s)";
            statusColor = LIGHTGRAY;
        }

        // Применяем физику (F = ma -> a = F/m)
        float dt = GetFrameTime();
        float acceleration = currentForce / mass;
        velocityX += acceleration * dt;
        positionX += velocityX * dt;

        // Отскок от краев (упругий удар)
        if (positionX * PIXELS_PER_METER > screenWidth - 30)
        {
            positionX = (screenWidth - 30) / PIXELS_PER_METER;
            velocityX *= -0.8f;
        }
        else if (positionX * PIXELS_PER_METER < 30)
        {
            positionX = 30 / PIXELS_PER_METER;
            velocityX *= -0.8f;
        }

        // Запись данных для графика (10 раз в секунду)
        timer += dt;
        if (timer > 0.1f)
        {
            speedHistory[historyIndex] = velocityX;
            historyIndex = (historyIndex + 1) % 200;
            timer = 0.0f;
        }

        // --- ОТРИСОВКА ---
        BeginDrawing();
        ClearBackground({20, 20, 24, 255}); // Очень темный фон

        // Сетка
        for (int i = 0; i < screenWidth; i += PIXELS_PER_METER)
        {
            DrawLine(i, 0, i, screenHeight, {40, 40, 45, 255});
        }
        DrawLine(0, 350, screenWidth, 350, GRAY); // Земля

        // Геометрия: рисуем объект
        Vector2 screenPos = {positionX * PIXELS_PER_METER, 320};
        DrawRectangle(screenPos.x - 30, screenPos.y - 30, 60, 60, {41, 128, 185, 255});
        DrawRectangleLines(screenPos.x - 30, screenPos.y - 30, 60, 60, {52, 152, 219, 255});
        DrawText(TextFormat("%.1f kg", mass), screenPos.x - 15, screenPos.y - 10, 10, RAYWHITE);

        // Вектор силы (красный вправо, синий влево)
        if (abs(currentForce) > 0.1f)
        {
            float arrowLen = currentForce * 5.0f;
            Vector2 arrowEnd = {screenPos.x + arrowLen, screenPos.y};
            Color arrowColor = (currentForce > 0) ? Color{231, 76, 60, 255} : Color{52, 152, 219, 255};
            DrawArrow(screenPos, arrowEnd, arrowColor);
            DrawText("F", screenPos.x + arrowLen / 2, screenPos.y - 20, 20, arrowColor);
        }

        // Вектор скорости (зеленый, рисуется чуть выше)
        if (abs(velocityX) > 0.1f)
        {
            Vector2 velStart = {screenPos.x, screenPos.y - 35};
            Vector2 velEnd = {screenPos.x + velocityX * 10.0f, screenPos.y - 35};
            DrawArrow(velStart, velEnd, {46, 204, 113, 255});
            DrawText("v", velStart.x + velocityX * 5.0f, velStart.y - 20, 15, {46, 204, 113, 255});
        }

        // --- UI Панели ---
        DrawRectangle(20, 20, 450, 100, {30, 30, 35, 200});
        DrawRectangleLines(20, 20, 450, 100, {52, 152, 219, 255});
        DrawText("LAB TASK: Apply force to move the block.", 30, 30, 18, RAYWHITE);
        DrawText("You can use spaces and negative values now.", 30, 55, 15, LIGHTGRAY);
        DrawText("Press ENTER to reset simulation.", 30, 80, 15, {241, 196, 15, 255}); // Желтый текст

        // Ввод формулы
        DrawText("FORMULA INPUT:", 20, 140, 20, RAYWHITE);
        DrawRectangle(20, 170, 450, 40, {15, 15, 18, 255});
        DrawRectangleLines(20, 170, 450, 40, statusColor);
        DrawText(formulaInput, 30, 180, 20, RAYWHITE);
        if (((int)(GetTime() * 2)) % 2 == 0)
            DrawText("_", 30 + MeasureText(formulaInput, 20), 180, 20, RAYWHITE);
        DrawText(statusMsg.c_str(), 20, 220, 15, statusColor);

        // Телеметрия
        DrawRectangle(screenWidth - 250, 20, 230, 150, {30, 30, 35, 200});
        DrawText("TELEMETRY", screenWidth - 230, 30, 20, {46, 204, 113, 255});
        DrawText(TextFormat("Position: %.2f m", positionX), screenWidth - 230, 60, 15, RAYWHITE);
        DrawText(TextFormat("Velocity: %.2f m/s", velocityX), screenWidth - 230, 85, 15, RAYWHITE);
        DrawText(TextFormat("Accel:    %.2f m/s^2", acceleration), screenWidth - 230, 110, 15, RAYWHITE);

        // График скорости (в самом низу)
        DrawRectangle(20, 400, screenWidth - 40, 180, {15, 15, 18, 200});
        DrawRectangleLines(20, 400, screenWidth - 40, 180, {40, 40, 45, 255});
        DrawText("Velocity Chart (v - time)", 30, 410, 15, GRAY);
        DrawLine(20, 490, screenWidth - 20, 490, {60, 60, 65, 255}); // Ось X (ноль скорости)

        for (int i = 0; i < 199; i++)
        {
            int idx1 = (historyIndex + i) % 200;
            int idx2 = (historyIndex + i + 1) % 200;
            Vector2 p1 = {20.0f + i * ((screenWidth - 40) / 200.0f), 490.0f - speedHistory[idx1] * 5.0f};
            Vector2 p2 = {20.0f + (i + 1) * ((screenWidth - 40) / 200.0f), 490.0f - speedHistory[idx2] * 5.0f};
            DrawLineEx(p1, p2, 2.0f, {46, 204, 113, 255}); // Зеленая линия графика
        }

        EndDrawing();
    }

    CloseWindow();
    return 0;
}