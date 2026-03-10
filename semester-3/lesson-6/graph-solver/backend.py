# backend.py
import collections
import re
from typing import Dict, List, Tuple, Set


def solve(matrix_str, edges_str, targets_str, is_weighted=True):
    """
    Основная функция-решатель.
    Теперь использует устойчивый парсинг и поиск изоморфизма (бэктрекинг),
    чтобы гарантированно находить корректное сопоставление или корректно объяснять ошибку.
    """
    try:
        # Парсинг таблицы
        if is_weighted:
            table_adj, table_weights = _parse_matrix_weighted(matrix_str)
        else:
            adj_matrix = _parse_matrix_unweighted(matrix_str)
            table_adj = _adj_from_matrix_unweighted(adj_matrix)
            table_weights = []  # не используется в невзвешенном режиме

        n = len(table_adj)

        # Парсинг графа
        if is_weighted:
            graph_adj, graph_nodes, graph_weights = _parse_edges_weighted(edges_str)
        else:
            graph_adj, graph_nodes = _parse_edges_unweighted(edges_str)
            graph_weights = []

        # Парсинг искомых вершин
        target_nodes = _parse_targets(targets_str)

        # Базовые проверки
        _validate_inputs(n, graph_nodes, target_nodes)

        # Проверка степеней
        table_degrees = {node: len(neigh) for node, neigh in table_adj.items()}
        graph_degrees = {node: len(neigh) for node, neigh in graph_adj.items()}
        if sorted(table_degrees.values()) != sorted(graph_degrees.values()):
            return _degree_error(graph_degrees, table_degrees)

        # Для взвешенного графа — проверка мультисета всех весов
        if is_weighted:
            # Вытащим веса из таблицы (уже есть) и из графа
            # graph_weights уже собран при разборе рёбер
            if sorted(table_weights) != sorted(graph_weights):
                return (f"Ошибка: Набор длин дорог графа и таблицы не совпадает.\n\n"
                        f"Длины из графа: {sorted(graph_weights)}\n"
                        f"Длины из таблицы: {sorted(table_weights)}")

        # Поиск изоморфизма(ов) между графом (буквы) и таблицей (номера)
        # Получаем все допустимые сопоставления (может быть несколько)
        mappings = _find_all_isomorphisms(graph_adj, table_adj, weighted=is_weighted)

        if not mappings:
            return "Ошибка: Не удалось сопоставить граф с таблицей. Проверьте корректность входных данных."

        # Собираем номера пунктов для искомых вершин из всех найденных сопоставлений
        result_points: Set[int] = set()
        for mapping in mappings:
            for t in target_nodes:
                if t in mapping:
                    result_points.add(mapping[t])

        if not result_points:
            return "Ошибка: Искомые вершины не найдены в полученных соответствиях."

        return "".join(map(str, sorted(result_points)))

    except ValueError as e:
        return f"Ошибка ввода: {e}"
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return f"Произошла внутренняя ошибка: {e}"


# ----------------------------- Парсинг и подготовка -----------------------------

def _parse_targets(targets_str: str) -> List[str]:
    # Разделители: запятые, пробелы, точки с запятой и т.п.
    parts = [p.strip().upper() for p in re.split(r'[\s,;]+', targets_str) if p.strip()]
    if not parts:
        raise ValueError("Искомые вершины не указаны.")
    return parts


def _validate_inputs(table_size: int, graph_nodes: List[str], target_nodes: List[str]):
    if table_size != len(graph_nodes):
        raise ValueError(
            f"Количество вершин в таблице ({table_size}) не совпадает с количеством в графе ({len(graph_nodes)}).")
    missing = sorted([node for node in target_nodes if node not in graph_nodes])
    if missing:
        raise ValueError(f"Искомые вершины {missing} не найдены в графе.")


def _degree_error(graph_degrees: Dict[str, int], table_degrees: Dict[int, int]):
    return (f"Ошибка: Степени вершин графа и таблицы не совпадают.\n\n"
            f"Степени графа (буквы): {sorted(graph_degrees.values())}\n"
            f"Степени таблицы (номера): {sorted(table_degrees.values())}")


# ---- Таблица: взвешенная матрица -> список смежности (веса в int) ----

def _parse_matrix_weighted(matrix_str: str) -> Tuple[Dict[int, Dict[int, int]], List[int]]:
    matrix: List[List[int]] = []
    for line in matrix_str.strip().splitlines():
        if not line.strip():
            continue
        row = []
        # Разрешаем только числа (неотрицательные). Пустое -> 0.
        for token in line.split():
            if re.fullmatch(r'\d+', token):
                row.append(int(token))
            else:
                row.append(0)
        if row:
            matrix.append(row)

    if not matrix:
        raise ValueError("Матрица пуста.")

    n = len(matrix)
    if not all(len(r) == n for r in matrix):
        raise ValueError("Матрица должна быть квадратной.")

    # Строим неориентированный граф по верхнему треугольнику
    adj: Dict[int, Dict[int, int]] = {i + 1: {} for i in range(n)}
    weights: List[int] = []
    for i in range(n):
        for j in range(i + 1, n):
            w = matrix[i][j]
            if w < 0:
                raise ValueError(f"Вес не может быть отрицательным (ячейка [{i + 1},{j + 1}] = {w}).")
            if w > 0:
                adj[i + 1][j + 1] = w
                adj[j + 1][i + 1] = w
                weights.append(w)
    return adj, weights


# ---- Таблица: невзвешенная матрица -> список смежности (вес=1) ----

def _parse_matrix_unweighted(matrix_str: str) -> List[List[int]]:
    matrix: List[List[int]] = []
    for line in matrix_str.strip().splitlines():
        if not line.strip():
            continue
        row = []
        for token in line.split():
            if token.strip().isdigit():
                row.append(int(token))
            else:
                # Если встретилось что-то нечисловое — считаем как 0
                row.append(0)
        if row:
            matrix.append(row)

    if not matrix:
        raise ValueError("Матрица смежности пуста.")
    n = len(matrix)
    if not all(len(r) == n for r in matrix):
        raise ValueError("Матрица смежности должна быть квадратной.")
    return matrix


def _adj_from_matrix_unweighted(matrix: List[List[int]]) -> Dict[int, Dict[int, int]]:
    n = len(matrix)
    adj: Dict[int, Dict[int, int]] = {i + 1: {} for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if matrix[i][j] == 1:
                adj[i + 1][j + 1] = 1
                adj[j + 1][i + 1] = 1
    return adj


# ---- Граф: парсинг рёбер (взвешенный) ----

def _parse_edges_weighted(edges_str: str) -> Tuple[Dict[str, Dict[str, int]], List[str], List[int]]:
    """
    Допускает строки вида:
      A-B 10
      A B 10
      А—Б 13   (любое тире: -, –, —)
      A        (изолированная вершина)
    Дубликаты рёбер с тем же весом игнорируются, с другим весом — ошибка.
    """
    adj: Dict[str, Dict[str, int]] = collections.defaultdict(dict)
    nodes: Set[str] = set()
    edge_weights: List[int] = []

    edge_map: Dict[Tuple[str, str], int] = {}

    for raw_line in edges_str.strip().splitlines():
        line = raw_line.strip().upper()
        if not line:
            continue

        # Нормализуем тире
        line = line.replace('—', '-').replace('–', '-').replace('−', '-')
        # Разрешаем запятые/точки с запятой как разделители
        line = re.sub(r'[;,]', ' ', line)
        parts = [p for p in re.split(r'\s+|-', line) if p]

        if len(parts) == 1:
            # Изолированная вершина
            u = parts[0]
            nodes.add(u)
            if u not in adj:
                adj[u] = {}
            continue

        if len(parts) >= 3 and parts[-1].isdigit():
            u, v, w_str = parts[0], parts[1], parts[-1]
            if u == v:
                raise ValueError(f"Найден петлевой ввод: '{raw_line}'.")
            w = int(w_str)
            key = (u, v) if u < v else (v, u)
            if key in edge_map:
                if edge_map[key] != w:
                    raise ValueError(f"Ребро {u}-{v} дублируется с разными весами ({edge_map[key]} и {w}).")
                # если вес тот же — просто игнорируем дубликат строки
            else:
                edge_map[key] = w
                adj[u][v] = w
                adj[v][u] = w
                nodes.add(u)
                nodes.add(v)
                edge_weights.append(w)
            continue

        raise ValueError(
            f"Неверный формат ребра: '{raw_line}'. Ожидается 'A-B 10' или 'A B 10', либо одиночная вершина.")

    if not nodes:
        raise ValueError("Описание графа пусто.")

    # Убедимся, что все вершины есть в adj даже если без рёбер
    for u in nodes:
        adj.setdefault(u, {})

    return adj, sorted(nodes), edge_weights


# ---- Граф: парсинг рёбер (невзвешенный) ----

def _parse_edges_unweighted(edges_str: str) -> Tuple[Dict[str, Dict[str, int]], List[str]]:
    """
    Допускает строки вида:
      A-B
      A B
      А—Б   (любое тире)
      A     (изолированная вершина)
    Дубликаты игнорируются.
    """
    adj: Dict[str, Dict[str, int]] = collections.defaultdict(dict)
    nodes: Set[str] = set()
    edge_set: Set[Tuple[str, str]] = set()

    for raw_line in edges_str.strip().splitlines():
        line = raw_line.strip().upper()
        if not line:
            continue
        line = line.replace('—', '-').replace('–', '-').replace('−', '-')
        line = re.sub(r'[;,]', ' ', line)
        parts = [p for p in re.split(r'\s+|-', line) if p]

        if len(parts) == 1:
            u = parts[0]
            nodes.add(u)
            if u not in adj:
                adj[u] = {}
            continue

        if len(parts) >= 2:
            u, v = parts[0], parts[1]
            if u == v:
                raise ValueError(f"Найден петлевой ввод: '{raw_line}'.")
            key = (u, v) if u < v else (v, u)
            if key not in edge_set:
                edge_set.add(key)
                adj[u][v] = 1
                adj[v][u] = 1
                nodes.add(u)
                nodes.add(v)
            continue

        raise ValueError(f"Неверный формат ребра: '{raw_line}'. Ожидается 'A-B' или 'A B', либо одиночная вершина.")

    if not nodes:
        raise ValueError("Описание графа пусто.")

    for u in nodes:
        adj.setdefault(u, {})

    return adj, sorted(nodes)


# -------------------------- Поиск изоморфизмов и ответ --------------------------

def _find_all_isomorphisms(graph: Dict[str, Dict[str, int]],
                           table: Dict[int, Dict[int, int]],
                           weighted: bool) -> List[Dict[str, int]]:
    """
    Ищет все сопоставления вершин graph (буквы) -> table (номера),
    согласованные по структуре (и по весам, если weighted=True).
    Возвращает список отображений.
    """
    g_nodes = list(graph.keys())
    t_nodes = list(table.keys())

    # Предварительные признаки (сильные локальные сигнатуры)
    g_deg = {u: len(graph[u]) for u in g_nodes}
    t_deg = {v: len(table[v]) for v in t_nodes}

    def node_signature(adj: Dict, degrees: Dict, node, include_weights: bool):
        # Степень узла
        deg = degrees[node]
        # Многомножество степеней соседей
        neigh_deg = sorted(degrees[n] for n in adj[node].keys())
        if include_weights:
            # Многомножество инцидентных весов
            inc_w = sorted(adj[node][n] for n in adj[node].keys())
            # Многомножество пар (вес, степень соседа)
            w_deg_pairs = sorted((adj[node][n], degrees[n]) for n in adj[node].keys())
            return (deg, tuple(neigh_deg), tuple(inc_w), tuple(w_deg_pairs))
        else:
            return (deg, tuple(neigh_deg))

    g_sig = {u: node_signature(graph, g_deg, u, weighted) for u in g_nodes}
    t_sig = {v: node_signature(table, t_deg, v, weighted) for v in t_nodes}

    # Кандидаты: для каждой вершины графа — какие номера таблицы возможны по локальной сигнатуре
    candidates: Dict[str, Set[int]] = {}
    sig_to_table_nodes: Dict[Tuple, List[int]] = collections.defaultdict(list)
    for v, sig in t_sig.items():
        sig_to_table_nodes[sig].append(v)

    for u in g_nodes:
        cand = set(sig_to_table_nodes.get(g_sig[u], []))
        if not cand:
            # Если локально никто не подходит — изоморфизма нет
            return []
        candidates[u] = cand

    # Бэктрекинг: назначаем вершины с наименьшим числом кандидатов
    solutions: List[Dict[str, int]] = []

    used_t: Set[int] = set()
    assignment: Dict[str, int] = {}

    # Порядок перебора: по возрастанию числа кандидатов
    order = sorted(g_nodes, key=lambda x: (len(candidates[x]), x))

    def consistent(u: str, v: int) -> bool:
        # проверяем согласованность с уже назначенными соседями
        for u2 in graph[u].keys():
            if u2 in assignment:
                v2 = assignment[u2]
                # В таблице должен быть такой же тип связи
                if v2 not in table[v]:
                    return False
                if weighted:
                    if table[v][v2] != graph[u][u2]:
                        return False
        return True

    def backtrack(idx: int):
        if idx == len(order):
            solutions.append(dict(assignment))
            return

        u = order[idx]
        # оставшиеся кандидаты для u (без уже занятых)
        cands = sorted(candidates[u] - used_t)
        for v in cands:
            if consistent(u, v):
                assignment[u] = v
                used_t.add(v)
                backtrack(idx + 1)
                used_t.remove(v)
                del assignment[u]

    backtrack(0)
    return solutions
