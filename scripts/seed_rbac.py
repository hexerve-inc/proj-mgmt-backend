import sys
import os
import uuid
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

# Define all permissions from the matrix
PERMISSIONS = [
    # Projects
    ("projects:create", "projects", "create", "Create projects"),
    ("projects:read", "projects", "read", "Read projects"),
    ("projects:update", "projects", "update", "Update projects"),
    ("projects:delete", "projects", "delete", "Delete projects"),
    ("projects:delete_own", "projects", "delete_own", "Delete own projects"),
    ("projects:archive", "projects", "archive", "Archive projects"),
    ("projects:configure", "projects", "configure", "Configure projects"),
    # Tasks
    ("tasks:create", "tasks", "create", "Create tasks"),
    ("tasks:read", "tasks", "read", "Read tasks"),
    ("tasks:update", "tasks", "update", "Update tasks"),
    ("tasks:update_own", "tasks", "update_own", "Update own tasks"),
    ("tasks:delete", "tasks", "delete", "Delete tasks"),
    ("tasks:delete_own", "tasks", "delete_own", "Delete own tasks"),
    ("tasks:assign", "tasks", "assign", "Assign tasks"),
    ("tasks:move_sprint", "tasks", "move_sprint", "Move sprint"),
    ("tasks:bulk_update", "tasks", "bulk_update", "Bulk update tasks"),
    ("tasks:export", "tasks", "export", "Export tasks"),
    # Sprints
    ("sprints:create", "sprints", "create", "Create sprints"),
    ("sprints:read", "sprints", "read", "Read sprints"),
    ("sprints:update", "sprints", "update", "Update sprints"),
    ("sprints:delete", "sprints", "delete", "Delete sprints"),
    ("sprints:start_complete", "sprints", "start_complete", "Start and complete sprints"),
    # Teams
    ("teams:create", "teams", "create", "Create teams"),
    ("teams:read", "teams", "read", "Read teams"),
    ("teams:update", "teams", "update", "Update teams"),
    ("teams:delete", "teams", "delete", "Delete teams"),
    ("teams:delete_own", "teams", "delete_own", "Delete own teams"),
    ("teams:manage_members", "teams", "manage_members", "Manage team members"),
    # Portfolios
    ("portfolios:create", "portfolios", "create", "Create portfolios"),
    ("portfolios:read", "portfolios", "read", "Read portfolios"),
    ("portfolios:update", "portfolios", "update", "Update portfolios"),
    ("portfolios:delete", "portfolios", "delete", "Delete portfolios"),
    # Programs
    ("programs:create", "programs", "create", "Create programs"),
    ("programs:read", "programs", "read", "Read programs"),
    ("programs:update", "programs", "update", "Update programs"),
    ("programs:delete", "programs", "delete", "Delete programs"),
    # Clients
    ("clients:create", "clients", "create", "Create clients"),
    ("clients:read", "clients", "read", "Read clients"),
    ("clients:update", "clients", "update", "Update clients"),
    ("clients:delete", "clients", "delete", "Delete clients"),
    # Invoices
    ("invoices:create", "invoices", "create", "Create invoices"),
    ("invoices:read", "invoices", "read", "Read invoices"),
    ("invoices:update", "invoices", "update", "Update invoices"),
    ("invoices:approve", "invoices", "approve", "Approve invoices"),
    # Time Entries
    ("time_entries:create", "time_entries", "create", "Create time entries"),
    ("time_entries:read", "time_entries", "read", "Read time entries"),
    ("time_entries:read_own", "time_entries", "read_own", "Read own time entries"),
    ("time_entries:update_own", "time_entries", "update_own", "Update own time entries"),
    ("time_entries:delete_own", "time_entries", "delete_own", "Delete own time entries"),
    ("time_entries:delete", "time_entries", "delete", "Delete time entries"),
    # Attachments
    ("attachments:upload", "attachments", "upload", "Upload attachments"),
    ("attachments:download", "attachments", "download", "Download attachments"),
    ("attachments:delete", "attachments", "delete", "Delete attachments"),
    # Comments
    ("comments:create", "comments", "create", "Create comments"),
    ("comments:read", "comments", "read", "Read comments"),
    ("comments:update_own", "comments", "update_own", "Update own comments"),
    ("comments:delete", "comments", "delete", "Delete comments"),
    # Watchers
    ("watchers:manage_self", "watchers", "manage_self", "Manage own watchers"),
    ("watchers:manage_others", "watchers", "manage_others", "Manage others watchers"),
    # User Management
    ("users:create", "users", "create", "Create users"),
    ("users:read", "users", "read", "Read users"),
    ("users:update", "users", "update", "Update users"),
    ("users:delete", "users", "delete", "Delete users"),
    # Role Management
    ("roles:read", "roles", "read", "Read roles"),
    ("roles:assign", "roles", "assign", "Assign roles"),
    ("roles:create_custom", "roles", "create_custom", "Create custom roles"),
    ("roles:manage", "roles", "manage", "Manage roles"),
    # Workflow Statuses
    ("workflow:create", "workflow", "create", "Create workflow statuses"),
    ("workflow:read", "workflow", "read", "Read workflow statuses"),
    ("workflow:update", "workflow", "update", "Update workflow statuses"),
    ("workflow:delete", "workflow", "delete", "Delete workflow statuses"),
    ("workflow:reorder", "workflow", "reorder", "Reorder workflow statuses"),
    # Custom Filters
    ("filters:create", "filters", "create", "Create filters"),
    ("filters:read_own", "filters", "read_own", "Read own filters"),
    ("filters:update_own", "filters", "update_own", "Update own filters"),
    ("filters:delete_own", "filters", "delete_own", "Delete own filters"),
    # Analytics & Reports
    ("analytics:read", "analytics", "read", "Read analytics"),
    ("analytics:export", "analytics", "export", "Export analytics"),
    ("analytics:advanced", "analytics", "advanced", "Advanced analytics"),
    # Notifications
    ("notifications:read_own", "notifications", "read_own", "Read own notifications"),
    ("notifications:configure_own", "notifications", "configure_own", "Configure own notifications"),
    # Settings
    ("settings:read", "settings", "read", "Read settings"),
    ("settings:update", "settings", "update", "Update settings"),
    # AI Copilot
    ("ai:use", "ai", "use", "Use AI copilot"),
    ("ai:configure", "ai", "configure", "Configure AI copilot"),
]

# Define roles
ROLES = [
    ("super_admin", "Super Admin", "Global", 0),
    ("org_admin", "Org Admin", "Organization", 1),
    ("portfolio_mgr", "Portfolio Manager", "Portfolio", 2),
    ("program_mgr", "Program Manager", "Program", 3),
    ("project_admin", "Project Admin", "Project", 4),
    ("project_mgr", "Project Manager", "Project", 5),
    ("team_lead", "Team Lead", "Project", 6),
    ("developer", "Developer", "Project", 7),
    ("qa_engineer", "QA Engineer", "Project", 8),
    ("reporter", "Reporter", "Project", 9),
    ("client", "Client", "Project", 10),
    ("viewer", "Viewer", "Project", 11),
]

# Role to permission mapping
ROLE_PERMS = {
    "super_admin": ["*"],
    "org_admin": ["*"],
    "project_mgr": [
        "projects:create", "projects:read", "projects:update", "projects:delete_own", "projects:archive", "projects:configure",
        "tasks:create", "tasks:read", "tasks:update", "tasks:update_own", "tasks:delete", "tasks:assign", "tasks:move_sprint", "tasks:bulk_update", "tasks:export",
        "sprints:create", "sprints:read", "sprints:update", "sprints:delete", "sprints:start_complete",
        "teams:create", "teams:read", "teams:update", "teams:delete_own", "teams:manage_members",
        "portfolios:read", "programs:read", "clients:read",
        "invoices:create", "invoices:read", "invoices:update",
        "time_entries:create", "time_entries:read", "time_entries:read_own", "time_entries:update_own", "time_entries:delete",
        "attachments:upload", "attachments:download", "attachments:delete",
        "comments:create", "comments:read", "comments:update_own", "comments:delete",
        "watchers:manage_self", "watchers:manage_others",
        "users:read", "workflow:create", "workflow:read", "workflow:update", "workflow:delete", "workflow:reorder",
        "filters:create", "filters:read_own", "filters:update_own", "filters:delete_own",
        "analytics:read", "analytics:export",
        "notifications:read_own", "notifications:configure_own",
        "settings:read",
        "ai:use"
    ],
    "developer": [
        "projects:read",
        "tasks:create", "tasks:read", "tasks:update", "tasks:update_own", "tasks:delete_own", "tasks:assign",
        "sprints:read",
        "teams:create", "teams:read", "teams:update", "teams:delete", "teams:manage_members",
        "time_entries:create", "time_entries:read_own", "time_entries:update_own", "time_entries:delete_own",
        "attachments:upload", "attachments:download", "attachments:delete",
        "comments:create", "comments:read", "comments:update_own", "comments:delete",
        "watchers:manage_self",
        "users:read", "workflow:read",
        "portfolios:read", "programs:read", "clients:read", "invoices:read", "analytics:read",
        "filters:create", "filters:read_own", "filters:update_own", "filters:delete_own",
        "notifications:read_own", "notifications:configure_own",
        "ai:use"
    ],
    "viewer": [
        "projects:read", "tasks:read", "sprints:read", "workflow:read",
        "attachments:download", "comments:read", "watchers:manage_self",
        "filters:create", "filters:read_own", "filters:update_own", "filters:delete_own",
        "notifications:read_own", "notifications:configure_own"
    ]
}

def seed_rbac_from_connection(conn):
    """
    Seed RBAC roles, permissions, and mappings using SQLAlchemy Core.
    Safe to call from Alembic migrations because it does not use ORM sessions.
    Also handles mapping existing users to their new roles safely.
    """
    print("Seeding RBAC schema using connection...")
    
    # 1. Seed Permissions
    perm_map = {}
    for code, mod, act, desc in PERMISSIONS:
        existing = conn.execute(
            text("SELECT id FROM permissions WHERE code = :code"), 
            {"code": code}
        ).fetchone()
        
        if existing:
            perm_map[code] = existing[0]
        else:
            perm_id = str(uuid.uuid4())
            conn.execute(
                text("""
                    INSERT INTO permissions (id, code, module, action, description, created_at) 
                    VALUES (:id, :code, :mod, :act, :desc, :now)
                """),
                {"id": perm_id, "code": code, "mod": mod, "act": act, "desc": desc, "now": datetime.now(timezone.utc)}
            )
            perm_map[code] = perm_id

    # 2. Seed Roles
    role_map = {}
    for slug, name, scope, level in ROLES:
        existing = conn.execute(
            text("SELECT id FROM roles WHERE slug = :slug"), 
            {"slug": slug}
        ).fetchone()
        
        if existing:
            role_map[slug] = existing[0]
        else:
            role_id = str(uuid.uuid4())
            conn.execute(
                text("""
                    INSERT INTO roles (id, name, slug, description, is_system, is_active, hierarchy_level, created_at, updated_at) 
                    VALUES (:id, :name, :slug, :desc, true, true, :level, :now, :now)
                """),
                {"id": role_id, "name": name, "slug": slug, "desc": f"{name} role", "level": level, "now": datetime.now(timezone.utc)}
            )
            role_map[slug] = role_id
            
    # 3. Seed Role-Permissions
    for slug, perms in ROLE_PERMS.items():
        role_id = role_map.get(slug)
        if not role_id:
            continue
            
        codes_to_grant = list(perm_map.keys()) if perms == ["*"] else [c for c in perms if c in perm_map]
        
        for code in codes_to_grant:
            perm_id = perm_map[code]
            
            # Idempotent insert
            existing_rp = conn.execute(
                text("SELECT id FROM role_permissions WHERE role_id = :r_id AND permission_id = :p_id"),
                {"r_id": role_id, "p_id": perm_id}
            ).fetchone()
            
            if not existing_rp:
                conn.execute(
                    text("INSERT INTO role_permissions (id, role_id, permission_id, created_at) VALUES (:id, :r_id, :p_id, :now)"),
                    {"id": str(uuid.uuid4()), "r_id": role_id, "p_id": perm_id, "now": datetime.now(timezone.utc)}
                )

    # 4. Migrate Users
    # Check if 'role' column still exists in users table
    columns_query = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'role'
    """)
    has_role_column = conn.execute(columns_query).fetchone()
    
    if has_role_column:
        print("Migrating user roles from legacy ENUM...")
        users = conn.execute(text("SELECT id, role, system_role_id FROM users")).fetchall()
        
        for user_row in users:
            user_id = user_row[0]
            legacy_role = user_row[1]  # ENUM value like 'ADMIN', 'MANAGER', 'MEMBER'
            current_system_role_id = user_row[2]
            
            # Map legacy enum to new role slug
            target_slug = "developer" # Default
            if legacy_role == "ADMIN":
                target_slug = "super_admin"
            elif legacy_role == "MANAGER":
                target_slug = "project_mgr"
                
            role_id = role_map.get(target_slug)
            if not role_id:
                continue
                
            # Assign system_role_id if not set
            if not current_system_role_id:
                conn.execute(
                    text("UPDATE users SET system_role_id = :role_id WHERE id = :user_id"),
                    {"role_id": role_id, "user_id": user_id}
                )
                
            # Assign global UserRole if not exists
            existing_ur = conn.execute(
                text("SELECT id FROM user_roles WHERE user_id = :user_id AND role_id = :role_id AND scope_type = 'global'"),
                {"user_id": user_id, "role_id": role_id}
            ).fetchone()
            
            if not existing_ur:
                conn.execute(
                    text("""
                        INSERT INTO user_roles (id, user_id, role_id, scope_type, assigned_at, created_at, updated_at) 
                        VALUES (:id, :user_id, :role_id, 'global', :now, :now, :now)
                    """),
                    {"id": str(uuid.uuid4()), "user_id": user_id, "role_id": role_id, "now": datetime.now(timezone.utc)}
                )
    else:
        print("Legacy 'role' column not found on users table. Skipping user migration.")

    # 5. Provision Super Admin User
    seed_super_admin(conn)

    print("RBAC seeding complete.")

def seed_super_admin(conn):
    from core.security import SUPER_ADMIN_EMAIL, get_password_hash
    print("Ensuring Super Admin user exists...")
    
    existing_user = conn.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": SUPER_ADMIN_EMAIL}
    ).fetchone()
    
    role_id_row = conn.execute(
        text("SELECT id FROM roles WHERE slug = 'super_admin'")
    ).fetchone()
    
    if not role_id_row:
        print("Super admin role not found, skipping.")
        return
        
    role_id = role_id_row[0]
    
    if existing_user:
        user_id = existing_user[0]
        conn.execute(
            text("UPDATE users SET system_role_id = :role_id WHERE id = :user_id"),
            {"role_id": role_id, "user_id": user_id}
        )
    else:
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash("Hexerve@123")
        conn.execute(
            text("""
                INSERT INTO users (id, name, email, hashed_password, system_role_id, created_at, updated_at) 
                VALUES (:id, :name, :email, :pwd, :role_id, :now, :now)
            """),
            {
                "id": user_id, 
                "name": "Super Admin", 
                "email": SUPER_ADMIN_EMAIL, 
                "pwd": hashed_password, 
                "role_id": role_id, 
                "now": datetime.now(timezone.utc)
            }
        )
        print(f"Created Super Admin: {SUPER_ADMIN_EMAIL}")
        
    existing_ur = conn.execute(
        text("SELECT id FROM user_roles WHERE user_id = :user_id AND role_id = :role_id AND scope_type = 'global'"),
        {"user_id": user_id, "role_id": role_id}
    ).fetchone()
    
    if not existing_ur:
        conn.execute(
            text("""
                INSERT INTO user_roles (id, user_id, role_id, scope_type, assigned_at, created_at, updated_at) 
                VALUES (:id, :user_id, :role_id, 'global', :now, :now, :now)
            """),
            {"id": str(uuid.uuid4()), "user_id": user_id, "role_id": role_id, "now": datetime.now(timezone.utc)}
        )

def seed():
    from core.database import engine
    with engine.begin() as conn:
        seed_rbac_from_connection(conn)

if __name__ == "__main__":
    seed()

