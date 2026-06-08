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
  body { margin: 0; padding: 0; background-color: #f4f4f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
  .email-wrapper { width: 100%; background-color: #f4f4f7; padding: 40px 0; }
  .email-body { max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .email-header { background: linear-gradient(135deg, #7B68EE 0%, #5B4CD8 100%); padding: 28px 32px; }
  .email-header h1 { color: #ffffff; margin: 0; font-size: 20px; font-weight: 600; letter-spacing: -0.3px; }
  .email-content { padding: 32px; color: #374151; line-height: 1.6; font-size: 15px; }
  .email-content h2 { color: #111827; font-size: 18px; margin: 0 0 16px 0; font-weight: 600; }
  .detail-card { background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 20px; margin: 16px 0; }
  .detail-card .label { color: #6b7280; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 4px; }
  .detail-card .value { color: #111827; font-size: 15px; font-weight: 500; }
  .change-row { display: flex; align-items: center; gap: 8px; margin: 8px 0; }
  .old-value { color: #9ca3af; text-decoration: line-through; }
  .new-value { color: #7B68EE; font-weight: 600; }
  .arrow { color: #d1d5db; }
  .btn { display: inline-block; background: linear-gradient(135deg, #7B68EE 0%, #5B4CD8 100%); color: #ffffff !important; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; margin-top: 20px; }
  .email-footer { padding: 24px 32px; text-align: center; color: #9ca3af; font-size: 12px; border-top: 1px solid #f3f4f6; }
  .email-footer a { color: #7B68EE; text-decoration: none; }
</style>
</head>
<body>
<div class="email-wrapper">
  <div class="email-body">
    <div class="email-header">
      <h1>{{ header_title }}</h1>
    </div>
    <div class="email-content">
      {{ content }}
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ task_url }}" class="btn">View Task →</a>
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
<a href="{{ frontend_url }}" class="btn">View Sprint →</a>
""",
    },
    "SPRINT_COMPLETED": {
        "subject": "[{{ project_name }}] Sprint completed: {{ sprint_name }}",
        "header": "Sprint Completed",
        "content": """\
<h2>{{ sprint_name }}</h2>
<p><strong>{{ actor_name }}</strong> marked this sprint as completed in <strong>{{ project_name }}</strong>.</p>
<a href="{{ frontend_url }}" class="btn">View Project →</a>
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
<a href="{{ frontend_url }}/projects" class="btn">View Project →</a>
""",
    },
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
