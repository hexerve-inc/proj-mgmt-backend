from sqlalchemy.orm import Session
from models.team import Team, team_members
from models.user import User
from schemas.team import TeamCreate, TeamUpdate
from typing import Optional

class TeamService:
    def __init__(self, db: Session):
        self.db = db

    def create_team(self, team_in: TeamCreate) -> Team:
        team = Team(**team_in.model_dump())
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def get_teams(self) -> list[Team]:
        return self.db.query(Team).all()

    def get_team(self, team_id: str) -> Optional[Team]:
        return self.db.query(Team).filter(Team.id == team_id).first()

    def update_team(self, team_id: str, team_in: TeamUpdate) -> Optional[Team]:
        team = self.get_team(team_id)
        if not team:
            return None
        
        update_data = team_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)
            
        self.db.commit()
        self.db.refresh(team)
        return team

    def add_member(self, team_id: str, user_id: str) -> Optional[Team]:
        team = self.get_team(team_id)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not team or not user:
            return None
            
        if user not in team.members:
            team.members.append(user)
            self.db.commit()
            self.db.refresh(team)
        return team
