from datetime import datetime
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

project_root = os.path.dirname(script_dir)
# YYYYMMDDHHMM format
timestamp = datetime.now().strftime("%Y%m%d%H%M")

filename = os.path.join(project_root, "migrations", f"{timestamp}.py")

migration_content = """\
def upgrade(db):
    with db.transaction() as cur:
        # Add your database changes here
        # cur.execute(\"\"\"
        #    
        # \"\"\")
        
        pass
        
    # optional
    with db.pool.connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            # If you need to run non-transactional queries, do them here
             
            # cur.execute(\"\"\"
            #
            # \"\"\")
            
            pass

"""

with open(filename, "w") as f:
    f.write(migration_content)

print(f"migration file created: {filename}")
