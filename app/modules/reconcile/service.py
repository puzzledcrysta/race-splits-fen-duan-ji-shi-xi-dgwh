from decimal import Decimal
from .ledger import ledger

CLAIMED = ('ZERO_CLAIM', 'KEY_VERIFIED')


def stripped(key):
    # 外部账可能漏抄前导零：纯数字键按去零形式归组，其余键只认原号
    if key.isascii() and key.isdigit():
        return key.lstrip('0') or '0'
    return key


def row(key, amount, line, book_key, reference, book_line, code, candidates=()):
    delta = (amount or Decimal(0)) - (reference or Decimal(0))
    return {'key': key, 'book_key': book_key,
            'amount': str(amount) if amount is not None else None,
            'reference': str(reference) if reference is not None else None,
            'delta': str(delta), 'line': line, 'book_line': book_line,
            'code': code, 'candidates': list(candidates)}


def summarize(rows):
    matched = sum(1 for item in rows if item['code'] == 'MATCH' or
                  (item['code'] in CLAIMED and not Decimal(item['delta'])))
    pending = sum(1 for item in rows if item['code'] == 'KEY_AMBIGUOUS' and item['book_key'] is not None)
    return {'matched': matched, 'mismatched': len(rows) - matched, 'pending': pending}


def compare(accepted, payload):
    expected = ledger(payload)
    actual = {item['key']: (Decimal(item['amount']), item['line']) for item in accepted}
    groups = {}
    for side, keys in ((0, actual), (1, expected)):
        for key in keys:
            groups.setdefault(stripped(key), (set(), set()))[side].add(key)
    rows = []
    for tag in sorted(groups):
        cards, books = (sorted(side) for side in groups[tag])
        if len(cards) <= 1 and len(books) <= 1:
            card, book = (side[0] if side else None for side in (cards, books))
            amount, line = actual.get(card, (None, None))
            reference, book_line = expected.get(book, (None, None))
            if book is None:
                code = 'MISSING_BOOK'
            elif card is None:
                code = 'MISSING_RESULT'
            elif card != book:
                code = 'ZERO_CLAIM'
            else:
                code = 'AMOUNT_DELTA' if amount - reference else 'MATCH'
            rows.append(row(card or book, amount, line, book, reference, book_line, code))
        else:
            # 同组多张计时卡或多笔外部账：归属无法自动判定，整组留待裁判核实
            for card in cards:
                amount, line = actual[card]
                rows.append(row(card, amount, line, None, None, None, 'KEY_AMBIGUOUS', books))
            for book in books:
                reference, book_line = expected[book]
                rows.append(row(book, None, None, book, reference, book_line, 'KEY_AMBIGUOUS', cards))
    rows.sort(key=lambda item: item['key'])
    actual_total = sum((pair[0] for pair in actual.values()), Decimal(0))
    book_total = sum((pair[0] for pair in expected.values()), Decimal(0))
    return {'rows': rows, **summarize(rows), 'actual': str(actual_total),
            'expected': str(book_total), 'delta': str(actual_total - book_total)}
