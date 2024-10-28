import pytest
from pytest_postgresql import factories


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
