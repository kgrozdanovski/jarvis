## Python Script Runner

This script is used to run Python scripts in the backend container. It is a wrapper around the `python` command
that sets the necessary environment variables and runs the script in the backend container or venv.

> If the script is run from within a Virtual Environment then the child process will also run within that environment.

### Usage

**With Docker**

Run the following command from the repository root:
```bash
docker compose exec python python3 scripts/script.py --name compile_mjml_templates
```

**On Host**

Run the following from the `backend/` directory:
```bash
python scripts/script.py --name compile_mjml_templates
```

Sample output:

```bash
python scripts/script.py --name compile_mjml_templates
2025-03-23 22:41:55 - script:compile_mjml_templates - INFO - Starting...
```


### Specific Requirements per Script

#### compile_mjml_templates.py

This script compiles the MJML templates into HTML. It requires that you have the `mjml` binary installed on your system.

```bash
npm install -g mjml
```

Find the path to your binary with

```bash
npm root -g
```

...and append to that the path to the `mjml` binary, then add it to the `MJML_BINARY` environment variable e.g.

```psh
$env:MJML_BINARY="C:\Users\ggroz\AppData\Roaming\npm\mjml.cmd"
```

or on Linux

```bash
export MJML_BINARY="/home/ggroz/.npm-global/bin/mjml"
```

> Note: The `MJML_BINARY` environment variable is only used when running the script from the command line.

#### generate_migration.py

Creates a timestamped migration file in `backend/migrations/`.

```bash
python scripts/script.py --name generate_migration
```

#### sync_blocked_email_domains.py

Synchronizes the blocked email domain table from its configured source.

```bash
python scripts/script.py --name sync_blocked_email_domains
```
