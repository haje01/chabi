from datetime import datetime

from pony import orm
from pony.orm import db_session  # NOQA

db = orm.Database()


def safe_db_init(db, sqlite_file):
    """Safe DB binding, mapping

    In automated test, multiple DB binds can occur, and cause
        "Database object already bound" error. This function
        handle error of duplicated binding.
    """
    try:
        db.bind('sqlite', sqlite_file, create_db=True)
    except TypeError:
        pass
    else:
        try:
            db.generate_mapping(create_tables=True)
        except orm.core.MappingError:
            pass


class AccountLink(db.Entity):
    id = orm.PrimaryKey(str)
    auth_code = orm.Required(str)


class PostbackToken(db.Entity):
    id = orm.PrimaryKey(int, auto=True)
    value = orm.Required(str)
    issue_dt = orm.Required(datetime)
    close_dt = orm.Optional(datetime)
