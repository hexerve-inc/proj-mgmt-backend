from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db, require_permission
from schemas.program import ProgramCreate, ProgramResponse, ProgramUpdate
from services.program_service import ProgramService

router = APIRouter()

@router.post("/", response_model=ProgramResponse, dependencies=[Depends(require_permission("programs:create"))])
def create_program(program_in: ProgramCreate, db: Session = Depends(get_db)):
    service = ProgramService(db)
    return service.create_program(program_in)

@router.get("/", response_model=list[ProgramResponse], dependencies=[Depends(require_permission("programs:read"))])
def get_programs(db: Session = Depends(get_db)):
    service = ProgramService(db)
    return service.get_programs()

@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(
    program_id: str, 
    db: Session = Depends(get_db),
    checker = Depends(require_permission("programs:read"))
):
    checker.check_scope("program", program_id)
    service = ProgramService(db)
    program = service.get_program(program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program
