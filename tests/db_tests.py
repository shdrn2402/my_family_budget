import pytest
from pytest_postgresql import factories
from scripts import create_db


# Starts a temporary PostgreSQL process, using a random available port
# and specifying the Unix socket directory.
postgresql_my_proc = factories.postgresql_proc(port=None, unixsocketdir="/tmp")

# Creates a client fixture connected to the PostgreSQL process.
# This fixture allows interaction with the temporary PostgreSQL instance.
postgresql_my = factories.postgresql("postgresql_my_proc")


@pytest.fixture
def db_connection(postgresql_my):
    """Pytest fixture to provide a PostgreSQL connection."""
    conn = postgresql_my
    yield conn  # provide the connection to the test
    # After the test is done, close the connection if needed
    conn.close()


@pytest.fixture
def db_params(db_connection):
    """Fixture to provide common parameters for database operations."""
    return {
        "root_db_name": "postgres",  # the default database name in PostgreSQL
        "root_user": "postgres",  # the default superuser
        "root_password": "",  # no password for the temporary DB
        "host": "localhost",
        "port": db_connection.info.port,
        "db_name_to_create": "test_db_creation",
        "wrong_db_name_to_create": "test_db; DROP DATABASE postgres; --"
    }


class TestDatabase:
    """Class to test PostgreSQL database connection."""

    def test_postgresql_connection(self, db_connection):
        """Test the PostgreSQL connection by checking the current database."""
        # Open a cursor to perform a database operation
        cur = db_connection.cursor()

        # Execute a query to check the current database
        cur.execute("SELECT current_database();")

        # Fetch the result and verify that the database name is not None
        db_name = cur.fetchone()[0]
        assert db_name is not None  # Ensure the database exists

        # Close the cursor after the operation
        cur.close()

    def test_create_db_with_correct_name(self, db_connection, db_params, caplog):
        """Test the create_database function."""
        # Call the create_database function with the parameters from the fixture
        create_db.create_database(
            db_params["root_db_name"],
            db_params["root_user"],
            db_params["root_password"],
            db_params["host"],
            db_params["port"],
            db_params["db_name_to_create"]
        )
        # Verify the database was created by connecting to it
        with db_connection.cursor() as cur:
            cur.execute(
                "SELECT datname FROM pg_database WHERE datname = %s;",
                (db_params["db_name_to_create"],),
            )
            db_exists = cur.fetchone()
            assert db_exists is not None, f"Database {db_params['db_name_to_create']} was not created."
