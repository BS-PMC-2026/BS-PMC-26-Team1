from __future__ import annotations

from typing import Optional

from app.models import Module, TheoryContent, db


def get_theory_content_by_module_name(module_name: str) -> Optional[TheoryContent]:
    module = Module.query.filter(Module.name.ilike(module_name)).first()
    if not module:
        return None
    return TheoryContent.query.filter_by(module_id=module.id).first()


def get_or_create_theory_content(module_name: str) -> Optional[TheoryContent]:
    module = Module.query.filter(Module.name.ilike(module_name)).first()
    if not module:
        return None
    content = TheoryContent.query.filter_by(module_id=module.id).first()
    if content:
        return content

    content = TheoryContent(
        module_id=module.id,
        headline=f"{module.name} Update",
        explanation=f"Latest lecturer guidance for the {module.name} module.",
        examples="Add practical examples here.",
    )
    db.session.add(content)
    db.session.flush()
    return content
