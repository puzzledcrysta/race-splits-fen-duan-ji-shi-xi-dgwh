import json
from datetime import datetime, timezone
from decimal import Decimal
from app.errors import DataError
from app.store import connection
from app.modules.runs.repository import lookup
from .service import row, summarize


def _claims(db, run_id):
    return {item['book_key']: item['card'] for item in
            db.execute('SELECT book_key,card FROM claims WHERE run_id=?', (run_id,))}


def claimed(run_id):
    with connection() as db:
        lookup(db, run_id)
        return _claims(db, run_id)


def recorded(run_id):
    with connection() as db:
        lookup(db, run_id)
        return [dict(item) for item in db.execute(
            'SELECT book_key,card,decided FROM claims WHERE run_id=? ORDER BY book_key', (run_id,))]


def settle(run_id, report):
    return apply(report, claimed(run_id))


def apply(report, claims):
    # 归属组全部核清后重写为核实结论；仍有未核外部账的组保持待核
    book = report['book']
    ambiguous = [item for item in book['rows'] if item['code'] == 'KEY_AMBIGUOUS']
    if not ambiguous:
        return report
    books = {item['book_key']: item for item in ambiguous if item['book_key'] is not None}
    cards = {item['key']: item for item in ambiguous if item['book_key'] is None}
    parent = {}

    def find(node):
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for book_key, item in books.items():
        for card in item['candidates']:
            parent[find(('book', book_key))] = find(('card', card))
    groups = {}
    for book_key in books:
        groups.setdefault(find(('book', book_key)), {'books': [], 'cards': []})['books'].append(book_key)
    for card in cards:
        groups.setdefault(find(('card', card)), {'books': [], 'cards': []})['cards'].append(card)
    rows = [item for item in book['rows'] if item['code'] != 'KEY_AMBIGUOUS']
    for group in groups.values():
        if any(book_key not in claims for book_key in group['books']):
            rows.extend(books[key] for key in group['books'])
            rows.extend(cards[key] for key in group['cards'])
            continue
        verified = set()
        for book_key in sorted(group['books']):
            item, card = books[book_key], claims[book_key]
            reference = Decimal(item['reference'])
            if card is None:
                rows.append(row(book_key, None, None, book_key, reference, item['book_line'],
                                'KEY_DISMISSED', item['candidates']))
                continue
            target = cards[card]
            verified.add(card)
            rows.append(row(card, Decimal(target['amount']), target['line'], book_key, reference,
                            item['book_line'], 'KEY_VERIFIED', item['candidates']))
        for card in group['cards']:
            if card not in verified:
                item = cards[card]
                rows.append(row(card, Decimal(item['amount']), item['line'], None, None, None,
                                'MISSING_BOOK', item['candidates']))
    rows.sort(key=lambda item: item['key'])
    book['rows'] = rows
    book.update(summarize(rows))
    return report


def decide_claim(run_id, book_key, card):
    book_key = book_key.strip()
    card = card.strip() if card else None
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        run = json.loads(lookup(db, run_id)['result'])
        claims = _claims(db, run_id)
        pending = {item['book_key']: item for item in run['book']['rows']
                   if item['code'] == 'KEY_AMBIGUOUS' and item['book_key'] is not None}
        if book_key not in pending:
            raise DataError('CLAIM_UNKNOWN', '该笔外部账不在待核归属中')
        if card is not None and card not in pending[book_key]['candidates']:
            raise DataError('CLAIM_CARD', '候选归属中无此计时卡')
        if card is not None and any(other != book_key and target == card
                                    for other, target in claims.items()):
            raise DataError('CLAIM_CONFLICT', '该计时卡已被其他外部账认领', 409)
        claims[book_key] = card
        db.execute('INSERT OR REPLACE INTO claims VALUES (?,?,?,?)',
                   (run_id, book_key, card, datetime.now(timezone.utc).isoformat()))
        return apply(run, claims)
