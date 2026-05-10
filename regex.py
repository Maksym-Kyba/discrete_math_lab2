from __future__ import annotations
from abc import ABC, abstractmethod


class State(ABC):

    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def check_self(self, char: str) -> bool:
        """
        function checks whether occured character is handled by current ctate
        """
        pass

    def check_next(self, next_char: str) -> State | Exception:
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        raise NotImplementedError("rejected string")


class StartState(State):
    next_states: list[State] = []

    def __init__(self):
        super().__init__()

    def check_self(self, char):
        return super().check_self(char)

class TerminationState(State):
    next_states: list[State] = []

    def __init__(self):
        self.next_states = []

    def check_self(self, char: str) -> bool:
        return False

class DotState(State):
    """
    state for . character (any character accepted)
    """

    next_states: list[State] = []

    def __init__(self):
        super().__init__()

    def check_self(self, char: str) -> bool:
        return len(char) == 1

class AsciiState(State):
    """
    state for alphabet letters or numbers
    """
    next_states: list[State] = []
    curr_sym = ""

    def __init__(self, symbol: str) -> None:
        self.next_states = []
        self.curr_sym = symbol

    def check_self(self, curr_char: str) -> bool:
        return curr_char == self.curr_sym

class StarState(State):
    next_states: list[State] = []

    def __init__(self, checking_state: State):
        self.next_states = []
        self._inner = checking_state

    def check_self(self, char: str) -> bool:
        return self._inner.check_self(char)


class PlusState(State):
    next_states: list[State] = []

    def __init__(self, checking_state: State):
        self.next_states = []
        self._inner = checking_state

    def check_self(self, char: str) -> bool:
        return self._inner.check_self(char)


class RegexFSM:
    curr_state: State = StartState()

    def __init__(self, regex_expr: str) -> None:
        self.curr_state = StartState()

        prev_state = self.curr_state
        tmp_next_state = self.curr_state

        for char in regex_expr:
            tmp_next_state = self.__init_next_state(char, prev_state, tmp_next_state)
            prev_state = tmp_next_state

        prev_state.next_states.append(TerminationState())

    def __init_next_state(
        self, next_token: str, prev_state: State, tmp_next_state: State
    ) -> State:
        new_state = None
        match next_token:
            case next_token if next_token == ".":
                new_state = DotState()
                prev_state.next_states.append(new_state)

            case next_token if next_token == "*":
                new_state = StarState(tmp_next_state)
                parent = self._find_parent(tmp_next_state)
                if parent and tmp_next_state in parent.next_states:
                    parent.next_states.remove(tmp_next_state)
                    parent.next_states.append(new_state)
                new_state.next_states.append(new_state)

            case next_token if next_token == "+":
                new_state = PlusState(tmp_next_state)
                tmp_next_state.next_states.append(new_state)
                new_state.next_states.append(new_state)

            case next_token if next_token.isascii():
                new_state = AsciiState(next_token)
                prev_state.next_states.append(new_state)

            case _:
                raise AttributeError("Character is not supported")

        return new_state

    def _find_parent(self, needle: State) -> State | None:
        """BFS від початкового стану — шукаємо батька для needle."""
        seen: set[int] = set()
        queue = [self.curr_state]
        while queue:
            node = queue.pop(0)
            uid = id(node)
            if uid in seen:
                continue
            seen.add(uid)
            if needle in node.next_states:
                return node
            for child in node.next_states:
                if child is not node:
                    queue.append(child)
        return None

    def _e_expand(self, active: set[State]) -> set[State]:
        """
        Проходить по е-стрілках від кожного активного стану.
        StarState та PlusState мають е-стрілки до своїх наступників —
        вони досяжні без споживання символу.
        """
        expanded = set(active)
        stack = list(active)
        while stack:
            st = stack.pop()
            if isinstance(st, (StarState, PlusState)):
                for nxt in st.next_states:
                    if nxt is not st and nxt not in expanded:
                        expanded.add(nxt)
                        stack.append(nxt)
        return expanded

    def check_string(self, input_string: str) -> bool:
        """
        Симуляція НКА методом підмножин (powerset simulation).

        Одночасно відстежуємо всі активні стани. Після кожного символу
        обчислюємо нову множину і виконуємо епсилон-замикання.
        Рядок прийнятий, якщо після останнього символу TerminationState
        міститься в активній множині.
        """
        current = self._e_expand(set(self.curr_state.next_states))

        for ch in input_string:
            following: set[State] = set()

            for st in current:
                if isinstance(st, TerminationState):
                    continue
                if st.check_self(ch):
                    for successor in st.next_states:
                        following.add(successor)
                    if isinstance(st, (StarState, PlusState)):
                        following.add(st)

            if not following:
                return False

            current = self._e_expand(following)

        return any(isinstance(st, TerminationState) for st in current)


if __name__ == "__main__":
    regex_pattern = "a*4.+hi"

    regex_compiled = RegexFSM(regex_pattern)

    print(regex_compiled.check_string("aaaaaa4uhi"))  # True
    print(regex_compiled.check_string("4uhi"))  # True
    print(regex_compiled.check_string("meow"))  # False
