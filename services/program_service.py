from sqlalchemy.orm import Session
from models.program import Program
from schemas.program import ProgramCreate, ProgramUpdate
from typing import Optional

class ProgramService:
    def __init__(self, db: Session):
        self.db = db

    def create_program(self, program_in: ProgramCreate) -> Program:
        program = Program(**program_in.model_dump())
        self.db.add(program)
        self.db.commit()
        self.db.refresh(program)
        return program

    def get_programs(self) -> list[Program]:
        return self.db.query(Program).all()

    def get_program(self, program_id: str) -> Optional[Program]:
        return self.db.query(Program).filter(Program.id == program_id).first()

    def update_program(self, program_id: str, program_in: ProgramUpdate) -> Optional[Program]:
        program = self.get_program(program_id)
        if not program:
            return None
            
        update_data = program_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(program, field, value)
            
        self.db.commit()
        self.db.refresh(program)
        return program
