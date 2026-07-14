from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db, get_current_user, require_permission, require_any_permission, get_permission_service
from schemas.team import TeamCreate, TeamResponse, TeamUpdate
from models.user import User
from services.team_service import TeamService

router = APIRouter()

@router.post("/", response_model=TeamResponse, dependencies=[Depends(require_permission("teams:create"))])
def create_team(team_in: TeamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TeamService(db)
    return service.create_team(team_in, actor_id=current_user.id)

@router.get("/", response_model=list[TeamResponse], dependencies=[Depends(require_permission("teams:read"))])
def get_teams(db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.get_teams()

@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: str, 
    db: Session = Depends(get_db),
    checker = Depends(require_permission("teams:read"))
):
    checker.check_scope("team", team_id)
    service = TeamService(db)
    team = service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.post("/{team_id}/members/{user_id}", response_model=TeamResponse)
def add_member(
    team_id: str, 
    user_id: str, 
    db: Session = Depends(get_db),
    checker = Depends(require_permission("teams:manage_members"))
):
    checker.check_scope("team", team_id)
    service = TeamService(db)
    team = service.add_member(team_id, user_id)
    if not team:
        raise HTTPException(status_code=400, detail="Team or User not found")
    return team

@router.delete("/{team_id}/members/{user_id}", response_model=TeamResponse)
def remove_member(
    team_id: str, 
    user_id: str, 
    db: Session = Depends(get_db),
    checker = Depends(require_permission("teams:manage_members"))
):
    checker.check_scope("team", team_id)
    service = TeamService(db)
    team = service.remove_member(team_id, user_id)
    if not team:
        raise HTTPException(status_code=400, detail="Team or User not found")
    return team

@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: str, 
    team_in: TeamUpdate, 
    db: Session = Depends(get_db),
    checker = Depends(require_permission("teams:update"))
):
    checker.check_scope("team", team_id)
    service = TeamService(db)
    team = service.update_team(team_id, team_in)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.delete("/{team_id}", dependencies=[Depends(require_any_permission("teams:delete", "teams:delete_own"))])
def delete_team(
    team_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service = Depends(get_permission_service)
):
    service = TeamService(db)
    team = service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    has_global_delete = perm_service.has_permission(current_user.id, "teams:delete", scope_type="team", scope_id=team_id)
    if not has_global_delete:
        if team.created_by_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only delete teams that you created.")

    success = service.delete_team(team_id)
    if not success:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"message": "Team deleted successfully"}
