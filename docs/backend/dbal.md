## Proprietary DBAL implementation

### Example Usage

```python
import json
import uuid
import datetime
from src.core.dbal import DBAL
from src.core.logger import get_logger

logger = get_logger("dbal")
db = DBAL()

if __name__ == "__main__":
    try:
        # Create table example (if it doesn't exist)
        create_table_query = """
        CREATE TABLE IF NOT EXISTS example (
            id UUID PRIMARY KEY,
            data JSONB,
            created_at TIMESTAMP
        );
        """
        db.execute(create_table_query)

        # Insert example data
        data_to_insert = {
            "id": uuid.uuid4(),
            "data": json.dumps({"message": "Hello, Sir!"}),
            "created_at": datetime.utcnow()
        }
        # Optionally returning the id (or any other column)
        inserted_id = db.insert("example", data_to_insert, returning="id")
        logger.info(f"Inserted record with ID: {inserted_id}")

        # Read records
        results = db.read("example")
        for row in results:
            logger.info(f"Row: {row}")

        # Update a record (using the id from the first record)
        if results:
            update_data = {"data": json.dumps({"updated": True})}
            where_clause = {"id": results[0][0]}
            updated_rows = db.update("example", update_data, where_clause)
            logger.info(f"Number of rows updated: {updated_rows}")

        # Delete a record (for demonstration)
        if results:
            delete_where = {"id": results[0][0]}
            deleted_rows = db.delete("example", delete_where)
            logger.info(f"Number of rows deleted: {deleted_rows}")

        # Transaction example
        with db.transaction() as cursor:
            cursor.execute("INSERT INTO example (id, data, created_at) VALUES (%s, %s, %s)",
                           (uuid.uuid4(), json.dumps({"transaction": True}), datetime.utcnow()))
            # Add more operations as needed

    except Exception as e:
        logger.error(f"An error occurred: {e}")
```
