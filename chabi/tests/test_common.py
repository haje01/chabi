import json

from pony import orm


def test_common_pony():
    db = orm.Database()

    class Account(db.Entity):
        name = orm.Required(str)
        msgn_id = orm.Required(int)
        auth_code = orm.Required(str)

    db.bind('sqlite', ':memory:', create_db=True)
    db.generate_mapping(create_tables=True)
    orm.sql_debug(True)

    @orm.db_session
    def test():
        Account(name="haje01", msgn_id=3498, auth_code="1234")
        a = Account(name="haje02", msgn_id=2345, auth_code="1234")
        assert len(orm.select(a for a in Account)) == 2
        assert len(orm.select(a for a in Account if a.msgn_id == 2345)) == 1
        a.delete()
        assert len(orm.select(a for a in Account)) == 1

    test()


def test_common_template():
    from jinja2 import Template

    temp = Template('Hello, {{ name }}!')
    assert 'Hello, John Doe!' == temp.render(name='John Doe')

    temp = Template('{"message": {"text": {{msg|tojson}}}}')
    data = temp.render(msg="Hello\nWorld.")
    data = json.loads(data)
    assert 'message' in data
