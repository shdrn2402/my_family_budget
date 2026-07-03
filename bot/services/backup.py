import os
import subprocess
import tempfile
import yaml
import logging
from datetime import datetime
from bot.config import Config
from bot.database import get_all_item_aliases

logger = logging.getLogger(__name__)

async def create_database_dump() -> str | None:
    """
    Creates a PostgreSQL database dump using pg_dump.
    Returns the file path to the dump or None if it failed.
    """
    try:
        backup_dir = "/app/backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(backup_dir, f"db_backup_{timestamp}.sql")
        
        env = os.environ.copy()
        if Config.DB_PASSWORD:
            env["PGPASSWORD"] = Config.DB_PASSWORD
            
        cmd = [
            "pg_dump",
            "-h", Config.DB_HOST,
            "-p", str(Config.DB_PORT),
            "-U", Config.DB_USER,
            "-d", Config.DB_NAME,
            "-F", "p", # Plain text SQL
            "-f", filepath
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"pg_dump failed: {result.stderr}")
            return None
            
        return filepath
    except Exception as e:
        logger.error(f"Error creating database dump: {e}")
        return None

async def export_aliases_to_yaml() -> str | None:
    """
    Exports the current item_aliases table to a YAML file compatible with seed_data.sql.
    Returns the file path to the yaml or None if it failed.
    """
    try:
        aliases_dict = await get_all_item_aliases()
        if not aliases_dict:
            logger.warning("No aliases found in database.")
            aliases_dict = {}
            
        # The dictionary is currently {name: category_id}. 
        # We need to reverse the mapping to {category_id: [name1, name2, ...]}
        reversed_mapping = {}
        for name, cat_id in aliases_dict.items():
            if cat_id not in reversed_mapping:
                reversed_mapping[cat_id] = []
            reversed_mapping[cat_id].append(name)
            
        # Format for YAML output
        yaml_data = {"aliases": reversed_mapping}
        
        backup_dir = "/app/backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(backup_dir, f"aliases_backup_{timestamp}.yaml")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
            
        return filepath
    except Exception as e:
        logger.error(f"Error exporting aliases to yaml: {e}")
        return None
