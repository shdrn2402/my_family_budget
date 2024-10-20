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
