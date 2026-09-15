from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incident_activity import IncidentActivityType
from app.models.incident_note import IncidentNote
from app.services.incident_activity_service import add_incident_activity

async def create_incident_note(
        db: AsyncSession,
        incident_id: int,
        author_user_id: int,
        content: str
) -> IncidentNote:
    """
    Create a new investigation note for an incident

    After creation, reload the note with its author relationship
    so after API serialisation does not trigger an asynchronous lazy load.
    """
    cleaned_content = content.strip()

    note = IncidentNote(
        incident_id=incident_id,
        author_user_id=author_user_id,
        content=cleaned_content,
    )

    db.add(note)
    # Generate the note ID while keeping everything in one transaction.
    await db.flush()

    await add_incident_activity(
        db,
        incident_id=incident_id,
        actor_user_id=author_user_id,
        activity_type=IncidentActivityType.NOTE_ADDED,
        description="Investigation note added.",
        new_value=f"Note #{note.id}",
    )

    await db.commit()

    result = await db.execute(
        select(IncidentNote)
        .options(
            selectinload(IncidentNote.author),
        )
        .where(IncidentNote.id == note.id)
    )

    return result.scalar_one_or_none()

async def get_incident_notes(
        db: AsyncSession,
        incident_id: int,
) -> list[IncidentNote]:
    """
    Return investigation notes for an incident in chronological order

    Authors are eager-loaded to avoid one additional query per note.
    """
    result = await db.execute(
        select(IncidentNote)
        .options(
            selectinload(IncidentNote.author)
        )
        .where(
            IncidentNote.incident_id == incident_id
        )
        .order_by(
            IncidentNote.created_at.asc(),
            IncidentNote.id.asc(),
        )
    )

    return list(result.scalars().all())