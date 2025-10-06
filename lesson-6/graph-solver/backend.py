# backend.py
import collections


def solve(matrix_str, edges_str, targets_str):
    """
    Основная функция-решатель, которую вызывает интерфейс.
    Использует "сигнатуры" вершин (своя степень + степени соседей) для сопоставления.
    """
    try:
        # 1. Парсинг всех входных данных
        table_adj = _parse_matrix(matrix_str)
        graph_adj, graph_nodes = _parse_edges(edges_str)
        target_nodes = _parse_targets(targets_str)

        # Проверки на корректность
        if len(table_adj) != len(graph_nodes):
            return f"Ошибка: Количество вершин в таблице ({len(table_adj)}) не совпадает с количеством в графе ({len(graph_nodes)})."

        if not all(node in graph_nodes for node in target_nodes):
            missing = sorted([node for node in target_nodes if node not in graph_nodes])
            return f"Ошибка: Искомые вершины {missing} не найдены в графе."

        # 2. Вычисление характеристик для обеих структур (таблицы и графа)
        table_degrees = _get_degrees(table_adj)
        graph_degrees = {node: len(graph_adj.get(node, [])) for node in graph_nodes}

        # Первичная проверка по набору степеней - самый быстрый способ найти несоответствие
        if sorted(table_degrees.values()) != sorted(graph_degrees.values()):
            return (f"Ошибка: Степени вершин графа и таблицы не совпадают.\n\n"
                    f"Степени графа (буквы): {sorted(graph_degrees.values())}\n"
                    f"Степени таблицы (номера): {sorted(table_degrees.values())}")

        # 3. Вычисление "сигнатур"
        table_signatures = _get_signatures(table_adj, table_degrees)
        graph_signatures = _get_signatures_from_adj_list(graph_adj, graph_degrees)

        # 4. Поиск соответствий по сигнатурам
        # Создаем карту "сигнатура -> список вершин с этой сигнатурой"
        table_sig_map = collections.defaultdict(list)
        for node, sig in table_signatures.items():
            table_sig_map[sig].append(node)

        graph_sig_map = collections.defaultdict(list)
        for node, sig in graph_signatures.items():
            graph_sig_map[sig].append(node)

        # 5. Находим ответ для искомых вершин
        result_points = []
        ambiguous_nodes = []  # Для вершин, которые не удалось однозначно определить

        for target in sorted(target_nodes):  # Сортируем для стабильного результата
            target_sig = graph_signatures.get(target)
            if not target_sig:
                # Эта проверка уже была, но для надежности
                return f"Не удалось вычислить сигнатуру для вершины {target}."

            # Ищем кандидатов в таблице с такой же сигнатурой
            candidates = table_sig_map.get(target_sig, [])

            # Проверяем на неоднозначность
            # Если для одной сигнатуры есть несколько букв и несколько цифр, то они неразличимы этим методом
            if len(graph_sig_map.get(target_sig, [])) > 1 and len(candidates) > 1:
                # Если все искомые вершины имеют одну и ту же неоднозначную сигнатуру,
                # то мы можем просто вернуть всех кандидатов.
                # Это частый случай в ЕГЭ (например, "найдите сумму длин дорог из A в B", где A и B симметричны)
                ambiguous_nodes.extend(candidates)
                continue

            if len(candidates) == 1:
                result_points.append(candidates[0])
            else:
                # Если кандидатов 0 или больше 1, но они не являются искомыми
                return f"Не удалось однозначно определить пункт для вершины '{target}'. Кандидаты: {candidates}"

        # Если были неоднозначные, но они подходят под условие
        if ambiguous_nodes:
            # Убираем дубликаты и добавляем к результату
            unique_ambiguous = sorted(list(set(ambiguous_nodes)))
            result_points.extend(unique_ambiguous)

        if not result_points:
            return "Не найдено соответствий для искомых вершин."

        return "".join(map(str, sorted(list(set(result_points)))))

    except ValueError as e:
        return f"Ошибка ввода: {e}"
    except Exception as e:
        # Улучшенный вывод внутренних ошибок для отладки
        import traceback
        print(traceback.format_exc())
        return f"Произошла внутренняя ошибка: {e}"


# --- Вспомогательные функции ---

def _get_degrees(adj_matrix):
    """Вычисляет степени вершин по матрице смежности."""
    # Нумерация с 1, как в задаче
    return {i + 1: sum(row) for i, row in enumerate(adj_matrix)}


def _get_signatures(adj_matrix, degrees):
    """Вычисляет сигнатуры для вершин таблицы."""
    signatures = {}
    n = len(adj_matrix)
    for i in range(n):
        node_id = i + 1
        neighbor_degrees = []
        for j in range(n):
            if adj_matrix[i][j] == 1:
                neighbor_id = j + 1
                neighbor_degrees.append(degrees[neighbor_id])

        # Сигнатура = (своя степень, отсортированный кортеж степеней соседей)
        # Кортеж используется, так как он неизменяемый и может быть ключом словаря
        signatures[node_id] = (degrees[node_id], tuple(sorted(neighbor_degrees)))
    return signatures


def _get_signatures_from_adj_list(adj_list, degrees):
    """Вычисляет сигнатуры для вершин графа (заданного списком смежности)."""
    signatures = {}
    for node, neighbors in adj_list.items():
        neighbor_degrees = [degrees[neighbor] for neighbor in neighbors]
        signatures[node] = (degrees[node], tuple(sorted(neighbor_degrees)))
    return signatures


def _parse_matrix(matrix_str):
    """Преобразует текстовое представление таблицы в числовую матрицу."""
    matrix = []
    for line in matrix_str.strip().split('\n'):
        row = [int(val) for val in line.split() if val.strip().isdigit()]
        if row:
            matrix.append(row)
    if not matrix:
        raise ValueError("Матрица смежности пуста.")
    n = len(matrix)
    if not all(len(r) == n for r in matrix):
        raise ValueError("Матрица смежности должна быть квадратной.")
    return matrix


def _parse_edges(edges_str):
    """Преобразует текстовое представление ребер в список смежности и множество вершин."""
    adj_list = collections.defaultdict(list)
    nodes = set()
    for line in edges_str.strip().split('\n'):
        line = line.strip().upper()
        if not line: continue
        # Более гибкий парсинг разделителей
        parts = [p.strip() for p in line.replace(',', ' ').replace('-', ' ').split() if p.strip()]
        if len(parts) != 2: raise ValueError(f"Неверный формат ребра: '{line}'")
        u, v = parts[0], parts[1]
        adj_list[u].append(v)
        adj_list[v].append(u)
        nodes.add(u)
        nodes.add(v)
    if not nodes:
        raise ValueError("Описание графа пусто.")
    return adj_list, sorted(list(nodes))


def _parse_targets(targets_str):
    """Преобразует строку с искомыми вершинами в список."""
    targets = [t.strip().upper() for t in targets_str.replace(',', ' ').split() if t.strip()]
    if not targets: raise ValueError("Искомые вершины не указаны.")
    return targets
