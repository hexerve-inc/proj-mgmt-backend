from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session

from models.task import Task
from models.user import User
from models.project import Project, ProjectStatus
from models.workflow_status import WorkflowStatus, WorkflowGroup


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    # ── helpers ──────────────────────────────────────────────────────
    def _closed_condition(self):
        """Sub-query fragment: status group_key == CLOSED."""
        return WorkflowStatus.group_key == WorkflowGroup.CLOSED

    def _active_condition(self):
        """Sub-query fragment: status group_key NOT CLOSED."""
        return WorkflowStatus.group_key != WorkflowGroup.CLOSED

    def _in_progress_condition(self):
        return WorkflowStatus.group_key == WorkflowGroup.IN_PROGRESS

    def _overdue_condition(self):
        """Task is overdue: not closed AND due_date < today."""
        today = date.today()
        return and_(
            WorkflowStatus.group_key != WorkflowGroup.CLOSED,
            Task.due_date.isnot(None),
            Task.due_date < today,
        )

    def _base_task_query(self):
        """Base query joining Task → WorkflowStatus, excluding soft-deleted."""
        return (
            self.db.query(Task)
            .join(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(Task.deleted_at.is_(None))
        )

    # ── tasks-per-user ──────────────────────────────────────────────
    def get_tasks_per_user(
        self,
        project_id: Optional[str] = None,
        include_unassigned: bool = False,
    ) -> list[dict]:
        today = date.today()

        q = (
            self.db.query(
                User.id.label("user_id"),
                User.name.label("user_name"),
                User.email.label("user_email"),
                func.count(Task.id).label("total_tasks"),
                func.sum(
                    case((self._closed_condition(), 1), else_=0)
                ).label("completed_tasks"),
                func.sum(
                    case((self._active_condition(), 1), else_=0)
                ).label("active_tasks"),
                func.sum(
                    case(
                        (
                            and_(
                                WorkflowStatus.group_key != WorkflowGroup.CLOSED,
                                Task.due_date.isnot(None),
                                Task.due_date < today,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("overdue_tasks"),
            )
            .outerjoin(
                Task,
                and_(
                    Task.assignee_id == User.id,
                    Task.deleted_at.is_(None),
                ),
            )
            .outerjoin(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(User.deleted_at.is_(None))
        )

        if project_id:
            q = q.filter(Task.project_id == project_id)

        q = q.group_by(User.id, User.name, User.email)
        rows = q.all()

        results = [
            {
                "user_id": r.user_id,
                "user_name": r.user_name,
                "user_email": r.user_email,
                "total_tasks": int(r.total_tasks or 0),
                "completed_tasks": int(r.completed_tasks or 0),
                "active_tasks": int(r.active_tasks or 0),
                "overdue_tasks": int(r.overdue_tasks or 0),
            }
            for r in rows
        ]

        if include_unassigned:
            unassigned_q = (
                self.db.query(
                    func.count(Task.id).label("total_tasks"),
                    func.sum(
                        case((self._closed_condition(), 1), else_=0)
                    ).label("completed_tasks"),
                    func.sum(
                        case((self._active_condition(), 1), else_=0)
                    ).label("active_tasks"),
                    func.sum(
                        case(
                            (
                                and_(
                                    WorkflowStatus.group_key != WorkflowGroup.CLOSED,
                                    Task.due_date.isnot(None),
                                    Task.due_date < today,
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("overdue_tasks"),
                )
                .join(WorkflowStatus, Task.status_id == WorkflowStatus.id)
                .filter(Task.deleted_at.is_(None), Task.assignee_id.is_(None))
            )
            if project_id:
                unassigned_q = unassigned_q.filter(Task.project_id == project_id)
            ur = unassigned_q.first()
            if ur and (ur.total_tasks or 0) > 0:
                results.append(
                    {
                        "user_id": "unassigned",
                        "user_name": "Unassigned",
                        "user_email": "",
                        "total_tasks": int(ur.total_tasks or 0),
                        "completed_tasks": int(ur.completed_tasks or 0),
                        "active_tasks": int(ur.active_tasks or 0),
                        "overdue_tasks": int(ur.overdue_tasks or 0),
                    }
                )

        return results

    # ── tasks-per-project ───────────────────────────────────────────
    def get_tasks_per_project(self) -> list[dict]:
        today = date.today()

        rows = (
            self.db.query(
                Project.id.label("project_id"),
                Project.name.label("project_name"),
                Project.project_key.label("project_key"),
                func.count(Task.id).label("total_tasks"),
                func.sum(
                    case((self._closed_condition(), 1), else_=0)
                ).label("completed_tasks"),
                func.sum(
                    case((self._active_condition(), 1), else_=0)
                ).label("active_tasks"),
                func.sum(
                    case(
                        (
                            and_(
                                WorkflowStatus.group_key != WorkflowGroup.CLOSED,
                                Task.due_date.isnot(None),
                                Task.due_date < today,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("overdue_tasks"),
            )
            .outerjoin(Task, and_(Task.project_id == Project.id, Task.deleted_at.is_(None)))
            .outerjoin(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(Project.deleted_at.is_(None))
            .group_by(Project.id, Project.name, Project.project_key)
            .all()
        )

        return [
            {
                "project_id": r.project_id,
                "project_name": r.project_name,
                "project_key": r.project_key,
                "total_tasks": int(r.total_tasks or 0),
                "completed_tasks": int(r.completed_tasks or 0),
                "active_tasks": int(r.active_tasks or 0),
                "overdue_tasks": int(r.overdue_tasks or 0),
                "completion_percentage": round(
                    (int(r.completed_tasks or 0) / int(r.total_tasks or 1)) * 100, 1
                )
                if int(r.total_tasks or 0) > 0
                else 0.0,
            }
            for r in rows
        ]

    # ── tasks-by-due-date ───────────────────────────────────────────
    def get_tasks_by_due_date(self, target_date: date) -> list[dict]:
        rows = (
            self.db.query(Task, User, Project, WorkflowStatus)
            .outerjoin(User, Task.assignee_id == User.id)
            .join(Project, Task.project_id == Project.id)
            .join(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(Task.deleted_at.is_(None), Task.due_date == target_date)
            .all()
        )

        return [
            {
                "task_id": task.id,
                "task_code": task.task_code,
                "title": task.title,
                "assignee_name": user.name if user else None,
                "assignee_id": user.id if user else None,
                "project_name": project.name,
                "project_id": project.id,
                "priority": task.priority.value if task.priority else None,
                "status_group": ws.group_key.value if ws.group_key else None,
                "status_name": ws.name,
                "due_date": task.due_date,
            }
            for task, user, project, ws in rows
        ]

    # ── user-workload ───────────────────────────────────────────────
    def get_user_workload(self, project_id: Optional[str] = None) -> list[dict]:
        q = (
            self.db.query(
                User.id.label("user_id"),
                User.name.label("user_name"),
                User.email.label("user_email"),
                func.count(Task.id).label("active_task_count"),
            )
            .outerjoin(
                Task,
                and_(
                    Task.assignee_id == User.id,
                    Task.deleted_at.is_(None),
                ),
            )
            .outerjoin(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(
                User.deleted_at.is_(None),
            )
        )

        # Only count non-closed tasks
        q = q.filter(
            (WorkflowStatus.group_key != WorkflowGroup.CLOSED)
            | (WorkflowStatus.group_key.is_(None))
        )

        if project_id:
            q = q.filter(Task.project_id == project_id)

        rows = (
            q.group_by(User.id, User.name, User.email)
            .order_by(func.count(Task.id).desc())
            .all()
        )

        return [
            {
                "user_id": r.user_id,
                "user_name": r.user_name,
                "user_email": r.user_email,
                "active_task_count": int(r.active_task_count or 0),
            }
            for r in rows
        ]

    # ── summary ─────────────────────────────────────────────────────
    def get_summary(self) -> dict:
        today = date.today()

        total_users = (
            self.db.query(func.count(User.id))
            .filter(User.deleted_at.is_(None))
            .scalar()
            or 0
        )

        # Users with at least one active task
        users_with_active = (
            self.db.query(func.count(func.distinct(Task.assignee_id)))
            .join(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(
                Task.deleted_at.is_(None),
                Task.assignee_id.isnot(None),
                WorkflowStatus.group_key != WorkflowGroup.CLOSED,
            )
            .scalar()
            or 0
        )
        users_with_no_active_tasks = total_users - users_with_active

        # Total active tasks (for avg calculation)
        total_active_tasks = (
            self.db.query(func.count(Task.id))
            .join(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(
                Task.deleted_at.is_(None),
                Task.assignee_id.isnot(None),
                WorkflowStatus.group_key != WorkflowGroup.CLOSED,
            )
            .scalar()
            or 0
        )
        avg_active = round(total_active_tasks / total_users, 1) if total_users > 0 else 0.0

        # Project counts
        total_projects = (
            self.db.query(func.count(Project.id))
            .filter(Project.deleted_at.is_(None))
            .scalar()
            or 0
        )
        active_projects = (
            self.db.query(func.count(Project.id))
            .filter(
                Project.deleted_at.is_(None),
                Project.status == ProjectStatus.ACTIVE,
            )
            .scalar()
            or 0
        )
        completed_projects = (
            self.db.query(func.count(Project.id))
            .filter(
                Project.deleted_at.is_(None),
                Project.status == ProjectStatus.COMPLETED,
            )
            .scalar()
            or 0
        )

        # Task counts
        total_tasks = (
            self.db.query(func.count(Task.id))
            .filter(Task.deleted_at.is_(None))
            .scalar()
            or 0
        )
        completed_tasks = (
            self.db.query(func.count(Task.id))
            .join(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(
                Task.deleted_at.is_(None),
                WorkflowStatus.group_key == WorkflowGroup.CLOSED,
            )
            .scalar()
            or 0
        )
        overdue_tasks = (
            self.db.query(func.count(Task.id))
            .join(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(
                Task.deleted_at.is_(None),
                WorkflowStatus.group_key != WorkflowGroup.CLOSED,
                Task.due_date.isnot(None),
                Task.due_date < today,
            )
            .scalar()
            or 0
        )
        tasks_in_progress = (
            self.db.query(func.count(Task.id))
            .join(WorkflowStatus, Task.status_id == WorkflowStatus.id)
            .filter(
                Task.deleted_at.is_(None),
                WorkflowStatus.group_key == WorkflowGroup.IN_PROGRESS,
            )
            .scalar()
            or 0
        )

        return {
            "total_users": total_users,
            "users_with_no_active_tasks": users_with_no_active_tasks,
            "avg_active_tasks_per_user": avg_active,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "tasks_in_progress": tasks_in_progress,
        }
