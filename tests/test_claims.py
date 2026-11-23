from decimal import Decimal
import pytest
from app.modules.reconcile.service import compare
from app.settings import KEY, UNIT

HEADER = f'{KEY},外部记录值({UNIT})'
SOURCE = '\n'.join([
    '计时卡,修订号,提交时间,检查点链,读数,原始备注',
    '007,1,2026-11-18T09:30:00+08:00,起点:0:0;终点:10:20,起点:0;终点:15,',
    '7,1,2026-11-18T09:30:00+08:00,起点:0:0;终点:10:20,起点:0;终点:18,',
]).encode()


def book_of(*pairs):
    return '\n'.join([HEADER, *(f'{key},{value}' for key, value in pairs)]).encode()


def accepted(*pairs):
    return [{'key': key, 'line': line + 2, 'amount': value}
            for line, (key, value) in enumerate(pairs)]


def race(client, book):
    return client.post('/api/runs', json={'data': SOURCE.decode(), 'book': book.decode()}).json()


def claim(client, run_id, book_key, card):
    return client.post(f'/api/reconcile/{run_id}/claims', json={'book_key': book_key, 'card': card})


def test_unique_zero_gap_is_claimed():
    result = compare(accepted(('007', '120')), book_of(('7', '120')))
    row, = result['rows']
    assert (row['code'], row['key'], row['book_key'], row['delta']) == ('ZERO_CLAIM', '007', '7', '0')
    assert (result['matched'], result['pending']) == (1, 0)


def test_collision_waits_for_referee():
    result = compare(accepted(('007', '120'), ('7', '55')), book_of(('7', '120')))
    by_key = {row['key']: row for row in result['rows']}
    assert {row['code'] for row in result['rows']} == {'KEY_AMBIGUOUS'}
    assert by_key['7']['book_key'] == '7' and by_key['7']['candidates'] == ['007', '7']
    assert by_key['007']['candidates'] == ['7'] and by_key['007']['amount'] == '120'
    assert (result['matched'], result['pending']) == (0, 1)


def test_exact_pair_without_collision_stays_exact():
    result = compare(accepted(('7', '55')), book_of(('7', '55')))
    row, = result['rows']
    assert (row['code'], row['book_key']) == ('MATCH', '7')


def test_non_digit_keys_keep_identity():
    result = compare(accepted(('A07', '5')), book_of(('A7', '5')))
    assert [row['code'] for row in result['rows']] == ['MISSING_BOOK', 'MISSING_RESULT']


def test_ambiguous_group_keeps_totals_consistent():
    result = compare(accepted(('007', '120'), ('7', '55')), book_of(('7', '120')))
    assert Decimal(result['delta']) == sum(Decimal(row['delta']) for row in result['rows'])
    assert (result['actual'], result['expected']) == ('175', '120')


@pytest.fixture
def anchor(client):
    report = race(client, book_of(('7', '15')))
    assert report['book']['pending'] == 1
    return report['manifest']['run_id']


def test_pending_blocks_signoff(client, anchor):
    response = client.post(f'/api/review/{anchor}',
                           json={'version': 0, 'decision': '确认', 'note': '已核对'})
    assert (response.status_code, response.json()['code']) == (422, 'CLAIM_PENDING')


def test_return_allowed_while_pending(client, anchor):
    response = client.post(f'/api/review/{anchor}',
                           json={'version': 0, 'decision': '退回', 'note': '归属待核'})
    assert response.status_code == 200


def test_verified_claim_unblocks_signoff_and_survives_replay(client, anchor):
    settled = claim(client, anchor, '7', '007')
    assert settled.status_code == 200
    rows = {row['key']: row for row in settled.json()['book']['rows']}
    pair = rows['007']
    assert (pair['code'], pair['book_key'], pair['amount'], pair['reference']) == ('KEY_VERIFIED', '7', '15', '15')
    assert rows['7']['code'] == 'MISSING_BOOK' and settled.json()['book']['pending'] == 0
    signoff = client.post(f'/api/review/{anchor}',
                          json={'version': 0, 'decision': '确认', 'note': '外部账 7 核实为计时卡 007'})
    assert signoff.status_code == 200
    for again in (client.post(f'/api/runs/{anchor}/replay').json(),
                  race(client, book_of(('7', '15')))):
        rows = {row['key']: row for row in again['book']['rows']}
        assert rows['007']['code'] == 'KEY_VERIFIED' and again['book']['pending'] == 0


def test_dismissed_claim_allows_signoff(client, anchor):
    settled = claim(client, anchor, '7', None).json()
    rows = settled['book']['rows']
    dismissed, = [row for row in rows if row['code'] == 'KEY_DISMISSED']
    assert (dismissed['key'], dismissed['book_key'], dismissed['reference']) == ('7', '7', '15')
    missing = {row['key'] for row in rows if row['code'] == 'MISSING_BOOK'}
    assert missing == {'007', '7'} and settled['book']['pending'] == 0
    signoff = client.post(f'/api/review/{anchor}',
                          json={'version': 0, 'decision': '确认', 'note': '外部账此笔与本批无关'})
    assert signoff.status_code == 200


def test_claim_validation(client, anchor):
    unknown = claim(client, anchor, '099', '007')
    assert (unknown.status_code, unknown.json()['code']) == (422, 'CLAIM_UNKNOWN')
    stranger = claim(client, anchor, '7', '008')
    assert (stranger.status_code, stranger.json()['code']) == (422, 'CLAIM_CARD')
    missing_run = claim(client, 'not-found', '7', '007')
    assert (missing_run.status_code, missing_run.json()['code']) == (404, 'RUN_UNKNOWN')


def test_two_books_cannot_claim_same_card(client):
    report = race(client, book_of(('7', '15'), ('07', '18')))
    run_id = report['manifest']['run_id']
    assert report['book']['pending'] == 2
    assert claim(client, run_id, '7', '007').status_code == 200
    conflict = claim(client, run_id, '07', '007')
    assert (conflict.status_code, conflict.json()['code']) == (409, 'CLAIM_CONFLICT')
    assert claim(client, run_id, '07', '7').status_code == 200
    assert client.get(f'/api/runs/{run_id}').json()['book']['pending'] == 0


def test_export_carries_claims(client, anchor):
    assert claim(client, anchor, '7', '007').status_code == 200
    proof = client.get(f'/api/export/{anchor}').json()
    assert [(item['book_key'], item['card']) for item in proof['claims']] == [('7', '007')]
    rows = {row['key']: row for row in proof['reconciliation']['rows']}
    assert rows['007']['code'] == 'KEY_VERIFIED' and rows['007']['book_key'] == '7'
