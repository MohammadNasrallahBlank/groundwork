def build():
    out = []
    for i in range(5):
        out.append(lambda: i)          # classic late-binding closure gotcha
    return [f() for f in out]


print(build())
