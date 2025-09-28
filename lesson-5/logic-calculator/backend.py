class TruthTableCalculator:
    def __init__(self):
        self.results = []
        self.expression = ""

    def calculate(self, expression):
        """Вычисляет таблицу истинности"""
        self.expression = expression
        self.results = []

        for w in range(2):
            for x in range(2):
                for y in range(2):
                    for z in range(2):
                        try:
                            result = eval(expression)
                            self.results.append({
                                'w': w, 'x': x, 'y': y, 'z': z,
                                'result': bool(result)
                            })
                        except Exception as e:
                            raise Exception(f"Ошибка при w={w}, x={x}, y={y}, z={z}: {str(e)}")

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

        # Простое создание минтермов
        terms = []
        for r in true_results:
            term_parts = []
            if r['w']:
                term_parts.append("w")
            else:
                term_parts.append("not w")
            if r['x']:
                term_parts.append("x")
            else:
                term_parts.append("not x")
            if r['y']:
                term_parts.append("y")
            else:
                term_parts.append("not y")
            if r['z']:
                term_parts.append("z")
            else:
                term_parts.append("not z")

            terms.append(f"({' and '.join(term_parts)})")

        return " or ".join(terms)
