"""
HTML email template engine for notification emails.

Uses Jinja2 for rendering branded, responsive email templates.
Each event type maps to a subject line and body template that
receives contextual metadata (task codes, status names, user names, etc.).
"""

from jinja2 import Environment, BaseLoader
from models.notification_preference import NotificationEventType
from core.config import settings


# ── Base HTML shell ──────────────────────────────────────────────

BASE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{{ subject }}</title>
<style>
  body { margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; }
  .email-wrapper { width: 100%; background-color: #f8fafc; padding: 48px 0; }
  .email-body { max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.02); border: 1px solid #f1f5f9; }
  .email-header { background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); padding: 36px 40px; text-align: center; }
  .email-header h1 { color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }
  .email-content { padding: 40px; color: #334155; line-height: 1.6; font-size: 16px; }
  .email-content h2 { color: #0f172a; font-size: 20px; margin: 0 0 20px 0; font-weight: 700; letter-spacing: -0.3px; }
  .email-content p { margin: 0 0 20px 0; }
  .detail-card { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px 24px; margin: 24px 0; }
  .detail-card .label { color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 700; margin-bottom: 8px; }
  .detail-card .value { color: #0f172a; font-size: 16px; font-weight: 500; }
  .change-row { padding: 4px 0; }
  .old-value { color: #94a3b8; text-decoration: line-through; display: inline-block; }
  .arrow { color: #cbd5e1; margin: 0 12px; font-weight: 600; display: inline-block; }
  .new-value { color: #4f46e5; font-weight: 700; display: inline-block; }
  .btn-wrapper { margin-top: 32px; text-align: center; }
  .btn { display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: #ffffff !important; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 15px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2); }
  .email-footer { padding: 32px 40px; text-align: center; color: #94a3b8; font-size: 13px; background-color: #fcfcfd; border-top: 1px solid #f1f5f9; }
  .email-footer a { color: #6366f1; text-decoration: none; font-weight: 500; }
  .email-footer p { margin: 0 0 8px 0; }
</style>
</head>
<body>
<div class="email-wrapper">
  <div class="email-body">
    <div class="email-header">
      <h1>{{ header_title }}</h1>
    </div>
    <div class="email-content">
      {{ content | safe }}
    </div>
    <div class="email-footer">
      <p>You received this email because of your notification preferences in <a href="{{ frontend_url }}">{{ app_name }}</a>.</p>
      <p><a href="{{ frontend_url }}/settings">Manage notification settings</a></p>
    </div>
  </div>
</div>
</body>
</html>
"""

# ── Per-event content templates ──────────────────────────────────

EVENT_TEMPLATES: dict[str, dict[str, str]] = {
    "TASK_CREATED": {
        "subject": "[{{ project_name }}] New task created: {{ task_code }} {{ task_title }}",
        "header": "New Task Created",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> created a new task in <strong>{{ project_name }}</strong>.</p>
<div class="detail-card">
  <div class="label">Task</div>
  <div class="value">{{ task_code }} — {{ task_title }}</div>
</div>
{% if description %}
<div class="detail-card">
  <div class="label">Description</div>
  <div class="value">{{ description }}</div>
</div>
{% endif %}
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "TASK_STATUS_CHANGED": {
        "subject": "[{{ project_name }}] {{ task_code }} status → {{ new_status }}",
        "header": "Status Changed",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> updated the status of this task.</p>
<div class="detail-card">
  <div class="label">Status Change</div>
  <div class="change-row">
    <span class="old-value">{{ old_status }}</span>
    <span class="arrow">→</span>
    <span class="new-value">{{ new_status }}</span>
  </div>
</div>
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "TASK_ASSIGNED": {
        "subject": "[{{ project_name }}] {{ task_code }} assigned to you",
        "header": "Task Assigned to You",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> assigned this task to you.</p>
<div class="detail-card">
  <div class="label">Assigned To</div>
  <div class="value">{{ assignee_name }}</div>
</div>
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "TASK_REASSIGNED": {
        "subject": "[{{ project_name }}] {{ task_code }} reassigned",
        "header": "Task Reassigned",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> reassigned this task.</p>
<div class="detail-card">
  <div class="label">Assignment Change</div>
  <div class="change-row">
    <span class="old-value">{{ old_assignee_name }}</span>
    <span class="arrow">→</span>
    <span class="new-value">{{ new_assignee_name }}</span>
  </div>
</div>
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "TASK_DETAILS_UPDATED": {
        "subject": "[{{ project_name }}] {{ task_code }} details updated",
        "header": "Task Details Updated",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> updated the details of this task.</p>
<div class="detail-card">
  <div class="label">Changed Fields</div>
  <div class="value">{{ changed_fields }}</div>
</div>
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "TASK_DELETED": {
        "subject": "[{{ project_name }}] {{ task_code }} deleted",
        "header": "Task Deleted",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> deleted this task from <strong>{{ project_name }}</strong>.</p>
""",
    },
    "TASK_PRIORITY_CHANGED": {
        "subject": "[{{ project_name }}] {{ task_code }} priority → {{ new_priority }}",
        "header": "Priority Changed",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> changed the priority of this task.</p>
<div class="detail-card">
  <div class="label">Priority Change</div>
  <div class="change-row">
    <span class="old-value">{{ old_priority }}</span>
    <span class="arrow">→</span>
    <span class="new-value">{{ new_priority }}</span>
  </div>
</div>
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "TASK_DUE_DATE_CHANGED": {
        "subject": "[{{ project_name }}] {{ task_code }} due date updated",
        "header": "Due Date Changed",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> updated the due date of this task.</p>
<div class="detail-card">
  <div class="label">Due Date Change</div>
  <div class="change-row">
    <span class="old-value">{{ old_due_date or 'Not set' }}</span>
    <span class="arrow">→</span>
    <span class="new-value">{{ new_due_date or 'Not set' }}</span>
  </div>
</div>
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "TASK_SPRINT_CHANGED": {
        "subject": "[{{ project_name }}] {{ task_code }} moved to {{ new_sprint }}",
        "header": "Sprint Changed",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> moved this task to a different sprint.</p>
<div class="detail-card">
  <div class="label">Sprint Change</div>
  <div class="change-row">
    <span class="old-value">{{ old_sprint or 'Backlog' }}</span>
    <span class="arrow">→</span>
    <span class="new-value">{{ new_sprint or 'Backlog' }}</span>
  </div>
</div>
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "TASK_COMMENT_ADDED": {
        "subject": "[{{ project_name }}] New comment on {{ task_code }}",
        "header": "New Comment",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> commented on this task.</p>
<div class="detail-card">
  <div class="label">Comment</div>
  <div class="value">{{ comment_text }}</div>
</div>
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "TASK_COMMENT_MENTION": {
        "subject": "[{{ project_name }}] You were mentioned in {{ task_code }}",
        "header": "You Were Mentioned",
        "content": """\
<h2>{{ task_code }}: {{ task_title }}</h2>
<p><strong>{{ actor_name }}</strong> mentioned you in a comment.</p>
<div class="detail-card">
  <div class="label">Comment</div>
  <div class="value">{{ comment_text }}</div>
</div>
<div class="btn-wrapper">
  <a href="{{ task_url }}" class="btn">View Task →</a>
</div>
""",
    },
    "SPRINT_STARTED": {
        "subject": "[{{ project_name }}] Sprint started: {{ sprint_name }}",
        "header": "Sprint Started",
        "content": """\
<h2>{{ sprint_name }}</h2>
<p><strong>{{ actor_name }}</strong> started a sprint in <strong>{{ project_name }}</strong>.</p>
{% if sprint_goal %}
<div class="detail-card">
  <div class="label">Sprint Goal</div>
  <div class="value">{{ sprint_goal }}</div>
</div>
{% endif %}
<div class="btn-wrapper">
  <a href="{{ frontend_url }}" class="btn">View Sprint →</a>
</div>
""",
    },
    "SPRINT_COMPLETED": {
        "subject": "[{{ project_name }}] Sprint completed: {{ sprint_name }}",
        "header": "Sprint Completed",
        "content": """\
<h2>{{ sprint_name }}</h2>
<p><strong>{{ actor_name }}</strong> marked this sprint as completed in <strong>{{ project_name }}</strong>.</p>
<div class="btn-wrapper">
  <a href="{{ frontend_url }}" class="btn">View Project →</a>
</div>
""",
    },
    "PROJECT_STATUS_CHANGED": {
        "subject": "[{{ project_name }}] Project status → {{ new_status }}",
        "header": "Project Status Changed",
        "content": """\
<h2>{{ project_name }}</h2>
<p><strong>{{ actor_name }}</strong> changed the project status.</p>
<div class="detail-card">
  <div class="label">Status Change</div>
  <div class="change-row">
    <span class="old-value">{{ old_status }}</span>
    <span class="arrow">→</span>
    <span class="new-value">{{ new_status }}</span>
  </div>
</div>
<div class="btn-wrapper">
  <a href="{{ frontend_url }}/projects" class="btn">View Project →</a>
</div>
""",
    }
}


class EmailTemplateEngine:
    """Renders email subject, HTML body, and plain-text body for each event."""

    def __init__(self):
        self._env = Environment(loader=BaseLoader(), autoescape=True)

    def render(
        self,
        event_type: str,
        context: dict,
    ) -> tuple[str, str, str]:
        """
        Returns (subject, html_body, text_body) for the given event type.

        The context dict is merged with global settings (app_name, frontend_url)
        and passed to the Jinja2 templates.
        """
        template_data = EVENT_TEMPLATES.get(event_type)
        if not template_data:
            # Fallback for unknown event types
            return (
                f"[{settings.SMTP_FROM_NAME}] Notification",
                f"<p>You have a new notification.</p>",
                "You have a new notification.",
            )

        # Merge global context
        ctx = {
            "app_name": settings.SMTP_FROM_NAME,
            "frontend_url": settings.FRONTEND_URL,
            **context,
        }

        # Build task_url if entity is a task
        if "task_id" in ctx:
            ctx.setdefault("task_url", f"{settings.FRONTEND_URL}/tasks/{ctx['task_id']}")

        # Render subject
        subject = self._env.from_string(template_data["subject"]).render(**ctx)

        # Render inner content
        content_html = self._env.from_string(template_data["content"]).render(**ctx)

        # Render full HTML shell
        html_body = self._env.from_string(BASE_HTML).render(
            subject=subject,
            header_title=template_data["header"],
            content=content_html,
            frontend_url=settings.FRONTEND_URL,
            app_name=settings.SMTP_FROM_NAME,
        )

        # Generate plain-text version by stripping HTML tags
        import re
        text_body = re.sub(r"<[^>]+>", "", content_html)
        text_body = re.sub(r"\n\s*\n", "\n\n", text_body).strip()

        return subject, html_body, text_body
