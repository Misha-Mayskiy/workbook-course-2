# backend.py
import collections
import re


def solve(matrix_str, edges_str, targets_str, is_weighted=True):
    """
    Основная функция-решатель.
    Принимает флаг is_weighted для выбора алгоритма.
    """
    try:
        if is_weighted:
            return _solve_weighted(matrix_str, edges_str, targets_str)
        else:
            return _solve_unweighted(matrix_str, edges_str, targets_str)
    except ValueError as e:
        return f"Ошибка ввода: {e}"
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return f"Произошла внутренняя ошибка: {e}"


# --- РЕШАТЕЛЬ ДЛЯ ВЗВЕШЕННЫХ ГРАФОВ ---

def _solve_weighted(matrix_str, edges_str, targets_str):
    table_adj, table_weights = _parse_matrix_weighted(matrix_str)
    graph_adj, graph_nodes, graph_weights = _parse_edges_weighted(edges_str)
    target_nodes = _parse_targets(targets_str)

    _validate_inputs(len(table_adj), graph_nodes, target_nodes)

    table_degrees = {node: len(neighbors) for node, neighbors in table_adj.items()}
    graph_degrees = {node: len(neighbors) for node, neighbors in graph_adj.items()}

    if sorted(table_degrees.values()) != sorted(graph_degrees.values()):
        return _degree_error(graph_degrees, table_degrees)
    if sorted(table_weights) != sorted(graph_weights):
        return (f"Ошибка: Набор длин дорог графа и таблицы не совпадает.\n\n"
                f"Длины из графа: {sorted(graph_weights)}\n"
                f"Длины из таблицы: {sorted(table_weights)}")

    table_signatures = _get_signatures_weighted(table_adj, table_degrees)
    graph_signatures = _get_signatures_weighted(graph_adj, graph_degrees)

    return _find_matches(target_nodes, graph_signatures, table_signatures)


# --- РЕШАТЕЛЬ ДЛЯ НЕВЗВЕШЕННЫХ ГРАФОВ (СТАРАЯ ЛОГИКА) ---

def _solve_unweighted(matrix_str, edges_str, targets_str):
    table_adj_matrix = _parse_matrix_unweighted(matrix_str)
    graph_adj_list, graph_nodes = _parse_edges_unweighted(edges_str)
    target_nodes = _parse_targets(targets_str)

    _validate_inputs(len(table_adj_matrix), graph_nodes, target_nodes)

    table_degrees = {i + 1: sum(row) for i, row in enumerate(table_adj_matrix)}
    graph_degrees = {node: len(graph_adj_list.get(node, [])) for node in graph_nodes}

    if sorted(table_degrees.values()) != sorted(graph_degrees.values()):
        return _degree_error(graph_degrees, table_degrees)

    table_signatures = _get_signatures_unweighted(table_adj_matrix, table_degrees)
    graph_signatures = _get_signatures_from_adj_list_unweighted(graph_adj_list, graph_degrees)

    return _find_matches(target_nodes, graph_signatures, table_signatures)


# --- ОБЩИЕ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def _validate_inputs(table_size, graph_nodes, target_nodes):
    if table_size != len(graph_nodes):
        raise ValueError(
            f"Количество вершин в таблице ({table_size}) не совпадает с количеством в графе ({len(graph_nodes)}).")
    if not all(node in graph_nodes for node in target_nodes):
        missing = sorted([node for node in target_nodes if node not in graph_nodes])
        raise ValueError(f"Искомые вершины {missing} не найдены в графе.")


def _degree_error(graph_degrees, table_degrees):
    return (f"Ошибка: Степени вершин графа и таблицы не совпадают.\n\n"
            f"Степени графа (буквы): {sorted(graph_degrees.values())}\n"
            f"Степени таблицы (номера): {sorted(table_degrees.values())}")


def _find_matches(target_nodes, graph_signatures, table_signatures):
    table_sig_map = collections.defaultdict(list)
    for node, sig in table_signatures.items():
        table_sig_map[sig].append(node)

    graph_sig_map = collections.defaultdict(list)
    for node, sig in graph_signatures.items():
        graph_sig_map[sig].append(node)

    result_points = []
    ambiguous_nodes = []
    for target in sorted(target_nodes):
        target_sig = graph_signatures.get(target)
        if not target_sig:
            raise ValueError(f"Не удалось вычислить сигнатуру для вершины {target}.")

        candidates = table_sig_map.get(target_sig, [])

        if len(graph_sig_map.get(target_sig, [])) > 1 and len(candidates) > 1:
            ambiguous_nodes.extend(candidates)
            continue

        if len(candidates) == 1:
            result_points.append(candidates[0])
        else:
            return f"Не удалось однозначно определить пункт для вершины '{target}'. Кандидаты: {candidates}"

    if ambiguous_nodes:
        result_points.extend(sorted(list(set(ambiguous_nodes))))

    if not result_points:
        return "Не найдено соответствий для искомых вершин."

    return "".join(map(str, sorted(list(set(result_points)))))


def _parse_targets(targets_str):
    targets = [t.strip().upper() for t in targets_str.replace(',', ' ').split() if t.strip()]
    if not targets: raise ValueError("Искомые вершины не указаны.")
    return targets


# --- ФУНКЦИИ ДЛЯ ВЗВЕШЕННОГО РЕЖИМА ---

def _get_signatures_weighted(adj_list, degrees):
    signatures = {}
    for node, neighbors in adj_list.items():
        neighbor_info = sorted([(degrees[neighbor], weight) for neighbor, weight in neighbors.items()])
        signatures[node] = (degrees[node], tuple(neighbor_info))
    return signatures


def _parse_matrix_weighted(matrix_str):
    matrix, n = [], 0
    for line in matrix_str.strip().split('\n'):
        row = [int(v) if v.isdigit() else 0 for v in line.split()]
        if row: matrix.append(row)
    if not matrix: raise ValueError("Матрица пуста.")
    n = len(matrix)
    if not all(len(r) == n for r in matrix): raise ValueError("Матрица должна быть квадратной.")

    adj_list, weights = collections.defaultdict(dict), []
    for i in range(n):
        for j in range(i + 1, n):
            if matrix[i][j] > 0:
                u, v, w = i + 1, j + 1, matrix[i][j]
                adj_list[u][v], adj_list[v][u] = w, w
                weights.append(w)
    for i in range(n):
        if i + 1 not in adj_list: adj_list[i + 1] = {}
    return adj_list, weights


def _parse_edges_weighted(edges_str):
    adj_list, nodes, weights = collections.defaultdict(dict), set(), []
    for line in edges_str.strip().split('\n'):
        if not line.strip(): continue
        parts = re.split(r'[\s,-]+', line.strip().upper())
        if len(parts) != 3: raise ValueError(f"Неверный формат ребра: '{line}'. Ожидается 'A-B 10'.")
        u, v, w_str = parts
        try:
            w = int(w_str)
        except ValueError:
            raise ValueError(f"Неверный вес в строке: '{line}'")

        adj_list[u][v] = w
        adj_list[v][u] = w
        nodes.add(u)
        nodes.add(v)
        weights.append(w)

    if not nodes: raise ValueError("Описание графа пусто.")
    return adj_list, sorted(list(nodes)), weights


# --- ФУНКЦИИ ДЛЯ НЕВЗВЕШЕННОГО РЕЖИМА ---

def _get_signatures_unweighted(adj_matrix, degrees):
    signatures, n = {}, len(adj_matrix)
    for i in range(n):
        node_id, neighbor_degrees = i + 1, []
        for j in range(n):
            if adj_matrix[i][j] == 1:
                neighbor_degrees.append(degrees[j + 1])
        signatures[node_id] = (degrees[node_id], tuple(sorted(neighbor_degrees)))
    return signatures


def _get_signatures_from_adj_list_unweighted(adj_list, degrees):
    signatures = {}
    for node, neighbors in adj_list.items():
        neighbor_degrees = [degrees[neighbor] for neighbor in neighbors]
        signatures[node] = (degrees[node], tuple(sorted(neighbor_degrees)))
    return signatures


def _parse_matrix_unweighted(matrix_str):
    matrix = []
    for line in matrix_str.strip().split('\n'):
        row = [int(val) for val in line.split() if val.strip().isdigit()]
        if row: matrix.append(row)
    if not matrix: raise ValueError("Матрица смежности пуста.")
    n = len(matrix)
    if not all(len(r) == n for r in matrix): raise ValueError("Матрица смежности должна быть квадратной.")
    return matrix


def _parse_edges_unweighted(edges_str):
    adj_list, nodes = collections.defaultdict(list), set()
    for line in edges_str.strip().split('\n'):
        if not line.strip(): continue
        parts = [p.strip() for p in re.split(r'[\s,-]+', line.strip().upper()) if p.strip()]
        if len(parts) != 2: raise ValueError(f"Неверный формат ребра: '{line}'")
        u, v = parts[0], parts[1]

        adj_list[u].append(v)
        adj_list[v].append(u)
        nodes.add(u)
        nodes.add(v)

    if not nodes: raise ValueError("Описание графа пусто.")
    return adj_list, sorted(list(nodes))
