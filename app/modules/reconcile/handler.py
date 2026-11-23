from fastapi import APIRouter
from app.inputs import Paired, Claim
from app.pipeline import execute
from .claims import decide_claim, recorded

router = APIRouter()

@router.post('/api/reconcile')
def reconcile(source: Paired):
    report = execute(source.raw(),source.ledger())
    return {key:report[key] for key in ('book','counts','balanced')}

@router.get('/api/reconcile/{run_id}/claims')
def claims(run_id: str):
    return recorded(run_id)

@router.post('/api/reconcile/{run_id}/claims')
def claim(run_id: str, claim: Claim):
    return decide_claim(run_id,claim.book_key,claim.card)
