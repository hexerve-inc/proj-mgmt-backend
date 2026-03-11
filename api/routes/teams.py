from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from schemas.team import TeamCreate, TeamResponse, TeamUpdate
from services.team_service import TeamService

router = APIRouter()

@router.post("/", response_model=TeamResponse)
def create_team(team_in: TeamCreate, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.create_team(team_in)

@router.get("/", response_model=list[TeamResponse])
def get_teams(db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.get_teams()

@router.get("/{team_id}", response_model=TeamResponse)
def get_team(team_id: str, db: Session = Depends(get_db)):
    service = TeamService(db)
    team = service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.post("/{team_id}/members/{user_id}", response_model=TeamResponse)
def add_member(team_id: str, user_id: str, db: Session = Depends(get_db)):
    service = TeamService(db)
    team = service.add_member(team_id, user_id)
    if not team:
        raise HTTPException(status_code=400, detail="Team or User not found")
    return team
