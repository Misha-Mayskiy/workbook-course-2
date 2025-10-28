from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Iterable, Dict, Callable


@dataclass
class GameRules:
    """
    Правила игры.
    - target_mode: 'sum' | 'max' | 'heap'
    - target: порог ≥ которого игра завершается
    - heap_index: индекс кучи для режима 'heap'
    - adds: допустимые прибавления (целые ≥ 1)
    - mults: допустимые множители (целые ≥ 2)
    - heaps: количество куч (1 или 2)
    """
    target_mode: str = "sum"
    target: int = 100
    heap_index: Optional[int] = None

    adds: List[int] = field(default_factory=lambda: [1])
    mults: List[int] = field(default_factory=lambda: [3])

    heaps: int = 2

    def __post_init__(self):
        if self.heaps not in (1, 2):
            raise ValueError("heaps должен быть 1 или 2")

        # Нормализуем списки действий: только уникальные отсортированные значения
        self.adds = sorted({a for a in self.adds if a >= 1})
        self.mults = sorted({m for m in self.mults if m >= 2})  # убираем 1

        if self.target <= 0:
            raise ValueError("target должен быть положительным")

        if self.target_mode == "heap":
            if self.heap_index is None:
                raise ValueError("heap_index must be set for target_mode='heap'")
            if not (0 <= self.heap_index < self.heaps):
                raise ValueError("heap_index вне диапазона куч")


def is_terminal(state: Tuple[int, ...], rules: GameRules) -> bool:
    if rules.target_mode == "sum":
        return sum(state) >= rules.target
    elif rules.target_mode == "max":
        return max(state) >= rules.target
    elif rules.target_mode == "heap":
        return state[rules.heap_index] >= rules.target  # type: ignore[index]
    else:
        raise ValueError(f"Unknown target_mode: {rules.target_mode}")


def iter_moves(state: Tuple[int, ...], rules: GameRules) -> Iterable[Tuple[int, ...]]:
    """Итерирует все позиции, достижимые за 1 ход (ровно одна куча меняется)."""
    n = len(state)
    seen = set()
    for i in range(n):
        val = state[i]
        # Прибавления
        for a in rules.adds:
            new_state = list(state)
            new_state[i] = val + a
            t = tuple(new_state)
            if t not in seen:
                seen.add(t)
                yield t
        # Умножения
        for m in rules.mults:
            new_state = list(state)
            new_state[i] = val * m
            t = tuple(new_state)
            if t not in seen:
                seen.add(t)
                yield t


def gen_moves(state: Tuple[int, ...], rules: GameRules) -> List[Tuple[int, ...]]:
    """Сгенерировать все позиции, достижимые за 1 ход (с уникализацией)."""
    return list(iter_moves(state, rules))


class EGESolver:
    """
    Универсальный solver для задач 19–21 ЕГЭ.
    - rules: GameRules
    - start_template: кортеж начальных куч, где ровно одно значение — None (там будет S)
      Примеры: (None,), (5, None)
    - s_min, s_max: диапазон S, включительно
    """

    def __init__(self, rules: GameRules, start_template: Tuple[Optional[int], ...], s_min: int, s_max: int):
        self.rules = rules
        self.start_tmpl = start_template
        self.s_min = min(s_min, s_max)
        self.s_max = max(s_min, s_max)

        if sum(1 for x in start_template if x is None) != 1:
            raise ValueError("start_template должен содержать ровно один None — место для S")
        if len(start_template) != rules.heaps:
            raise ValueError("Длина start_template должна совпадать с rules.heaps")

        self.var_idx = next(i for i, x in enumerate(start_template) if x is None)

        # Кэши: сильно ускоряют переборы
        self._moves_cache: Dict[Tuple[int, ...], Tuple[Tuple[int, ...], ...]] = {}
        self._w1_cache: Dict[Tuple[int, ...], bool] = {}
        self._can_cache: Dict[Tuple[Tuple[int, ...], int], bool] = {}

    def _start_from_S(self, S: int) -> Tuple[int, ...]:
        st = list(self.start_tmpl)
        st[self.var_idx] = S
        return tuple(st)

    def _moves(self, state: Tuple[int, ...]) -> Tuple[Tuple[int, ...], ...]:
        res = self._moves_cache.get(state)
        if res is not None:
            return res
        res = tuple(iter_moves(state, self.rules))
        self._moves_cache[state] = res
        return res

    def _has_move_to_terminal(self, state: Tuple[int, ...]) -> bool:
        cached = self._w1_cache.get(state)
        if cached is not None:
            return cached
        for nxt in self._moves(state):
            if is_terminal(nxt, self.rules):
                self._w1_cache[state] = True
                return True
        self._w1_cache[state] = False
        return False

    def _can_win_in(self, state: Tuple[int, ...], k: int) -> bool:
        """
        Выигрыш за k собственных ходов текущего игрока.
        - Терминальная позиция: False (ходить уже некому — текущий проиграл).
        - k == 0: False.
        - Иначе: существует ход s1:
            * если s1 терминал -> True (выигрыш сразу)
            * иначе для всех ответов соперника s2: _can_win_in(s2, k-1) == True
        """
        key = (state, k)
        if key in self._can_cache:
            return self._can_cache[key]

        if is_terminal(state, self.rules):
            self._can_cache[key] = False
            return False
        if k == 0:
            self._can_cache[key] = False
            return False

        for s1 in self._moves(state):
            if is_terminal(s1, self.rules):
                self._can_cache[key] = True
                return True
            # Соперник отвечает из s1
            opp_moves = self._moves(s1)
            if not opp_moves:
                # Если у соперника нет ходов и s1 не терминал — текущий выигрывает.
                self._can_cache[key] = True
                return True

            # Гарантия: для всех ответов соперника мы выигрываем за k-1
            if all(self._can_win_in(s2, k - 1) for s2 in opp_moves):
                self._can_cache[key] = True
                return True

        self._can_cache[key] = False
        return False

    def solve_all(
            self,
            progress_cb: Optional[Callable[[int, int], None]] = None,
            cancel_cb: Optional[Callable[[], bool]] = None,
    ) -> Tuple[List[int], List[int], List[int]]:
        """
        Вернёт три списка S для задач 19, 20, 21 (полные множества подходящих S).
        Можно передать:
        - progress_cb(i, total) — прогресс по S
        - cancel_cb() -> bool — если True, расчёт прерывается исключением
        """
        s_list_19: List[int] = []
        s_list_20: List[int] = []
        s_list_21: List[int] = []

        total = self.s_max - self.s_min + 1
        for idx, S in enumerate(range(self.s_min, self.s_max + 1), start=1):
            if cancel_cb and cancel_cb():
                raise RuntimeError("CANCELLED")
            if progress_cb:
                progress_cb(idx, total)

            start = self._start_from_S(S)

            # 19
            ok_19 = False
            for pm in self._moves(start):  # ходы Пети
                if is_terminal(pm, self.rules):
                    continue  # неудачным такой ход не считается
                if self._has_move_to_terminal(pm):  # ход Вани
                    ok_19 = True
                    break
            if ok_19:
                s_list_19.append(S)

            # 20
            w1_petya = self._has_move_to_terminal(start)
            w2_petya = self._can_win_in(start, 2)
            if (not w1_petya) and w2_petya:
                s_list_20.append(S)

            # 21
            petya_moves = self._moves(start)
            if any(is_terminal(pm, self.rules) for pm in petya_moves):
                ok_21 = False
            else:
                all_vanya_w2 = all(self._can_win_in(pm, 2) for pm in petya_moves)
                exists_not_w1 = any(not self._has_move_to_terminal(pm) for pm in petya_moves)
                ok_21 = all_vanya_w2 and exists_not_w1
            if ok_21:
                s_list_21.append(S)

        return s_list_19, s_list_20, s_list_21
