import sys
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://pmuser:password@localhost:5432/proj_mgmt_db')
with engine.connect() as conn:
    res = conn.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'notification_log';"))
    print("Notification Log indexes:", [r[0] for r in res])
    res = conn.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'notification_preferences';"))
    print("Notification Prefs indexes:", [r[0] for r in res])
    res = conn.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'task_watchers';"))
    print("Task Watchers indexes:", [r[0] for r in res])
