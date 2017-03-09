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
        db.bind('sqlite', sqlite_file)
    except TypeError:
        pass

    if sqlite_file == ':memory:':
        try:
            db.generate_mapping(check_tables=False)
        except orm.core.MappingError:
            pass
        db.drop_all_tables(with_all_data=True)

    db.create_tables()


class AccountLink(db.Entity):
    id = orm.PrimaryKey(str)
    auth_code = orm.Required(str)
