class Outer:
    def method_a(self):
        def closure(x):
            return x
        return closure(1)


def top():
    return 1
