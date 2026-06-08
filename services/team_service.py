from sqlalchemy.orm import Session
from models.team import Team, team_members
from models.user import User
from models.project import Project
from schemas.team import TeamCreate, TeamUpdate
from typing import Optional, List

class TeamService:
    def __init__(self, db: Session):
        self.db = db

    def create_team(self, team_in: TeamCreate) -> Team:
        data = team_in.model_dump(exclude={"member_ids", "project_ids"})
        team = Team(**data)
        
        if team_in.member_ids:
            members = self.db.query(User).filter(User.id.in_(team_in.member_ids)).all()
            team.members = members
            
        if team_in.project_ids:
            projects = self.db.query(Project).filter(Project.id.in_(team_in.project_ids)).all()
            team.projects = projects

        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def get_teams(self) -> list[Team]:
        return self.db.query(Team).filter(Team.deleted_at.is_(None)).all()

    def get_team(self, team_id: str) -> Optional[Team]:
        return self.db.query(Team).filter(Team.id == team_id, Team.deleted_at.is_(None)).first()

    def update_team(self, team_id: str, team_in: TeamUpdate) -> Optional[Team]:
        team = self.get_team(team_id)
        if not team:
            return None
        
        update_data = team_in.model_dump(exclude_unset=True, exclude={"member_ids", "project_ids"})
        for field, value in update_data.items():
            setattr(team, field, value)
            
        if team_in.member_ids is not None:
            members = self.db.query(User).filter(User.id.in_(team_in.member_ids)).all()
            team.members = members
            
        if team_in.project_ids is not None:
            projects = self.db.query(Project).filter(Project.id.in_(team_in.project_ids)).all()
            team.projects = projects
            
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

    def remove_member(self, team_id: str, user_id: str) -> Optional[Team]:
        team = self.get_team(team_id)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not team or not user:
            return None

        if user in team.members:
            team.members.remove(user)
            self.db.commit()
            self.db.refresh(team)
        return team

    def delete_team(self, team_id: str) -> bool:
        team = self.get_team(team_id)
        if not team:
            return False
            
        team.soft_delete()
        self.db.commit()
        return True
