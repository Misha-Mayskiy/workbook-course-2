from itertools import permutations
import re


class TruthTableCalculator:
    def __init__(self):
        self.results = []
        self.expression = ""
        self.variables = []

    def calculate(self, expression):
        """Вычисляет таблицу истинности для выражения."""
        self.expression = expression
        self.variables = self._extract_variables(expression)
        if not self.variables:
            raise Exception("Не удалось найти переменные в выражении.")

        self.results = []
        num_vars = len(self.variables)

        for i in range(2 ** num_vars):
            values = {}
            temp_i = i
            # Присваиваем значения переменным в обратном порядке для стандартного вида таблицы
            for var in reversed(self.variables):
                values[var] = temp_i % 2
                temp_i //= 2

            try:
                result = eval(self.expression, {"__builtins__": {}}, values)
                row = values
                row['result'] = bool(result)
                self.results.append(row)
            except Exception as e:
                raise Exception(f"Ошибка вычисления для {values}: {str(e)}")

        return self.results

    def get_filtered_results(self, filter_type='all'):
        """Возвращает отфильтрованные результаты"""
        if filter_type == 'all':
            return self.results
        elif filter_type == 'true':
            return [r for r in self.results if r['result']]
        elif filter_type == 'false':
            return [r for r in self.results if not r['result']]
        elif filter_type == 'minority':
            true_count = sum(1 for r in self.results if r['result'])
            false_count = len(self.results) - true_count
            if true_count < false_count:
                return [r for r in self.results if r['result']]
            elif false_count < true_count:
                return [r for r in self.results if not r['result']]
            else:
                return self.results
        return self.results

    def get_stats(self):
        """Возвращает статистику"""
        if not self.results:
            return {}

        true_count = sum(1 for r in self.results if r['result'])
        false_count = len(self.results) - true_count

        return {
            'total': len(self.results),
            'true': true_count,
            'false': false_count,
            'minority': 'True' if true_count < false_count else 'False' if false_count < true_count else 'Равно'
        }

    def create_expression_from_table(self, custom_results=None):
        """Создает выражение из таблицы истинности (упрощенная версия)"""
        results = custom_results or self.results
        true_results = [r for r in results if r['result']]

        if not true_results:
            return "False"
        if len(true_results) == len(results):
            return "True"

        terms = []
        for r in true_results:
            term_parts = []
            for var in self.variables:
                if r[var]:
                    term_parts.append(var)
                else:
                    term_parts.append(f"not {var}")
            terms.append(f"({' and '.join(term_parts)})")

        return " or ".join(terms)

    def solve_ege_task(self, expression, incomplete_table):
        """
        Решает задачу ЕГЭ: определяет соответствие переменных по неполной таблице.
        Значения в таблице могут быть 0, 1 или None (неизвестно).
        """
        variables = sorted(self._extract_variables(expression))
        if len(variables) != 4:
            raise Exception(f"Выражение должно содержать ровно 4 переменные, найдено: {variables}")

        # Генерируем полную таблицу истинности для выражения
        full_table = []
        for x1 in range(2):
            for x2 in range(2):
                for x3 in range(2):
                    for x4 in range(2):
                        # Создаем словарь для eval(), где ключи - имена переменных
                        local_vars = {
                            variables[0]: x1,
                            variables[1]: x2,
                            variables[2]: x3,
                            variables[3]: x4
                        }
                        result = eval(expression, {"__builtins__": {}}, local_vars)

                        row = local_vars
                        row['result'] = bool(result)
                        full_table.append(row)

        columns = ['F1', 'F2', 'F3', 'F4']
        solutions = []

        # Перебираем все возможные перестановки переменных по столбцам
        for p_vars in permutations(variables):
            # p_vars - это гипотеза, например ('y', 'x', 'w', 'z')
            # Это значит, что F1=y, F2=x, F3=w, F4=z

            # Фильтруем полную таблицу, оставляя только строки, которые могут соответствовать
            # фрагменту из задачи (по значению функции)
            target_result = incomplete_table[0]['result']
            candidate_rows = [row for row in full_table if row['result'] == target_result]

            # Если кандидатов меньше, чем строк в задаче, гипотеза неверна
            if len(candidate_rows) < len(incomplete_table):
                continue

            # Теперь нужно проверить, можно ли сопоставить строки из задачи
            # с уникальными строками из числа кандидатов

            # Перебираем все комбинации строк-кандидатов
            for p_rows in permutations(candidate_rows, len(incomplete_table)):
                is_valid_mapping = True
                # Сопоставляем i-ю строку из задачи с i-й строкой из комбинации кандидатов
                for i in range(len(incomplete_table)):
                    problem_row = incomplete_table[i]
                    candidate_row = p_rows[i]

                    # Проверяем на противоречия
                    for col_idx, col_name in enumerate(columns):
                        var_for_this_col = p_vars[col_idx]
                        problem_value = problem_row[col_name]
                        candidate_value = candidate_row[var_for_this_col]

                        # Если в задаче есть значение, и оно не совпадает с кандидатом - это противоречие
                        if problem_value is not None and problem_value != candidate_value:
                            is_valid_mapping = False
                            break
                    if not is_valid_mapping:
                        break

                # Если для этой комбинации строк все сошлось, значит гипотеза о переменных верна
                if is_valid_mapping:
                    solution_str = "".join(p_vars)
                    if solution_str not in solutions:
                        solutions.append(solution_str)

        return solutions

    def _extract_variables(self, expression):
        """Извлекает уникальные переменные из выражения"""
        # Ищем буквы/слова, которые не являются ключевыми словами
        keywords = {'and', 'or', 'not', 'True', 'False'}
        tokens = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', expression)
        variables = sorted(list(set(token for token in tokens if token not in keywords)))
        return variables
