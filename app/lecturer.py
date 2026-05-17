{% extends 'base.html' %}

{% block content %}
<div class="module-header">
    <h1>Lecturer Dashboard</h1>
    <p class="subtitle">Student performance, averages, and weak module analytics.</p>
</div>

{# Issue 2: Visible, distinct error messaging for the lecturer's home screen.
   The alert component is part of the design system (ds-alert) and shares one
   visual language with every other screen. We render an "access" alert only
   when the active session is not a lecturer (or is in demo mode without a
   real lecturer identity). #}
{% set is_lecturer = session.get('role') == 'lecturer' and not session.get('demo_mode') %}
{% if not is_lecturer %}
<div class="ds-alert ds-alert--error" role="alert" aria-live="polite" id="lecturer-access-alert">
    <div class="ds-alert__icon" aria-hidden="true">!</div>
    <div class="ds-alert__body">
        <h3 class="ds-alert__title">Lecturer access required</h3>
        <p class="ds-alert__message">
            This screen is restricted to lecturer accounts. Students should head to the learning path,
            while lecturers can sign in with their staff credentials to manage questions, theory content
            and review live student analytics.
        </p>
        <div class="ds-alert__action ds-flex ds-gap-2">
            <a href="/login" class="ds-btn ds-btn-primary ds-btn-sm">Sign in as lecturer</a>
            <a href="/learning-path" class="ds-btn ds-btn-mint ds-btn-sm">Continue as student</a>
        </div>
    </div>
</div>
{% endif %}

<div class="ds-row" style="margin-bottom: var(--ds-space-6);">
    <div class="ds-card ds-text-center" style="flex:1; min-width:220px;">
        <p class="ds-eyebrow ds-mb-2">Students</p>
        <h2 class="ds-stat-number ds-text-primary">{{ metrics.students_count }}</h2>
        <p class="ds-text-muted ds-mt-2" style="margin-bottom:0;">Registered Students</p>
    </div>
    <div class="ds-card ds-text-center" style="flex:1; min-width:220px;">
        <p class="ds-eyebrow ds-mb-2" style="color: var(--ds-state-success);">Performance</p>
        <h2 class="ds-stat-number ds-text-success">{{ metrics.overall_average_success }}%</h2>
        <p class="ds-text-muted ds-mt-2" style="margin-bottom:0;">Overall Success Average</p>
    </div>
</div>

<div class="action-container" style="justify-content:flex-start; margin-bottom: var(--ds-space-5);">
    <a href="/lecturer/questions" class="ds-btn ds-btn-purple">Manage Questions</a>
    <a href="/lecturer/theory" class="ds-btn ds-btn-mint">Manage Theory Content</a>
</div>

<div class="ds-card" style="margin-bottom: var(--ds-space-6);">
    <h2 class="ds-mt-0">Student Performance</h2>
    {% if metrics.student_performance %}
        <table class="ds-table">
            <thead>
                <tr>
                    <th>Student</th>
                    <th>Average Success</th>
                    <th>Attempts</th>
                </tr>
            </thead>
            <tbody>
                {% for row in metrics.student_performance %}
                <tr>
                    <td>{{ row.student.full_name }}</td>
                    <td>{{ row.avg_success_rate }}%</td>
                    <td>{{ row.total_attempts }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <div class="ds-alert ds-alert--info" role="status" style="margin-top: var(--ds-space-4);">
            <div class="ds-alert__icon" aria-hidden="true">i</div>
            <div class="ds-alert__body">
                <h3 class="ds-alert__title">No analytics yet</h3>
                <p class="ds-alert__message">Student analytics will appear here once learners begin completing exercises.</p>
            </div>
        </div>
    {% endif %}
</div>

<div class="ds-card">
    <h2 class="ds-mt-0">Weak Areas by Module</h2>
    {% if metrics.module_weakness %}
        <table class="ds-table">
            <thead>
                <tr>
                    <th>Module</th>
                    <th>Average Success</th>
                </tr>
            </thead>
            <tbody>
                {% for item in metrics.module_weakness %}
                <tr>
                    <td>{{ item.module.name }}</td>
                    <td>
                        {% set rate = item.avg_success_rate %}
                        {% if rate >= 70 %}
                            <span class="ds-pill ds-pill-success">{{ rate }}%</span>
                        {% elif rate >= 40 %}
                            <span class="ds-pill ds-pill-progress">{{ rate }}%</span>
                        {% else %}
                            <span class="ds-pill ds-pill-error">{{ rate }}%</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <div class="ds-alert ds-alert--info" role="status" style="margin-top: var(--ds-space-4);">
            <div class="ds-alert__icon" aria-hidden="true">i</div>
            <div class="ds-alert__body">
                <h3 class="ds-alert__title">No module statistics yet</h3>
                <p class="ds-alert__message">Module-level weakness reports will populate after the first cohort of attempts.</p>
            </div>
        </div>
    {% endif %}
</div>
{% endblock %}
