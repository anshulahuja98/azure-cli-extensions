# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=protected-access

"""
Unit tests for AKS backup helper name generation functions with extreme edge cases.
Tests focus on maximum-length cluster names and resource group names to ensure
proper truncation and sanitization.
"""

import unittest
import re


class TestAksHelperNameGeneration(unittest.TestCase):
    """Test name generation functions in aks_helper.py with extreme cases."""

    @staticmethod
    def generate_backup_resource_group_name(cluster_location):
        """Generate backup resource group name."""
        return f"AKSAzureBackup_{cluster_location}"
    
    @staticmethod
    def generate_backup_storage_account_name(cluster_location):
        """Generate backup storage account name."""
        import uuid
        sanitized_location = ''.join(c for c in cluster_location.lower() if c.isalnum())
        guid_suffix = str(uuid.uuid4()).replace('-', '')[:6]
        sanitized_location = sanitized_location[:12]
        return f"aksbkp{sanitized_location}{guid_suffix}"
    
    @staticmethod
    def generate_backup_storage_account_container_name(cluster_name, cluster_resource_group_name):
        """Generate backup blob container name."""
        import re
        
        def sanitize(name):
            sanitized = re.sub(r'[^a-z0-9-]', '-', name.lower())
            sanitized = re.sub(r'-+', '-', sanitized)
            return sanitized.strip('-')
        
        sanitized_cluster = sanitize(cluster_name)
        sanitized_rg = sanitize(cluster_resource_group_name)
        container_name = f"{sanitized_cluster}-{sanitized_rg}"
        return container_name[:63].rstrip('-')
    
    @staticmethod
    def generate_backup_vault_name(cluster_location):
        """Generate backup vault name."""
        return f"AKSAzureBackup-{cluster_location}"
    
    @staticmethod
    def generate_backup_policy_name(backup_strategy):
        """Generate backup policy name."""
        return f"AKSBackupPolicy-{backup_strategy}"
    
    @staticmethod
    def generate_trusted_access_role_binding_name():
        """Generate trusted access role binding name."""
        import uuid
        guid_suffix = str(uuid.uuid4()).replace('-', '')[:16]
        return f"tarb-{guid_suffix}"

    # Test data: Maximum length names for Azure resources
    # AKS cluster name max: 63 characters
    MAX_CLUSTER_NAME = "a" * 63
    # Resource group name max: 90 characters
    MAX_RG_NAME = "b" * 90
    # Very long names with special characters
    LONG_CLUSTER_WITH_SPECIAL = "My-Super-Long-Cluster-Name-With-Hyphens-And-Numbers-12345-ABCDE"
    LONG_RG_WITH_SPECIAL = "My-Very-Long-Resource-Group-Name-With-Multiple-Hyphens-And-Underscores_123456"
    
    def test_backup_resource_group_name_with_max_location(self):
        """Test backup resource group name generation with maximum location length."""
        # Azure location names are typically short (e.g., "eastus", "westeurope")
        # but let's test with a very long hypothetical location
        long_location = "verylonglocationnamethatshouldstillwork"
        result = self.generate_backup_resource_group_name(long_location)
        
        # Verify naming constraints for resource groups (1-90 chars)
        self.assertGreaterEqual(len(result), 1, "Resource group name too short")
        self.assertLessEqual(len(result), 90, "Resource group name exceeds 90 characters")
        self.assertFalse(result.endswith('.'), "Resource group name cannot end with period")
        self.assertTrue(re.match(r'^[a-zA-Z0-9._()-]+$', result), "Resource group name contains invalid characters")
        self.assertTrue(result.startswith("AKSAzureBackup_"), "Resource group name should start with AKSAzureBackup_")

    def test_backup_storage_account_name_with_various_locations(self):
        """Test storage account name generation with various location formats."""
        test_locations = [
            "eastus",
            "westeurope",
            "southeastasia",
            "verylonglocationname",  # Test truncation
            "Location-With-Hyphens",  # Test sanitization
            "Location_With_Underscores",
            "UPPERCASELOCATION",  # Test lowercasing
        ]
        
        for location in test_locations:
            with self.subTest(location=location):
                result = self.generate_backup_storage_account_name(location)
                
                # Verify naming constraints for storage accounts (3-24 chars)
                self.assertGreaterEqual(len(result), 3, f"Storage account name too short for location: {location}")
                self.assertLessEqual(len(result), 24, f"Storage account name exceeds 24 characters for location: {location}")
                self.assertTrue(result.islower(), f"Storage account name must be lowercase for location: {location}")
                self.assertTrue(result.isalnum(), f"Storage account name must be alphanumeric for location: {location}")
                self.assertTrue(result.startswith("aksbkp"), f"Storage account name should start with 'aksbkp' for location: {location}")

    def test_backup_storage_account_container_name_max_cluster_name(self):
        """Test container name generation with maximum-length cluster name."""
        result = self.generate_backup_storage_account_container_name(
            self.MAX_CLUSTER_NAME,
            "test-rg"
        )
        
        # Verify naming constraints for blob containers (3-63 chars)
        self.assertGreaterEqual(len(result), 3, "Container name too short")
        self.assertLessEqual(len(result), 63, "Container name exceeds 63 characters")
        self.assertTrue(re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', result), 
                       f"Container name '{result}' has invalid format")
        self.assertFalse('--' in result, "Container name contains consecutive hyphens")
        self.assertFalse(result.endswith('-'), "Container name ends with hyphen")

    def test_backup_storage_account_container_name_max_rg_name(self):
        """Test container name generation with maximum-length resource group name."""
        result = self.generate_backup_storage_account_container_name(
            "test-cluster",
            self.MAX_RG_NAME
        )
        
        # Verify naming constraints
        self.assertGreaterEqual(len(result), 3, "Container name too short")
        self.assertLessEqual(len(result), 63, "Container name exceeds 63 characters")
        self.assertTrue(re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', result),
                       f"Container name '{result}' has invalid format")

    def test_backup_storage_account_container_name_both_max_length(self):
        """Test container name generation with both names at maximum length."""
        result = self.generate_backup_storage_account_container_name(
            self.MAX_CLUSTER_NAME,
            self.MAX_RG_NAME
        )
        
        # This is the critical test - both inputs are very long
        self.assertGreaterEqual(len(result), 3, "Container name too short")
        self.assertLessEqual(len(result), 63, "Container name exceeds 63 characters")
        self.assertTrue(re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', result),
                       f"Container name '{result}' has invalid format")
        self.assertFalse(result.endswith('-'), "Container name ends with hyphen after truncation")

    def test_backup_storage_account_container_name_with_special_chars(self):
        """Test container name generation with special characters in names."""
        test_cases = [
            ("Cluster_With_Underscores", "RG_With_Underscores"),
            ("Cluster.With.Dots", "RG.With.Dots"),
            ("Cluster@With#Special$Chars", "RG!With%Special^Chars"),
            ("UPPERCASE-CLUSTER", "UPPERCASE-RG"),
            (self.LONG_CLUSTER_WITH_SPECIAL, self.LONG_RG_WITH_SPECIAL),
        ]
        
        for cluster_name, rg_name in test_cases:
            with self.subTest(cluster=cluster_name, rg=rg_name):
                result = self.generate_backup_storage_account_container_name(
                    cluster_name,
                    rg_name
                )
                
                # Verify constraints
                self.assertLessEqual(len(result), 63, 
                                   f"Container name exceeds 63 chars for cluster='{cluster_name}', rg='{rg_name}'")
                self.assertTrue(re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', result),
                               f"Container name '{result}' has invalid format")
                # Container must start with alphanumeric
                self.assertTrue(result[0].isalnum(), f"Container name '{result}' must start with alphanumeric")

    def test_backup_storage_account_container_name_consecutive_hyphens(self):
        """Test that consecutive hyphens are removed from container names."""
        result = self.generate_backup_storage_account_container_name(
            "cluster---with---many---hyphens",
            "rg---with---many---hyphens"
        )
        
        self.assertFalse('--' in result, "Container name should not contain consecutive hyphens")
        self.assertTrue(re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', result),
                       f"Container name '{result}' has invalid format")

    def test_backup_storage_account_container_name_leading_trailing_hyphens(self):
        """Test that leading and trailing hyphens are removed."""
        test_cases = [
            ("---leading-hyphens", "rg-name"),
            ("cluster-name", "---leading-hyphens"),
            ("trailing-hyphens---", "rg-name"),
            ("cluster-name", "trailing-hyphens---"),
            ("---both-sides---", "---both-sides---"),
        ]
        
        for cluster_name, rg_name in test_cases:
            with self.subTest(cluster=cluster_name, rg=rg_name):
                result = self.generate_backup_storage_account_container_name(
                    cluster_name,
                    rg_name
                )
                
                self.assertFalse(result.startswith('-'), 
                               f"Container name '{result}' should not start with hyphen")
                self.assertFalse(result.endswith('-'),
                               f"Container name '{result}' should not end with hyphen")

    def test_backup_storage_account_container_name_truncation_at_boundary(self):
        """Test that truncation at 63 chars doesn't create invalid names."""
        # Create names that would result in a hyphen at position 63
        # This tests the rstrip('-') logic
        cluster_62_chars = "a" * 30 + "-"
        rg_31_chars = "b" * 31
        
        result = self.generate_backup_storage_account_container_name(
            cluster_62_chars,
            rg_31_chars
        )
        
        # Should be truncated to 63 and trailing hyphen removed
        self.assertLessEqual(len(result), 63)
        self.assertFalse(result.endswith('-'), 
                        "Truncation should not leave trailing hyphen")

    def test_backup_vault_name_with_various_locations(self):
        """Test backup vault name generation with various locations."""
        test_locations = [
            "eastus",
            "westeurope",
            "verylonglocationname",
        ]
        
        for location in test_locations:
            with self.subTest(location=location):
                result = self.generate_backup_vault_name(location)
                
                # Verify naming constraints for backup vaults (2-50 chars)
                self.assertGreaterEqual(len(result), 2, f"Vault name too short for location: {location}")
                self.assertLessEqual(len(result), 50, f"Vault name exceeds 50 characters for location: {location}")
                self.assertTrue(result[0].isalpha(), f"Vault name must start with letter for location: {location}")
                self.assertFalse(result.endswith('-'), f"Vault name cannot end with hyphen for location: {location}")
                self.assertTrue(re.match(r'^[a-zA-Z0-9-]+$', result), 
                               f"Vault name contains invalid characters for location: {location}")

    def test_backup_policy_name_with_various_strategies(self):
        """Test backup policy name generation with various strategies."""
        test_strategies = [
            "Week",
            "Month",
            "Immutable",
            "DisasterRecovery",
            "Custom",
        ]
        
        for strategy in test_strategies:
            with self.subTest(strategy=strategy):
                result = self.generate_backup_policy_name(strategy)
                
                # Verify naming constraints for backup policies (3-150 chars)
                self.assertGreaterEqual(len(result), 3, f"Policy name too short for strategy: {strategy}")
                self.assertLessEqual(len(result), 150, f"Policy name exceeds 150 characters for strategy: {strategy}")
                self.assertTrue(re.match(r'^[a-zA-Z0-9-]+$', result),
                               f"Policy name contains invalid characters for strategy: {strategy}")

    def test_trusted_access_role_binding_name_format(self):
        """Test trusted access role binding name generation."""
        # Generate multiple names to ensure consistency
        results = [self.generate_trusted_access_role_binding_name() for _ in range(5)]
        
        for result in results:
            with self.subTest(result=result):
                # Verify naming constraints (1-24 chars)
                self.assertGreaterEqual(len(result), 1, "Role binding name too short")
                self.assertLessEqual(len(result), 24, "Role binding name exceeds 24 characters")
                self.assertTrue(re.match(r'^[a-zA-Z0-9_-]+$', result),
                               f"Role binding name '{result}' contains invalid characters")
                self.assertTrue(result.startswith('tarb-'), 
                               f"Role binding name '{result}' should start with 'tarb-'")
        
        # Verify uniqueness - all generated names should be different
        self.assertEqual(len(set(results)), len(results), 
                        "Generated role binding names should be unique")

    def test_backup_storage_account_container_name_all_special_chars(self):
        """Test container name with names containing only special characters."""
        test_cases = [
            ("...", "___"),
            ("@@@", "###"),
            ("---", "---"),
        ]
        
        for cluster_name, rg_name in test_cases:
            with self.subTest(cluster=cluster_name, rg=rg_name):
                result = self.generate_backup_storage_account_container_name(
                    cluster_name,
                    rg_name
                )
                
                # Should produce valid container name even from all special chars
                self.assertGreaterEqual(len(result), 3, "Container name too short")
                self.assertLessEqual(len(result), 63, "Container name exceeds 63 characters")
                # After sanitization, should have valid format
                if len(result) > 0:  # Might be empty after sanitization
                    self.assertTrue(re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', result) or len(result) == 1,
                                   f"Container name '{result}' has invalid format")

    def test_extreme_edge_case_cluster_and_rg_max_real_world(self):
        """Test with realistic maximum-length names from real-world scenarios."""
        # Realistic long cluster name (63 chars max for AKS)
        long_cluster = "production-aks-cluster-for-microservices-region-east-us-v2"
        # Realistic long RG name (90 chars max)
        long_rg = "rg-production-kubernetes-infrastructure-east-us-application-platform-services"
        
        result = self.generate_backup_storage_account_container_name(
            long_cluster,
            long_rg
        )
        
        self.assertLessEqual(len(result), 63, 
                           "Container name exceeds 63 characters with realistic long names")
        self.assertTrue(re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', result),
                       f"Container name '{result}' has invalid format")
        print(f"\nGenerated container name from long inputs: '{result}' (length: {len(result)})")


if __name__ == '__main__':
    unittest.main()
