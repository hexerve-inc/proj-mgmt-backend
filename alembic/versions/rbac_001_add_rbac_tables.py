"""Add RBAC tables: roles, permissions, role_permissions, user_roles, role_audit_log

Revision ID: rbac_001_tables
Revises: b431092c5544
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "rbac_001_tables"
down_revision = "b431092c5544"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── roles ────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("hierarchy_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_roles_slug", "roles", ["slug"], if_not_exists=True)
    op.create_index("idx_roles_deleted_at", "roles", ["deleted_at"], if_not_exists=True)

    # ── permissions ──────────────────────────────────────────────
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_perm_code", "permissions", ["code"], if_not_exists=True)
    op.create_index("idx_perm_module", "permissions", ["module"], if_not_exists=True)

    # ── role_permissions ─────────────────────────────────────────
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("role_id", sa.String(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.String(), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index("idx_rp_role", "role_permissions", ["role_id"], if_not_exists=True)
    op.create_index("idx_rp_perm", "role_permissions", ["permission_id"], if_not_exists=True)

    # ── user_roles ───────────────────────────────────────────────
    op.create_table(
        "user_roles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.String(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope_type", sa.String(20), nullable=False, server_default="global"),
        sa.Column("scope_id", sa.String(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("assigned_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_user_role_user", "user_roles", ["user_id"], if_not_exists=True)
    op.create_index("idx_user_role_role", "user_roles", ["role_id"], if_not_exists=True)
    op.create_index("idx_user_role_scope", "user_roles", ["user_id", "role_id", "scope_type", "scope_id"], if_not_exists=True)
    op.create_index("idx_user_roles_deleted_at", "user_roles", ["deleted_at"], if_not_exists=True)

    # ── role_audit_log ───────────────────────────────────────────
    op.create_table(
        "role_audit_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("role_id", sa.String(), nullable=True),
        sa.Column("scope_type", sa.String(20), nullable=True),
        sa.Column("scope_id", sa.String(), nullable=True),
        sa.Column("old_value", JSONB, nullable=True),
        sa.Column("new_value", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_audit_user_action", "role_audit_log", ["user_id", "action"], if_not_exists=True)
    op.create_index("idx_audit_created", "role_audit_log", ["created_at"], if_not_exists=True)
    op.create_index("idx_audit_actor", "role_audit_log", ["actor_id"], if_not_exists=True)

    # ── Add system_role_id FK to users ───────────────────────────
    op.add_column(
        "users",
        sa.Column("system_role_id", sa.String(), sa.ForeignKey("roles.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "system_role_id")
    op.drop_table("role_audit_log")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
