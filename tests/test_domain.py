from decimal import Decimal
import pytest
from app.errors import DataError
from app.modules.domain.rule import evaluate


def test_backtrack(cases):
    # TRAP-13
    actual, proof = evaluate(cases['backtrack'])
    assert actual == Decimal('120')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['终点 · 时刻 120'])) == Decimal('60')


def test_fastest_valid(cases):
    actual, proof = evaluate(cases['fastest_valid'])
    assert actual == Decimal('122')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['起点 · 时刻 8'])) == Decimal('0')


def test_normal(cases):
    actual, proof = evaluate(cases['normal'])
    assert actual == Decimal('200')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['中段 · 时刻 100'])) == Decimal('100')


def test_same_finish(cases):
    # TRAP-19
    actual, proof = evaluate(cases['same_finish'])
    assert actual == Decimal('110')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['半程 · 时刻 40'])) == Decimal('40')


def test_precise(cases):
    actual, proof = evaluate(cases['precise'])
    assert actual == Decimal('119.56')
    assert proof


def test_multi_gate(cases):
    actual, proof = evaluate(cases['multi_gate'])
    assert actual == Decimal('240')
    assert proof


def test_delayed_checkpoint(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['delayed_checkpoint'])
    assert error.value.code == 'RACE_GAP'


def test_unknown_checkpoint(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['unknown_checkpoint'])
    assert error.value.code == 'RACE_READER'


def test_missing_point(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['missing_point'])
    assert error.value.code == 'RACE_GAP'
