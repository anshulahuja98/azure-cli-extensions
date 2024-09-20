import json
from src.dataprotection.azext_dataprotection.manual.enums import CONST_RECOMMENDED
from azure.cli.core.commands.client_factory import get_mgmt_service_client

def dataprotection_enable_backup_helper(cmd, datasource_uri: str, backup_strategy=CONST_RECOMMENDED, configuration_params=None):
    # Do GET on exten
    print("Do GET on extension")
    print("datasourceUri: " + datasource_uri)
    print("backupStrategy: " + backup_strategy)
    print ("configurationParams: " + json.dumps(configuration_params))

    # extract subscriptoin ID from datasource_uri
    cluster_subscription_id = datasource_uri.split('/')[2]
    cluster_resource_group_name = datasource_uri.split('/')[4]
    cluster_name = datasource_uri.split('/')[8]

    storage_account_subscription_id = "f0c630e0-2995-4853-b056-0b3c09cb673f"
    storage_account_resource_group_name = "rg2eacanrraj"
    storage_account_name = "tinysarraj"
    storage_account_container_name = "container"

    backup_vault_subscription_id = "f0c630e0-2995-4853-b056-0b3c09cb673f"
    backup_vault_resource_group = "rgwerraj"
    backup_vault_name = "vaultwerraj"

    
    """ 
    - Create backup vault and policy in the cluster resource group*
    - Create backup resource group
    - Create backup storage account and container
    - Create backup extension
    - Create trusted access role binding
    - Assign all permissions
    - Create backup instance
    """

    storage_account_arm_id = __generate_arm_id(storage_account_subscription_id, storage_account_resource_group_name, "Microsoft.Storage/storageAccounts", storage_account_name)

    # backup_extension = __create_backup_extension(cmd, cluster_subscription_id, cluster_resource_group_name, cluster_name)
    from azure.cli.command_modules.role.custom import list_role_assignments, create_role_assignment

    create_role_assignment(
        cmd,
        assignee="e433a43c-9667-4e6a-9f73-8213565eb49e",
        # assignee=backup_extension.aks_assigned_identity.principal_id,
        role="Storage Blob Data Contributor",
        scope=storage_account_arm_id)



# Example usage
# __create_backup_storage_account_and_container(cli_ctx, "your_subscription_id", "your_resource_group_name", "your_storage_account_name", "your_container_name", "eastus")


# Example usage
# __create_resource_group(cli_ctx, "your_subscription_id", "your_resource_group_name", "eastus")

def __generate_arm_id(subscription_id, resource_group_name, resource_type, resource_name):
    return f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/{resource_type}/{resource_name}"

def __create_backup_extension(cmd, subscription_id, resource_group_name, cluster_name):
    from azext_dataprotection.vendored_sdks.azure_mgmt_kubernetesconfiguration import SourceControlConfigurationClient
    from azext_dataprotection.vendored_sdks.azure_mgmt_kubernetesconfiguration.v2023_05_01.models import Extension

    k8s_configuration_client = get_mgmt_service_client(cmd.cli_ctx, SourceControlConfigurationClient, subscription_id=subscription_id)

    extensions = k8s_configuration_client.extensions.list(
        cluster_rp="Microsoft.ContainerService",
        cluster_resource_name="managedClusters",
        resource_group_name=resource_group_name,
        cluster_name=cluster_name)    
    
    for page in extensions.by_page():
        for extension in page:
            if extension.extension_type.lower() == 'microsoft.dataprotection.kubernetes':
                print("Extension found: " + extension.name)
                break

    print("Creating backup extension...")
    
    from azure.cli.core.extension.operations import add_extension_to_path
    from importlib import import_module
    add_extension_to_path("k8s-extension")
    K8s_extension_client_factory = import_module("azext_k8s_extension._client_factory")
    k8s_extension_module = import_module("azext_k8s_extension.custom")

    # return k8s_extension_module.create_k8s_extension(
    #     cmd=cmd,
    #     client=K8s_extension_client_factory.cf_k8s_extension_operation(cmd.cli_ctx),
    #     resource_group_name=resource_group_name,
    #     cluster_name=cluster_name,
    #     name="azure-aks-backup",
    #     cluster_type="managedClusters",
    #     extension_type="microsoft.dataprotection.kubernetes",
    #     cluster_resource_provider="Microsoft.ContainerService",
    #     scope="cluster",
    #     auto_upgrade_minor_version=True,
    #     release_train="stable",
    #     configuration_settings=[{
    #         "blobContainer": "container",
    #         "storageAccount": "tinysarraj",
    #         "storageAccountResourceGroup": "rg2eacanrraj",
    #         "storageAccountSubscriptionId": "f0c630e0-2995-4853-b056-0b3c09cb673f"
    #     }]
    # ).result()
    

    # print(response)
    # print(response.result())

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
