// ==============================================================================
// Edge Optimizer - Azure Policy Assignments for Management Group
// ==============================================================================
// Creates Policy Assignments for subscription governance
//
// PREREQUISITES:
// 1. Management Group 'eo-re-d01-azure-mgmt-group' must exist
//    (Deploy eo-re-d01-azure-mgmt-group.bicep first)
//
// DEPLOYMENT:
// This template requires MANAGEMENT GROUP scope deployment:
//   az deployment mg create \
//     --location japaneast \
//     --management-group-id eo-re-d01-azure-mgmt-group \
//     --template-file eo-re-d01-azure-mgmt-group-policies.bicep
//
// POST-DEPLOYMENT:
// 1. Verify policy assignments in Azure Portal
// 2. Deploy eo-re-d01-azure-funcapp.bicep to resource group under this subscription
//
// ==============================================================================

targetScope = 'managementGroup'

// ==============================================================================
// Parameters
// ==============================================================================

// --- Policy Settings ---
@description('Allowed Azure locations for resources')
param allowedLocations array = [
  'japaneast'
]

@description('Allowed resource types for deployment')
param allowedResourceTypes array = [
  'Microsoft.Web/sites'
  'Microsoft.Web/serverFarms'
  'Microsoft.KeyVault/vaults'
  'Microsoft.Storage/storageAccounts'
]

@description('Enable Application Insights for monitoring (optional)')
param enableApplicationInsights bool = false

// ==============================================================================
// Variables
// ==============================================================================

// Management Group name (must match the deployed management group)
var managementGroupName = 'eo-re-d01-azure-mgmt-group'

// Policy assignment names
var allowedLocationsAssignmentName = 'eo-re-d01-allowed-locations'
var allowedResourceTypesAssignmentName = 'eo-re-d01-allowed-resource-types'

// Built-in Policy Definition IDs
// Reference: https://learn.microsoft.com/en-us/azure/governance/policy/samples/built-in-policies
var allowedLocationsPolicyId = '/providers/Microsoft.Authorization/policyDefinitions/e56962a6-4747-49cd-b67b-bf8b01975c4c'
var allowedResourceTypesPolicyId = '/providers/Microsoft.Authorization/policyDefinitions/a08ec900-254a-4555-9bf5-e42af04b5c5c'

// Conditionally add Application Insights to allowed resource types
var finalAllowedResourceTypes = enableApplicationInsights
  ? concat(allowedResourceTypes, ['Microsoft.Insights/components'])
  : allowedResourceTypes

// ==============================================================================
// Resources
// ==============================================================================

// ============================================================================
// Policy Assignment: Allowed Locations
// ============================================================================
resource allowedLocationsPolicy 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: allowedLocationsAssignmentName
  properties: {
    displayName: 'Allowed locations for ${managementGroupName}'
    description: '[Azure Policy制限] プロジェクト管理ルールにより、${join(allowedLocations, ', ')} 以外のリージョンへのデプロイは許可されていません。'
    policyDefinitionId: allowedLocationsPolicyId
    enforcementMode: 'Default'
    parameters: {
      listOfAllowedLocations: {
        value: allowedLocations
      }
    }
    nonComplianceMessages: [
      {
        message: '[Azure Policy制限] プロジェクト管理ルールにより、${join(allowedLocations, ', ')} 以外のリージョンへのデプロイは許可されていません。追加が必要な場合、該当管理グループのポリシー設定を確認してください。'
      }
    ]
  }
}

// ============================================================================
// Policy Assignment: Allowed Resource Types
// ============================================================================
resource allowedResourceTypesPolicy 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: allowedResourceTypesAssignmentName
  properties: {
    displayName: 'Allowed resource types for ${managementGroupName}'
    description: '[Azure Policy制限] プロジェクト管理ルールにより、許可されたリソースタイプ以外はデプロイできません。'
    policyDefinitionId: allowedResourceTypesPolicyId
    enforcementMode: 'Default'
    parameters: {
      listOfResourceTypesAllowed: {
        value: finalAllowedResourceTypes
      }
    }
    nonComplianceMessages: [
      {
        message: '[Azure Policy制限] プロジェクト管理ルールにより、許可されたリソースタイプ以外はデプロイできません。追加が必要な場合、該当管理グループのポリシー設定を確認してください。'
      }
    ]
  }
}

// ==============================================================================
// Outputs
// ==============================================================================

@description('Allowed Locations Policy Assignment ID')
output allowedLocationsPolicyAssignmentId string = allowedLocationsPolicy.id

@description('Allowed Resource Types Policy Assignment ID')
output allowedResourceTypesPolicyAssignmentId string = allowedResourceTypesPolicy.id

@description('Allowed locations configured')
output configuredAllowedLocations array = allowedLocations

@description('Allowed resource types configured')
output configuredAllowedResourceTypes array = finalAllowedResourceTypes
