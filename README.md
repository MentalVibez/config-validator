# Config Validation Suite

A lightweight toolkit for validating configuration files across JSON, TOML, and INI formats. The
suite helps teams catch configuration drift before it hits production by combining structural checks
with easy-to-read reports.

## Why use the Config Validation Suite?

- **Confidence before deployment:** detect invalid or missing settings long before they reach
  production systems.
- **Consistent validation rules:** reuse the same schema across different environments and config
  formats.
- **Automation friendly:** ships with a CLI designed for CI pipelines and local development alike.

## Step-by-step: Validate a configuration file

1. **Install the project in a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Create or locate the configuration file you want to validate**. The suite supports `.json`,
   `.toml`, and `.ini` files.

3. **Optionally describe the expected structure** in a JSON schema subset. Save the schema to a file
   (for example `schema.json`):

   ```json
   {
     "type": "object",
     "required": ["service", "database"],
     "properties": {
       "service": {
         "type": "object",
         "required": ["host", "port"],
         "properties": {
           "host": {"type": "string"},
           "port": {"type": "integer"}
         }
       },
       "database": {
         "type": "object",
         "required": ["url"],
         "properties": {
           "url": {"type": "string"}
         }
       },
       "debug": {"type": "boolean"}
     }
   }
   ```

4. **Run the validator** against your config and optional schema:

   ```bash
   config-validator path/to/config.toml --schema schema.json
   ```

   The command prints a concise PASS/FAIL summary followed by detailed error or warning messages.

5. **Integrate into automation** by adding the same command to CI workflows or deployment scripts. A
   non-zero exit code signals validation failure, making it easy to gate releases on healthy
   configuration files.

## Project layout

```
.
├── README.md
├── pyproject.toml
└── src/
    └── config_validator/
        ├── __init__.py
        ├── cli.py
        └── suite.py
```

## Next steps

- Extend the schema subset with custom validators tailored to your applications.
- Add regression tests that feed known-good and known-bad configs through the suite.
- Publish the package to your internal package index for reuse across services.
