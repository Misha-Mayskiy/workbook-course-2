from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple, Optional


@dataclass
class GameRules:
    # Режим цели
    # 'sum'  -> суммарно >= target
    # 'max'  -> максимум >= target
    # 'heap' -> конкретная куча >= target (heap_index обязателен)
    target_mode: str = "sum"
    target: int = 100
    heap_index: Optional[int] = None  # для target_mode='heap'

    # Допустимые ходы к одной куче за ход
    adds: List[int] = None  # например [1]
    mults: List[int] = None  # например [3]

    # Количество куч (1 или 2)
    heaps: int = 2

    def __post_init__(self):
        if self.adds is None:
            self.adds = [1]
        if self.mults is None:
            self.mults = [3]
        # Удалим 1 из множителей (умножение на 1 бессмысленно)
        self.mults = [m for m in self.mults if m > 1]


def is_terminal(state: Tuple[int, ...], rules: GameRules) -> bool:
    if rules.target_mode == "sum":
        return sum(state) >= rules.target
    elif rules.target_mode == "max":
        return max(state) >= rules.target
    elif rules.target_mode == "heap":
        if rules.heap_index is None:
            raise ValueError("heap_index must be set for target_mode='heap'")
        return state[rules.heap_index] >= rules.target
    else:
        raise ValueError(f"Unknown target_mode: {rules.target_mode}")


def gen_moves(state: Tuple[int, ...], rules: GameRules) -> List[Tuple[int, ...]]:
    """Сгенерировать все позиции, достижимые за 1 ход (применять к ровно одной куче)."""
    res = set()
    n = len(state)
    for i in range(n):
        val = state[i]
        # Прибавления
        for a in rules.adds:
            new_state = list(state)
            new_state[i] = val + a
            res.add(tuple(new_state))
        # Умножения
        for m in rules.mults:
            new_state = list(state)
            new_state[i] = val * m
            res.add(tuple(new_state))
    return list(res)


class EGESolver:
    """
    Универсальный solver для задач 19–21.
    Параметры:
    - rules: GameRules
    - start_template: кортеж начальных куч, где одно место может быть None (там будет S)
      Примеры:
        одна куча: (None,)  -> S в одной куче
        две кучи: (5, None) -> первая фикс. 5, вторая S
    - s_min, s_max: диапазон значений S (включительно)
    """

    def __init__(self, rules: GameRules, start_template: Tuple[Optional[int], ...], s_min: int, s_max: int):
        self.rules = rules
        self.start_tmpl = start_template
        self.s_min = s_min
        self.s_max = s_max

        if sum(1 for x in start_template if x is None) != 1:
            raise ValueError("start_template должен содержать ровно один None — место для S")

        if len(start_template) != rules.heaps:
            raise ValueError("Длина start_template должна совпадать с количеством куч в rules.heaps")

        # индекс переменной кучи
        self.var_idx = [i for i, x in enumerate(start_template) if x is None][0]

    @staticmethod
    def _check_w1(state: Tuple[int, ...], rules: GameRules) -> bool:
        """Есть ли ход прямо в терминал."""
        for nxt in gen_moves(state, rules):
            if is_terminal(nxt, rules):
                return True
        return False

    @staticmethod
    @lru_cache(maxsize=None)
    def _can_win_in(state: Tuple[int, ...], k: int, rules_pack: Tuple) -> bool:
        """
        Мемоизированная функция:
        - state — позиция
        - k — число собственных ходов текущего игрока, за которые он хочет гарантированно выиграть
        - rules_pack — сериализация правил (для кэширования)
        Логика:
        - терминальная позиция -> False (ходить уже некому, текущий проиграл)
        - k == 0 -> False
        - иначе: существует ход s1:
            * если s1 терминал -> True
            * иначе для всех ответов соперника s2 выполняется _can_win_in(s2, k-1) == True
              (потому что после хода соперника снова ходит текущий)
        """
        # восстановим rules из кортежа
        rules = EGESolver._unpack_rules(rules_pack)

        if is_terminal(state, rules):
            return False
        if k == 0:
            return False

        next_positions = gen_moves(state, rules)
        for s1 in next_positions:
            if is_terminal(s1, rules):
                return True
            # Соперник ходит из s1
            opponent_replies = gen_moves(s1, rules)
            if not opponent_replies:
                # Если у соперника нет ходов и s1 не терминал — в наших задачах такого обычно нет
                # но если случится, считаем, что текущий выигрывает (оппонент застрял)
                return True
            # Требование для гарантии: для всех ответов соперника мы всё равно выигрываем за k-1
            ok = True
            for s2 in opponent_replies:
                if not EGESolver._can_win_in(s2, k - 1, rules_pack):
                    ok = False
                    break
            if ok:
                return True

        return False

    @staticmethod
    def _pack_rules(rules: GameRules) -> Tuple:
        """Преобразуем правила к хешируемому кортежу для кэша."""
        return (
            rules.target_mode,
            rules.target,
            rules.heap_index,
            tuple(sorted(rules.adds)),
            tuple(sorted(rules.mults)),
            rules.heaps,
        )

    @staticmethod
    def _unpack_rules(pack: Tuple) -> GameRules:
        """Восстановим GameRules из кортежа (только для внутренних нужд кеша)."""
        mode, tgt, hidx, adds, mults, heaps = pack
        return GameRules(
            target_mode=mode,
            target=tgt,
            heap_index=hidx,
            adds=list(adds),
            mults=list(mults),
            heaps=heaps,
        )

    def _start_from_S(self, S: int) -> Tuple[int, ...]:
        st = list(self.start_tmpl)
        st[self.var_idx] = S
        return tuple(st)

    def solve_all(self):
        """Вернёт три списка S для задач 19, 20, 21 (полные множества подходящих S)."""
        rules_pack = self._pack_rules(self.rules)
        # Очистим кеш при каждом прогоне диапазона (важно при смене правил)
        EGESolver._can_win_in.cache_clear()

        s_list_19 = []
        s_list_20 = []
        s_list_21 = []

        for S in range(self.s_min, self.s_max + 1):
            start = self._start_from_S(S)

            # 19: "Ваня выиграл своим первым ходом после неудачного первого хода Пети."
            # Т.е. существует первый ход Пети (в терминал не считается), после которого у Вани есть Win in 1.
            petya_moves = gen_moves(start, self.rules)
            ok_19 = False
            for pm in petya_moves:
                if is_terminal(pm, self.rules):
                    # тут Ваня ход не получит — такой ход Пети не считается "неудачным"
                    continue
                if self._check_w1(pm, self.rules):  # теперь ходит Ваня
                    ok_19 = True
                    break
            if ok_19:
                s_list_19.append(S)

            # 20: "Петя не может выиграть за 1; но может выиграть своим вторым ходом при любой игре Вани."
            w1_petya = self._check_w1(start, self.rules)
            w2_petya = self._can_win_in(start, 2, rules_pack)
            if (not w1_petya) and w2_petya:
                s_list_20.append(S)

            # 21:
            #  1) При любой игре Пети после его первого хода Ваня выигрывает первым или вторым ходом
            #     -> для всех ходов Пети pm: Win_in_2 для Вани (т.е. _can_win_in(pm, 2) True)
            #  2) Но Ваня не может гарантированно выиграть первым ходом
            #     -> существует ход Пети pm, для которого W1 Вани ложно
            petya_moves = gen_moves(start, self.rules)

            # Если у Пети есть ход в терминал, условие 1) автоматически нарушается
            if any(is_terminal(pm, self.rules) for pm in petya_moves):
                ok_21 = False
            else:
                all_vanya_w2 = all(self._can_win_in(pm, 2, rules_pack) for pm in petya_moves)
                exists_not_w1 = any(not self._check_w1(pm, self.rules) for pm in petya_moves)
                ok_21 = all_vanya_w2 and exists_not_w1

            if ok_21:
                s_list_21.append(S)

        return s_list_19, s_list_20, s_list_21
