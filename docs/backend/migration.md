# Database Migration System

## Getting started

1. **Generate a migration file:**
    ```shell
    python generate_migration.py
    ```
2. **Write your database changes in the generated file:**

```python
def upgrade(conn):
    with conn.cursor() as cur:
        # Add your database changes here
        pass

        conn.commit()
```

3. **Deploy your changes:**

   Migrations run automatically during deployment in timestamp order.
