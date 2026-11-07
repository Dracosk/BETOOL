from fastapi import APIRouter, HTTPException

from backend.app import bankroll as br

router = APIRouter(tags=["bankroll"])


@router.get("/bankroll")
def get_bankroll():
    return br.read_bankroll()


@router.post("/bankroll/settle")
def set_settlement(filename: str, index: int, status: str):
    result = br.settle(filename, index, status)
    if result is None:
        raise HTTPException(status_code=400, detail="Estado inválido. Usa: won, lost, void, pending")
    return result


@router.get("/papers")
def list_papers():
    return {"files": br.list_paper_files()}