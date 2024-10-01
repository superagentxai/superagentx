from typing import Self


class TestOpeOver:

    def __init__(self, name: str):
        self.name = name
        self._head: Self | None = None
        self._next: Self | None = None
        self._parallel: Self | None = None

    def clean(self):
        self._next = None
        self._parallel = None

    # def clean_all(self):
    #     _nodes = []
    #     while self._parallel

    def __repr__(self):
        return (
            f"Engine(Name={self.name},"
            f" Next={self._next},"
            f" Parallel={self._parallel})"
            # f" Head={self._head})"
        )

    def __add__(self, other: Self):
        if self.name != other.name:
            # print("Name => ", self.name, " Parallel => ", other)
            if self._parallel:
                self._parallel + other
            else:
                self._parallel = other
                # other._head = self._head
        return self

    def __radd__(self, other: Self):
        if self.name != other.name:
            other + self
        return self

    def __rshift__(self, other: Self):
        if self.name != other.name:
            # print("Name => ", self.name, " Next => ", other)
            if self._next:
                self._next >> other
            else:
                self._next = other
                # other._head = self
            return self

    def __rrshift__(self, other):
        if self.name != other.name:
            other >> self
        return self


# class ParallelOpeOver(Iterable[TestOpeOver]):
#
#     def __init__(self):
#         self._next: Self | TestOpeOver | None = None
#
#     def __iter__(self):
#         self.__init__()
#
#     def __rshift__(self, other: Self | TestOpeOver):
#         # print("Name => ", self.name, " Next => ", other)
#         if self._next:
#             self._next >> other
#         else:
#             self._next = other
#         return self

    # def __rrshift__(self, other):
    #     other >> self
    #     return other


# class ParTestOpeOver(list[TestOpeOver]):
#
#     # def __init__(
#     #         self,
#     #         *args: TestOpeOver
#     # ):
#     #     self._iters = args
#     #     self._next: Self | TestOpeOver | None = None
#     #     super().__init__()
#
#     # def __iter__(self):
#     #     return iter(self._iters)
#
#     def __rshift__(self, other: Self | TestOpeOver):
#         if self._next:
#             self._next >> other
#         else:
#             self._next = other
#         return self

# def test(n):
#     print("Wait for => ", n)
#     time.sleep(n)
#     print(f"Wait for {n} ended!")
#
#
# async def main():
#     await asyncio.gather(
#         asyncio.to_thread(test, 5),
#         asyncio.to_thread(test, 3)
#     )


# if __name__ == '__main__':
#     asyncio.run(
#         main()
#     )
