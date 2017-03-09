from pony import orm
from pony.orm import db_session  # NOQA

db = orm.Database()


class AccountLink(db.Entity):
    id = orm.PrimaryKey(str)
    auth_code = orm.Required(str)
