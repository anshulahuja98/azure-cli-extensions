# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AKS Backup Strategy Constants
CONST_BACKUP_STRATEGY_WEEK = "Week"
CONST_BACKUP_STRATEGY_MONTH = "Month"
CONST_BACKUP_STRATEGY_IMMUTABLE = "Immutable"
CONST_BACKUP_STRATEGY_DISASTER_RECOVERY = "DisasterRecovery"
CONST_BACKUP_STRATEGY_CUSTOM = "Custom"

# List of all backup strategies for AKS
CONST_AKS_BACKUP_STRATEGIES = [
    CONST_BACKUP_STRATEGY_WEEK,
    CONST_BACKUP_STRATEGY_MONTH,
    CONST_BACKUP_STRATEGY_IMMUTABLE,
    CONST_BACKUP_STRATEGY_DISASTER_RECOVERY,
    CONST_BACKUP_STRATEGY_CUSTOM,
]

# API Versions
CONST_DATAPROTECTION_API_VERSION = "2024-04-01"
CONST_AKS_API_VERSION = "2024-08-01"

# Resource Types
CONST_AKS_RESOURCE_TYPE = "Microsoft.ContainerService/managedClusters"
CONST_DATAPROTECTION_RESOURCE_TYPE = "Microsoft.DataProtection/backupVaults"
CONST_STORAGE_RESOURCE_TYPE = "Microsoft.Storage/storageAccounts"
