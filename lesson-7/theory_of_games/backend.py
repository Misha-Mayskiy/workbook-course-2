from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Iterable, Dict, Callable


@dataclass
class GameRules:
    """
    Правила игры.
    - target_mode: 'sum' | 'max' | 'heap'
    - target: порог
    - finish_cmp: 'ge' (>= target) или 'lt' (< target)
    - heap_index: индекс кучи для режима 'heap'
    - adds: целочисленные сдвиги (могут быть отрицательными), 0 исключается
    - mults: множители (целые >= 2)
    - divs: делители (целые >= 2), результат — целочисленное деление (округление вниз)
    - heaps: количество куч (1 или 2)
    """
    target_mode: str = "sum"
    target: int = 100
    finish_cmp: str = "ge"  # 'ge' или 'lt'
    heap_index: Optional[int] = None

    adds: List[int] = field(default_factory=lambda: [1])
    mults: List[int] = field(default_factory=lambda: [3])
    divs: List[int] = field(default_factory=list)

    heaps: int = 2

    def __post_init__(self):
        if self.heaps not in (1, 2):
            raise ValueError("heaps должен быть 1 или 2")

        if self.finish_cmp not in ("ge", "lt"):
            raise ValueError("finish_cmp должен быть 'ge' или 'lt'")

        # Нормализация списков действий
        self.adds = sorted({a for a in self.adds if a != 0})
        self.mults = sorted({m for m in self.mults if m >= 2})
        self.divs = sorted({d for d in self.divs if d >= 2})

        if self.target <= 0:
            # допускаем положительный порог (так же работает в 'lt' режиме)
            raise ValueError("target должен быть положительным")

        if self.target_mode == "heap":
            if self.heap_index is None:
                raise ValueError("heap_index must be set for target_mode='heap'")
            if not (0 <= self.heap_index < self.heaps):
                raise ValueError("heap_index вне диапазона куч")


def is_terminal(state: Tuple[int, ...], rules: GameRules) -> bool:
    if rules.target_mode == "sum":
        val = sum(state)
    elif rules.target_mode == "max":
        val = max(state)
    elif rules.target_mode == "heap":
        idx = rules.heap_index or 0
        val = state[idx]
    else:
        raise ValueError(f"Unknown target_mode: {rules.target_mode}")

    if rules.finish_cmp == "ge":
        return val >= rules.target
    else:  # "lt"
        return val < rules.target


def iter_moves(state: Tuple[int, ...], rules: GameRules) -> Iterable[Tuple[int, ...]]:
    """Итерирует все позиции, достижимые за 1 ход (меняется ровно одна куча)."""
    n = len(state)
    seen = set()
    for i in range(n):
        val = state[i]
        # Сдвиги (прибавления/вычитания)
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
        # Деления (округление вниз)
        for d in rules.divs:
            new_state = list(state)
            new_state[i] = val // d
            t = tuple(new_state)
            if t not in seen:
                seen.add(t)
                yield t


def gen_moves(state: Tuple[int, ...], rules: GameRules) -> List[Tuple[int, ...]]:
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

        # Кэши
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
            * если s1 терминал -> True
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
            opp_moves = self._moves(s1)
            if not opp_moves:
                self._can_cache[key] = True
                return True
            if all(self._can_win_in(s2, k - 1) for s2 in opp_moves):
                self._can_cache[key] = True
                return True

        self._can_cache[key] = False
        return False

    # ---------- Форматирование/стратегии ----------
    def fmt_state(self, st: Tuple[int, ...]) -> str:
        return "(" + ", ".join(map(str, st)) + ")"

    def describe_move(self, a: Tuple[int, ...], b: Tuple[int, ...]) -> str:
        if len(a) != len(b):
            return f"{self.fmt_state(a)} → {self.fmt_state(b)}"
        idx = [i for i in range(len(a)) if a[i] != b[i]]
        if len(idx) != 1:
            return f"{self.fmt_state(a)} → {self.fmt_state(b)}"
        i = idx[0]
        old, new = a[i], b[i]
        op = None
        # Пробуем умножение
        if old != 0 and new % old == 0:
            m = new // old
            if m in self.rules.mults:
                op = f"×{m}"
        # Пробуем деление (округление вниз)
        if op is None and self.rules.divs:
            for d in self.rules.divs:
                if old // d == new:
                    op = f"÷{d}"
                    break
        # Пробуем сдвиг
        if op is None:
            d = new - old
            if d in self.rules.adds:
                op = f"{'+' if d >= 0 else '−'}{abs(d)}"
        if op is None:
            op = f"{old}→{new}"
        return f"на {i + 1}-й куче: {op}"

    def _find_w1_move(self, state: Tuple[int, ...]) -> Optional[Tuple[int, ...]]:
        for nxt in self._moves(state):
            if is_terminal(nxt, self.rules):
                return nxt
        return None

    def _find_w2_witness(
            self, state: Tuple[int, ...], limit_replies: int = 6
    ) -> Optional[Tuple[Tuple[int, ...], List[Tuple[Tuple[int, ...], Tuple[int, ...]]], int]]:
        """
        Найти стратегию выигрыша за 2 собственных хода из 'state' (текущий игрок).
        Возвращает:
          (первый_ход, список_примеров[(ответ_соперника, наш_ход_в_терминал)], всего_ответов_соперника)
        """
        for s1 in self._moves(state):
            opp_moves = self._moves(s1)
            if not opp_moves:
                if is_terminal(s1, self.rules):
                    continue
                return s1, [], 0
            ok_for_all = True
            examples: List[Tuple[Tuple[int, ...], Tuple[int, ...]]] = []
            for s2 in opp_moves:
                win_in_1 = self._find_w1_move(s2)
                if not win_in_1:
                    ok_for_all = False
                    break
                if len(examples) < limit_replies:
                    examples.append((s2, win_in_1))
            if ok_for_all:
                return s1, examples, len(opp_moves)
        return None

    def sample_strategy_19(self, S: int, limit_examples: int = 8) -> Optional[str]:
        start = self._start_from_S(S)
        if self._has_move_to_terminal(start):
            return None
        # Проверяем 19-жёсткое: для всех ходов Пети Ваня выигрывает за 1
        petya_moves = [pm for pm in self._moves(start) if not is_terminal(pm, self.rules)]
        if not petya_moves:
            return None
        if not all(self._find_w1_move(pm) for pm in petya_moves):
            return None
        lines = [f"Старт: {self.fmt_state(start)}",
                 "Для любого хода Пети Ваня выигрывает своим первым ходом. Примеры:"]
        shown = 0
        for pm in petya_moves:
            if shown >= limit_examples:
                break
            v1 = self._find_w1_move(pm)
            lines.append(f"  Петя: {self.describe_move(start, pm)} → {self.fmt_state(pm)}")
            lines.append(f"  Ваня: {self.describe_move(pm, v1)} → {self.fmt_state(v1)} (терминал)")
            shown += 1
        if len(petya_moves) > shown:
            lines.append(f"  … и ещё {len(petya_moves) - shown} ход(а) Пети с аналогичным добиванием Вани.")
        return "\n".join(lines)

    def sample_strategy_20(self, S: int, limit_examples: int = 6) -> Optional[str]:
        start = self._start_from_S(S)
        if self._has_move_to_terminal(start):
            return None
        if not self._can_win_in(start, 2):
            return None
        for p1 in self._moves(start):
            if is_terminal(p1, self.rules):
                continue
            w2 = self._find_w2_witness(p1, limit_replies=limit_examples)
            if not w2:
                continue
            first, examples, total = w2
            lines = []
            lines.append(f"Старт: {self.fmt_state(start)}")
            lines.append(f"Петя (1-й ход): {self.describe_move(start, p1)} → {self.fmt_state(p1)}")
            lines.append("Далее при любом ходе Вани у Пети есть победный 2-й ход. Примеры:")
            shown = 0
            for v1, p2 in examples:
                lines.append(f"  Ваня: {self.describe_move(p1, v1)} → {self.fmt_state(v1)}")
                lines.append(f"  Петя: {self.describe_move(v1, p2)} → {self.fmt_state(p2)} (терминал)")
                shown += 1
            hidden = total - shown
            if hidden > 0:
                lines.append(f"  … и ещё {hidden} вариантов ответов Вани, при которых Петя выигрывает вторым ходом.")
            return "\n".join(lines)
        return None

    def sample_strategy_21(self, S: int, limit_examples: int = 6) -> Optional[str]:
        start = self._start_from_S(S)
        for pm in self._moves(start):
            if is_terminal(pm, self.rules):
                continue
            if self._has_move_to_terminal(pm):
                continue  # нам нужен пример, где Ваня не выигрывает сразу
            if not self._can_win_in(pm, 2):
                continue
            w2 = self._find_w2_witness(pm, limit_replies=limit_examples)
            if not w2:
                continue
            v1, examples, total = w2
            lines = []
            lines.append(f"Старт: {self.fmt_state(start)}")
            lines.append(
                "Покажем ход Пети, после которого Ваня НЕ выигрывает сразу, но выигрывает вторым ходом при любой игре Пети.")
            lines.append(f"Петя: {self.describe_move(start, pm)} → {self.fmt_state(pm)}")
            lines.append(f"Ваня (1-й ход): {self.describe_move(pm, v1)} → {self.fmt_state(v1)} (подготовка)")
            lines.append("Далее при любом ответе Пети Ваня добивает за 2-й ход. Примеры:")
            shown = 0
            for p2, v2 in examples:
                lines.append(f"  Петя: {self.describe_move(v1, p2)} → {self.fmt_state(p2)}")
                lines.append(f"  Ваня: {self.describe_move(p2, v2)} → {self.fmt_state(v2)} (терминал)")
                shown += 1
            hidden = total - shown
            if hidden > 0:
                lines.append(f"  … и ещё {hidden} вариантов ответов Пети, при которых Ваня выигрывает вторым ходом.")
            return "\n".join(lines)
        return None

    # ---------- Перебор ----------
    def solve_all(
            self,
            progress_cb: Optional[Callable[[int, int], None]] = None,
            cancel_cb: Optional[Callable[[], bool]] = None,
    ) -> Tuple[List[int], List[int], List[int]]:
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

            # 19: Петя не выигрывает за 1; для любого хода Пети Ваня выигрывает за 1
            w1_petya = self._has_move_to_terminal(start)
            petya_moves = [pm for pm in self._moves(start) if not is_terminal(pm, self.rules)]
            all_vanya_w1 = bool(petya_moves) and all(self._has_move_to_terminal(pm) for pm in petya_moves)
            if (not w1_petya) and all_vanya_w1:
                s_list_19.append(S)

            # 20: Петя не выигрывает за 1; выигрывает своим вторым при любой игре Вани
            w2_petya = self._can_win_in(start, 2)
            if (not w1_petya) and w2_petya:
                s_list_20.append(S)

            # 21: у Вани W2 при любой игре Пети; и нет гарантии W1
            petya_moves_all = self._moves(start)
            if any(is_terminal(pm, self.rules) for pm in petya_moves_all):
                ok_21 = False
            else:
                all_vanya_w2 = all(self._can_win_in(pm, 2) for pm in petya_moves_all)
                exists_not_w1 = any(not self._has_move_to_terminal(pm) for pm in petya_moves_all)
                ok_21 = all_vanya_w2 and exists_not_w1
            if ok_21:
                s_list_21.append(S)

        return s_list_19, s_list_20, s_list_21
