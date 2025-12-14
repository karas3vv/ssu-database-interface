from sqlalchemy.exc import SQLAlchemyError, IntegrityError


def db_error_to_text(exc: Exception) -> str:
    orig = getattr(exc, "orig", None)
    if orig is not None:
        msg = str(orig)
    else:
        msg = str(exc)

    if "violates foreign key constraint" in msg or "23503" in msg:
        return "Нельзя выполнить действие: есть связанные записи (ограничение связей)."
    if "duplicate key value violates unique constraint" in msg or "23505" in msg:
        return "Нельзя выполнить действие: такое значение уже существует (уникальность)."
    if "check constraint" in msg:
        return "Нельзя выполнить действие: нарушено ограничение допустимых значений."
    if "booking conflict" in msg.lower():
        return "Нельзя создать бронирование: выбранное время пересекается с другой бронью."
    return msg


def safe_commit(db):
    try:
        db.commit()
        return None
    except IntegrityError as exc:
        db.rollback()
        return db_error_to_text(exc)
    except SQLAlchemyError as exc:
        db.rollback()
        return db_error_to_text(exc)
