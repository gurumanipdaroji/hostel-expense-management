from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

db_url = settings.resolved_database_url

connect_args = {}
engine_kwargs = {}

if db_url.startswith("sqlite"):
    # SQLite requires check_same_thread=False when used across threads in FastAPI
    connect_args["check_same_thread"] = False
else:
    # MySQL / remote databases benefit from pool_pre_ping to detect dropped connections
    engine_kwargs["pool_pre_ping"] = True

# Create SQLAlchemy engine
engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

# Enable foreign key enforcement for SQLite
if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def migrate_db_schema():
    """
    Safely adds missing columns (such as 'usn' and 'department') to existing tables
    without dropping or modifying existing data.
    """
    try:
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("users")]
            with engine.begin() as conn:
                if "usn" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN usn VARCHAR(50)"))
                    print("[Migration] Added 'usn' column to 'users' table")
                if "department" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(100)"))
                    print("[Migration] Added 'department' column to 'users' table")
    except Exception as e:
        print(f"[Migration Warning] Schema migration check: {e}")


def get_db():
    """
    FastAPI dependency that yields a database session per request
    and ensures it is properly closed when finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
