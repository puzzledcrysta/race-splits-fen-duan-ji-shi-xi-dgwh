from collections import defaultdict
from decimal import Decimal as D
from app.errors import DataError
from .values import number, parts


def evaluate(row):
    chain = []
    for item in parts(row['检查点链']):
        fields = item.split(':')
        if len(fields) != 3 or not fields[0]:
            raise DataError('RACE_CHAIN', '检查点格式为名称:最短分段秒:最长分段秒')
        point, lower, upper = fields
        minimum = number(lower, 0, 86400)
        maximum = number(upper, minimum, 86400)
        chain.append((point, minimum, maximum))
    names = [point for point,_,_ in chain]
    if len(chain) < 2 or len(set(names)) != len(chain) or chain[0][1:] != (0, 0):
        raise DataError('RACE_CHAIN', '检查点须唯一，起点区间为 0:0')
    ticks = defaultdict(set)
    for reading in parts(row['读数']):
        point, sep, value = reading.partition(':')
        if not sep or point not in names:
            raise DataError('RACE_READER', f'读数的检查点未知 {point}')
        ticks[point].add(number(value, 0, 86400))
    candidates = {tick:(tick,) for tick in ticks[names[0]]}
    for point, lower, upper in chain[1:]:
        next_candidates = {}
        for tick in sorted(ticks[point]):
            paths = [path+(tick,) for last,path in candidates.items() if lower <= tick-last <= upper and tick > last]
            if paths:
                next_candidates[tick] = min(paths, key=rank)
        if not next_candidates:
            raise DataError('RACE_GAP', f'{point} 无法接续上一计时点')
        candidates = next_candidates
    if not candidates:
        raise DataError('RACE_GAP', '缺少起点读数')
    best = min(candidates.values(), key=rank)
    proof = [(f'{point} · 时刻 {tick}', tick-best[i-1] if i else D(0), '秒')
             for i,(point,tick) in enumerate(zip(names,best))]
    return best[-1]-best[0], proof


def rank(path):
    return path[-1]-path[0], tuple(b-a for a,b in zip(path,path[1:])), path
