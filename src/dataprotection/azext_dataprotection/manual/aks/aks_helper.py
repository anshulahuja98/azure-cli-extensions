import json
from src.dataprotection.azext_dataprotection.manual.enums import CONST_RECOMMENDED
from azure.cli.core.commands.client_factory import get_mgmt_service_client

def dataprotection_enable_backup_helper(cmd, datasource_id: str, backup_strategy=CONST_RECOMMENDED, configuration_params=None):
    print("datasourceId: " + datasource_id)
    print("backupStrategy: " + backup_strategy)
    print ("configurationParams: " + json.dumps(configuration_params))

    cluster_subscription_id = datasource_id.split('/')[2]
    cluster_resource_group_name = datasource_id.split('/')[4]
    cluster_name = datasource_id.split('/')[8]

    from azure.cli.command_modules.role.custom import create_role_assignment
    from azure.mgmt.resource import ResourceManagementClient

    resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceManagementClient, subscription_id=cluster_subscription_id)
    cluster_resource = resource_client.resources.get_by_id(datasource_id, api_version="2024-08-01")
    cluster_location = cluster_resource.location
    
    """ 
    - Create backup vault and policy in the cluster resource group*
    - Create backup resource group
    - Create backup storage account and container
    - Create backup extension
    - Create trusted access role binding
    - Assign all permissions
    - Create backup instance
    """
    
    backup_resource_group_name = __generate_backup_resource_group_name(cluster_location, cluster_name)
    print(f"Creating backup resource group ({backup_resource_group_name}) ...")
    backup_resource_group = resource_client.resource_groups.create_or_update(backup_resource_group_name, {"location": cluster_location})
    print(f"Assigning 'Contributor' role to the cluster identity on the backup resource group ({backup_resource_group_name}) ...")
    create_role_assignment(
        cmd,
        role="Contributor",
        assignee=cluster_resource.identity.principal_id,
        scope=backup_resource_group.id)

    from azure.mgmt.storage import StorageManagementClient
    storage_client = get_mgmt_service_client(cmd.cli_ctx, StorageManagementClient, subscription_id=cluster_subscription_id)
    backup_storage_account_name = __generate_backup_storage_account_name(cluster_location)
    print(f"Creating storage account ({backup_storage_account_name}) in the backup resource group ({backup_resource_group_name}) ...")
    backup_storage_account = storage_client.storage_accounts.begin_create(
        resource_group_name=backup_resource_group_name,
        account_name=backup_storage_account_name,
        parameters={
            "location": cluster_location,
            "kind": "StorageV2",
            "sku": {"name": "Standard_LRS"},
            "allow_blob_public_access": False
        }).result()
    
    backup_storage_account_container_name = __generate_backup_storage_account_container_name(cluster_name)
    print(f"Creating blob container ({backup_storage_account_container_name}) in the backup storage account ({backup_storage_account_name}) ...")
    storage_client.blob_containers.create(backup_resource_group_name, backup_storage_account_name, backup_storage_account_container_name, {})
 
    backup_extension = __create_backup_extension(
        cmd,
        cluster_subscription_id,
        cluster_resource_group_name,
        cluster_name,
        backup_storage_account_name,
        backup_storage_account_container_name,
        backup_resource_group_name,
        cluster_subscription_id)

    print(f"Assigning 'Storage Blob Data Contributor' role to the extension identity on the backup storage account ({backup_storage_account_name}) ...")
    create_role_assignment(
        cmd,
        role="Storage Blob Data Contributor",
        assignee=backup_extension.aks_assigned_identity.principal_id,
        scope=backup_storage_account.id)

    from azext_dataprotection.aaz.latest.dataprotection.backup_vault import Create as _BackupVaultCreate
    backup_vault_name = __generate_backup_vault_name(cluster_location)
    print(f"Creating backup vault ({backup_vault_name}) in the cluster resource group ({cluster_resource_group_name}) ...")
    backup_vault = _BackupVaultCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "vault_name": backup_vault_name,
        "resource_group": cluster_resource_group_name,
        "type": "SystemAssigned",
        "storage_setting": [{'type': 'LocallyRedundant', 'datastore-type': 'VaultStore'}]
    }).result()

    print(f"Assigning 'Reader' role to the backup vault identity on the cluster ({cluster_name}) ...")
    create_role_assignment(
        cmd,
        role="Reader",
        assignee=backup_vault["identity"]["principalId"],
        scope=cluster_resource.id)

    print(f"Assigning 'Reader' role to the backup vault identity on the backup resource group ({backup_resource_group_name}) ...")
    create_role_assignment(
        cmd,
        role="Reader",
        assignee=backup_vault["identity"]["principalId"],
        scope=backup_resource_group.id)
    
    print(f"Setting up trusted access between the cluster ({cluster_name}) and the backup vault ({backup_vault_name}) ...")
    from azext_dataprotection.vendored_sdks.azure_mgmt_containerservice import ContainerServiceClient
    from azext_dataprotection.vendored_sdks.azure_mgmt_containerservice.v2024_07_01.models import TrustedAccessRoleBinding

    cluster_client = get_mgmt_service_client(cmd.cli_ctx, ContainerServiceClient, subscription_id=cluster_subscription_id)
    _trusted_access_role_binding = TrustedAccessRoleBinding(
        source_resource_id=backup_vault["id"],
        roles=["Microsoft.DataProtection/backupVaults/backup-operator"])

    cluster_client.trusted_access_role_bindings.begin_create_or_update(
        resource_group_name=cluster_resource_group_name,
        resource_name=cluster_name,
        trusted_access_role_binding_name=__generate_trusted_access_role_binding_name(backup_vault_name),
        trusted_access_role_binding=_trusted_access_role_binding).result()

    print(f"Creating backup policy in the backup vault ({backup_vault_name}) ...")
    from azext_dataprotection.manual.aaz_operations.backup_policy import Create as _BackupPolicyCreate
    backup_policy_name = __generate_backup_policy_name()
    backup_policy = _BackupPolicyCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "backup_policy_name": backup_policy_name,
        "resource_group": cluster_resource_group_name,
        "vault_name": backup_vault_name,
        "policy": {
            "objectType": "BackupPolicy",
            "datasourceTypes": [
                "Microsoft.ContainerService/managedClusters"
            ],
            "policyRules": [
                {
                    "isDefault": True,
                    "lifecycles": [
                        {
                            "deleteAfter": {
                                "duration": "P1D",
                                "objectType": "AbsoluteDeleteOption"
                            },
                            "sourceDataStore": {
                                "dataStoreType": "OperationalStore",
                                "objectType": "DataStoreInfoBase"
                            },
                            "targetDataStoreCopySettings": []
                        }
                    ],
                    "name": "Default",
                    "objectType": "AzureRetentionRule"
                },
                {
                    "backupParameters": {
                        "backupType": "Incremental",
                        "objectType": "AzureBackupParams"
                    },
                    "dataStore": {
                        "dataStoreType": "OperationalStore",
                        "objectType": "DataStoreInfoBase"
                    },
                    "name": "BackupHourly",
                    "objectType": "AzureBackupRule",
                    "trigger": {
                        "objectType": "ScheduleBasedTriggerContext",
                        "schedule": {
                            "repeatingTimeIntervals": [
                                "R/2024-01-01T00:00:00+00:00/PT6H"
                            ],
                            "timeZone": "Coordinated Universal Time"
                        },
                        "taggingCriteria": [
                            {
                                "isDefault": True,
                                "tagInfo": {
                                    "id": "Default_",
                                    "tagName": "Default"
                                },
                                "taggingPriority": 99
                            }
                        ]
                    }
                }
            ]
        }
    })

    print(f"Running final validation and configuring backup for the cluster ({cluster_name}) ...")
    from azext_dataprotection.manual.aaz_operations.backup_instance import ValidateAndCreate as _BackupInstanceValidateAndCreate

    import uuid
    backup_instance_name = f"{cluster_name}-{uuid.uuid4()}"
    backup_instance = _BackupInstanceValidateAndCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "backup_instance_name": backup_instance_name,
        "resource_group": cluster_resource_group_name,
        "vault_name": backup_vault_name,
        "backup_instance": {
            "backup_instance_name": backup_instance_name,
            "properties": {
                "friendly_name": f"{cluster_name}\\fullbackup",
                "object_type": "BackupInstance",
                "data_source_info": {
                    "datasource_type": "Microsoft.ContainerService/managedClusters",
                    "object_type": "Datasource",
                    "resource_id": datasource_id,
                    "resource_location": cluster_location,
                    "resource_name": cluster_name,
                    "resource_type": "Microsoft.ContainerService/managedclusters",
                    "resource_uri": datasource_id
                },
                "data_source_set_info": {
                    "datasource_type": "Microsoft.ContainerService/managedClusters",
                    "object_type": "DatasourceSet",
                    "resource_id": datasource_id,
                    "resource_location": cluster_location,
                    "resource_name": cluster_name,
                    "resource_type": "Microsoft.ContainerService/managedclusters",
                    "resource_uri": datasource_id
                },
                "policy_info": {
                    "policy_id": backup_policy["id"],
                    # "policy_id": "/subscriptions/f0c630e0-2995-4853-b056-0b3c09cb673f/resourceGroups/rg2eacanrraj/providers/Microsoft.DataProtection/backupVaults/hackvault/backupPolicies/def",
                    "policy_parameters": {
                        "backup_datasource_parameters_list": [
                            {
                                "objectType": "KubernetesClusterBackupDatasourceParameters",
                                "include_cluster_scope_resources": True,
                                "snapshot_volumes": True
                            }
                        ],
                        "data_store_parameters_list": [
                            {
                                "object_type": "AzureOperationalStoreParameters",
                                "data_store_type": "OperationalStore",
                                "resource_group_id": backup_resource_group.id
                            }
                        ]
                    }
                }
            }
        }
    }).result()

    print(f"Kubernetes cluster ({cluster_name}) protected successfully.")

def __generate_arm_id(subscription_id, resource_group_name, resource_type, resource_name):
    return f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/{resource_type}/{resource_name}"

def __generate_backup_resource_group_name(cluster_location, cluster_name):
    return f"rg_azurebackup_{cluster_location}_{cluster_name}"

def __generate_backup_storage_account_name(cluster_location):
    return f"kubernetesbackup{cluster_location}"

def __generate_backup_storage_account_container_name(cluster_name):
    return f"backup-{cluster_name}"

def __generate_backup_vault_name(cluster_location):
    return f"backupvault-{cluster_location}"

def __generate_backup_policy_name():
    return f"defaultbackuppolicy"

def __generate_trusted_access_role_binding_name(backup_vault_name):
    return f"backup-howtogetid"

def __create_backup_extension(cmd, subscription_id, resource_group_name, cluster_name, storage_account_name, storage_account_container_name, storage_account_resource_group, storage_account_subscription_id):
    from azext_dataprotection.vendored_sdks.azure_mgmt_kubernetesconfiguration import SourceControlConfigurationClient
    k8s_configuration_client = get_mgmt_service_client(cmd.cli_ctx, SourceControlConfigurationClient, subscription_id=subscription_id)

    extensions = k8s_configuration_client.extensions.list(
        cluster_rp="Microsoft.ContainerService",
        cluster_resource_name="managedClusters",
        resource_group_name=resource_group_name,
        cluster_name=cluster_name)    
    
    for page in extensions.by_page():
        for extension in page:
            if extension.extension_type.lower() == 'microsoft.dataprotection.kubernetes':
                print(f"Data protection extension ({extension.name}) is already installed in the cluster ({cluster_name}).")
                return extension

    print(f"Installing data protection extension (azure-aks-backup) in the cluster ({cluster_name}) ...")
    
    from azure.cli.core.extension.operations import add_extension_to_path
    from importlib import import_module
    add_extension_to_path("k8s-extension")
    K8s_extension_client_factory = import_module("azext_k8s_extension._client_factory")
    k8s_extension_module = import_module("azext_k8s_extension.custom")

    return k8s_extension_module.create_k8s_extension(
        cmd=cmd,
        client=K8s_extension_client_factory.cf_k8s_extension_operation(cmd.cli_ctx),
        resource_group_name=resource_group_name,
        cluster_name=cluster_name,
        name="azure-aks-backup",
        cluster_type="managedClusters",
        extension_type="microsoft.dataprotection.kubernetes",
        cluster_resource_provider="Microsoft.ContainerService",
        scope="cluster",
        auto_upgrade_minor_version=True,
        release_train="stable",
        configuration_settings=[{
            "blobContainer": storage_account_container_name,
            "storageAccount": storage_account_name,
            "storageAccountResourceGroup": storage_account_resource_group,
            "storageAccountSubscriptionId": storage_account_subscription_id
        }]
    ).result()

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
