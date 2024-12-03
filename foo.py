import datetime

def gen(s: datetime.date, e: datetime.date) -> datetime.date:
    while s <= e:
        yield s
        s += datetime.timedelta(days=1)

A = datetime.date(2024, 11, 25)
B = datetime.date(2024, 12, 2)

for d in gen(A, B):
    print(f'old {d}')

print(f'{(B-A).days}')
for d in (A + datetime.timedelta(days=d) for d in range((B-A).days + 1)):
    print(f'new {d}')

