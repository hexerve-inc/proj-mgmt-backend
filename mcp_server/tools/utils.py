import uuid

def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

async def resolve_project_id(client, project_identifier: str) -> str:
    if not project_identifier:
        return project_identifier
    if is_valid_uuid(project_identifier):
        return project_identifier
        
    # It's a name or key, fetch projects and find it
    try:
        projects = await client.get_projects()
        for p in projects:
            if p.get("name", "").lower() == project_identifier.lower() or p.get("project_key", "").lower() == project_identifier.lower():
                return p["id"]
        raise Exception(f"Could not find project with name or key '{project_identifier}'")
    except Exception as e:
        raise Exception(f"Failed to resolve project identifier '{project_identifier}': {str(e)}")
