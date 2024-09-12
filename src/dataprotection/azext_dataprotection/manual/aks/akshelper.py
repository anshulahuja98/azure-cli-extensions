import json
from src.dataprotection.azext_dataprotection.manual.enums import CONST_RECOMMENDED

def dataprotection_enable_backup_helper(datasource_uri: str, backup_strategy=CONST_RECOMMENDED, configuration_params=None):
    # Do GET on exten
    print("Do GET on extension")
    print("datasourceUri: " + datasource_uri)
    print("backupStrategy: " + backup_strategy)
    print ("configurationParams: " + json.dumps(configuration_params))
