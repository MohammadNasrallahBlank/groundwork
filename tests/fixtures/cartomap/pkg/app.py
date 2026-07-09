from pkg.util import Formatter, helper


class App:
    def run(self):
        f = Formatter()
        return f.format(helper(41))


def main():
    return App().run()
