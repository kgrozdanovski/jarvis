import os
import re
import sys
import importlib.util
from src.core.logger import get_logger
from src.core.dbal import DBAL

folder = "migrations"
logger = get_logger("script:migrate")

# Directory where migration scripts reside.
MIGRATIONS_DIR = os.path.join(os.getcwd(), "migrations")

# Regular expression for migration file names: 12 digits (YYYYMMDDHHMM) + .py extension.
MIGRATION_FILENAME_REGEX = re.compile(r"^\d{12}\.py$")

db = DBAL()


def get_migration_files():
    """List and return migration files in the migrations directory sorted by filename."""
    try:
        files = os.listdir(MIGRATIONS_DIR)
    except FileNotFoundError:
        sys.exit(f"Error: Migrations directory '{MIGRATIONS_DIR}' not found.")

    migration_files = [f for f in files if MIGRATION_FILENAME_REGEX.match(f)]
    migration_files.sort()
    return migration_files


def ensure_migrations_table():
    """
    Create the migrations table if it does not already exist.
    This table tracks which migrations have been applied.
    """
    db.execute("""
               CREATE TABLE IF NOT EXISTS migrations
               (
                   id         SERIAL PRIMARY KEY,
                   migration  VARCHAR(255) NOT NULL,
                   applied_at TIMESTAMP    NOT NULL DEFAULT NOW()
               )
               """)


def get_applied_migrations_as_filenames():
    """Retrieve a set of migration filenames that have already been applied."""
    results = db.fetch_all("SELECT migration FROM migrations")
    if results is None:
        return set()

    return [f"{result['migration']}.py" for result in results]


def apply_migration(migration_filename: str):
    """
    Import and execute the upgrade() function from a migration script.
    After successful execution, record the migration in the migrations table.
    """
    migration_path = os.path.join(MIGRATIONS_DIR, migration_filename)
    logger.info(f"Applying migration: {migration_filename}")

    # Dynamically import the migration module.
    spec = importlib.util.spec_from_file_location("migration", migration_path)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)

    # Check that the migration module has an upgrade() function.
    if not hasattr(migration_module, "upgrade"):
        raise Exception(
            f"Migration {migration_filename} does not define an upgrade() function."
        )

    # Run the upgrade function
    migration_module.upgrade(db)

    # Extract migration number from filename
    migration_number = migration_filename.split('.')[0]

    # Record the migration as applied.
    db.execute("INSERT INTO migrations (migration) VALUES (%s)", (migration_number,))
    logger.info(f"Migration {migration_filename} applied successfully.")


def main():
    migration_files = get_migration_files()
    if not migration_files:
        logger.info("No migration files found in the migrations directory.")
        return

    try:
        ensure_migrations_table()
        applied_migrations = get_applied_migrations_as_filenames()

        for migration in migration_files:
            try:
                logger.info(f"Processing migration: {migration}...")
                if migration in applied_migrations:
                    logger.info(f"Skipping already applied migration: {migration}")
                    continue

                apply_migration(migration)
            except Exception as e:
                logger.error(f"Error applying migration {migration}: {e}")
                sys.exit(1)

        logger.info("All migrations applied successfully.")
        return

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(
            f"Error while running migration script at line {exc_traceback.tb_lineno}: {e}",
            exc_info=True
        )

    sys.exit(1)


if __name__ == "__main__":
    main()
