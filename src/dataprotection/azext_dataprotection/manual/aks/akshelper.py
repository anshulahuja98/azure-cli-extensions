import json
from src.dataprotection.azext_dataprotection.manual.enums import CONST_RECOMMENDED
from azure.identity import DefaultAzureCredential
from azure.mgmt.kubernetesconfiguration import SourceControlConfigurationClient


def dataprotection_enable_backup_helper(cli_ctx, datasource_uri: str, backup_strategy=CONST_RECOMMENDED, configuration_params=None):
    # Do GET on exten
    print("Do GET on extension")
    print("datasourceUri: " + datasource_uri)
    print("backupStrategy: " + backup_strategy)
    print ("configurationParams: " + json.dumps(configuration_params))

    # extract subscriptoin ID from datasource_uri
    clusterSubscriptionId = datasource_uri.split('/')[2]
    clusterResourceGroup = datasource_uri.split('/')[4]
    clusterName = datasource_uri.split('/')[8]

    extension = __get_extension(cli_ctx, subscription_id=clusterSubscriptionId, resource_group=clusterResourceGroup, cluster_name=clusterName)

def __get_extension(cli_ctx, subscription_id, resource_group, cluster_name):   
     # https://learn.microsoft.com/en-us/python/api/overview/azure/mgmt-kubernetesconfiguration-readme?view=azure-python
     # use cli_ctx to make credential object
    # client = SourceControlConfigurationClient(credential=DefaultAzureCredential)
    # client = SourceControlConfigurationClient(credential=DefaultAzureCredential(), subscription_id=subscription_id)
    # extensions = client.extensions.list(cluster_rp="Microsoft.ContainerService", cluster_resource_name="ManagedClusters", resource_group_name=resource_group, cluster_name=cluster_name)    # iterate and find the extension of type dataprotection.microsoft
    # seriliaze cli_ctx and print
    print(cli_ctx.)
    # if len(extensions) == 0:
    #     print("No extensions found")
    # else:
    #     for extension in extensions:
    #         if extension.extension_type.lower() == 'microsoft.dataprotection.kubernetes':
    #             print("Extension found: " + extension.name)                  
    # 
    # Check if there is an SA in cluster RG with azure tag - clusterName = backup
    # If not, create one with name bkp- (4)<clustername without -> (4) sha256 of cluster URI             
    #
    #
    # 
    #  P2  - Using Extension routing, if there is a BI already for the cluster. If there, is print the vault name where it resides. (this can be the very first step)
    #
    #
    # Check if there is a backupvault in the subscription with tag, default=true
    #
    # If there is no such backup vault, create a resource group with tag backup-resource-group=true
    # Create a backup vault in the resource group with tag default=true
    #
    # Check if the Vault has a policy with params matching Recommended Policy params
    #
    # 
    # 
    #
