// ==============================================================================
// Edge Optimizer - Azure Policy Assignments for Management Group
// ==============================================================================
// Creates Policy Assignments for subscription governance
//
// PREREQUISITES:
// 1. Management Group 'eo-re-d1-azure-mgmt-grp' must exist
//    (Deploy eo-re-d1-azure-mgmt-grp.bicep first)
//
// DEPLOYMENT:
// This template requires MANAGEMENT GROUP scope deployment:
//   az deployment mg create \
//     --location japaneast \
//     --management-group-id eo-re-d1-azure-mgmt-grp \
//     --template-file eo-re-d1-azure-mgmt-grp-policies.bicep
//
// POST-DEPLOYMENT:
// 1. Verify policy assignments in Azure Portal
// 2. Deploy eo-re-d1-azure-funcapp.bicep to resource group under this subscription
//
// ==============================================================================

targetScope = 'managementGroup'

// ==============================================================================
// Parameters
// ==============================================================================

// --- Policy Settings (README: EO_AZ_* 環境変数と統一) ---
@description('ポリシーでデプロイを許可するリージョン。README: EO_AZ_LOCATIONS')
param EO_AZ_LOCATIONS array = [
  'japaneast'
]

@description('ポリシーでデプロイを許可するリソースタイプ。README: EO_AZ_RESOURCE_TYPES')
param EO_AZ_RESOURCE_TYPES array = [
  'Microsoft.Web/sites'
  'Microsoft.Web/serverFarms'
  'Microsoft.KeyVault/vaults'
  'Microsoft.Storage/storageAccounts'
]

@description('Enable Application Insights for monitoring (optional). README: EO_AZ_ENABLE_APPLICATION_INSIGHTS')
param EO_AZ_ENABLE_APPLICATION_INSIGHTS bool = false

@description('デプロイ先リージョン制限用の組み込みポリシー定義 ID。Azure 組み込み "Allowed locations" の ID を指定すること。')
param EO_AZ_POLICY_REGIONS_DEFINITION_ID string = '<デプロイ先リージョン制限のポリシー定義ID>'

@description('デプロイ可能リソースタイプ制限用の組み込みポリシー定義 ID。Azure 組み込み "Allowed resource types" の ID を指定すること。')
param EO_AZ_POLICY_RESOURCE_TYPES_DEFINITION_ID string = '<デプロイ可能リソースタイプ制限のポリシー定義ID>'

// ==============================================================================
// Variables
// ==============================================================================
// Management Group: デプロイスコープの名前は managementGroup().name で参照（README: EO_AZ_CHILD_MANAGEMENT_GROUP_ID と一致）

// デプロイ先リージョン制限用ポリシー割り当ての名前（README の EO_AZ_* 命名に合わせる）
var EO_AZ_POLICY_REGIONS_NAME = 'eo-re-d1-allowed-locations'
// デプロイ可能リソースタイプ制限用ポリシー割り当ての名前
var EO_AZ_POLICY_RESOURCE_TYPES_NAME = 'eo-re-d1-allowed-resource-types'

// 上記パラメータで受け取ったポリシー定義 ID（フルパスで参照）
var EO_AZ_POLICY_REGIONS_ID = concat('/providers/Microsoft.Authorization/policyDefinitions/', EO_AZ_POLICY_REGIONS_DEFINITION_ID)
var EO_AZ_POLICY_RESOURCE_TYPES_ID = concat('/providers/Microsoft.Authorization/policyDefinitions/', EO_AZ_POLICY_RESOURCE_TYPES_DEFINITION_ID)

// リソースタイプ制限用ポリシーに渡す一覧（Application Insights 有効時は Microsoft.Insights/components を追加）
var EO_AZ_RESOURCE_TYPES_FOR_ASSIGNMENT = EO_AZ_ENABLE_APPLICATION_INSIGHTS
  ? concat(EO_AZ_RESOURCE_TYPES, ['Microsoft.Insights/components'])
  : EO_AZ_RESOURCE_TYPES

// ==============================================================================
// Resources
// ==============================================================================

// ============================================================================
// Policy Assignment: デプロイ先リージョン制限
// ============================================================================
resource allowedLocationsPolicy 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: EO_AZ_POLICY_REGIONS_NAME
  properties: {
    displayName: 'Allowed locations for ${managementGroup().name}'
    description: '[Azure Policy制限] プロジェクト管理ルールにより、${join(EO_AZ_LOCATIONS, ', ')} 以外のリージョンへのデプロイは許可されていません。'
    policyDefinitionId: EO_AZ_POLICY_REGIONS_ID
    enforcementMode: 'Default'
    parameters: {
      listOfAllowedLocations: {
        value: EO_AZ_LOCATIONS
      }
    }
    nonComplianceMessages: [
      {
        message: '[Azure Policy制限] プロジェクト管理ルールにより、${join(EO_AZ_LOCATIONS, ', ')} 以外のリージョンへのデプロイは許可されていません。追加が必要な場合、該当管理グループのポリシー設定を確認してください。'
      }
    ]
  }
}

// ============================================================================
// Policy Assignment: デプロイ可能リソースタイプ制限
// ============================================================================
resource allowedResourceTypesPolicy 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: EO_AZ_POLICY_RESOURCE_TYPES_NAME
  properties: {
    displayName: 'Allowed resource types for ${managementGroup().name}'
    description: '[Azure Policy制限] プロジェクト管理ルールにより、許可されたリソースタイプ以外はデプロイできません。'
    policyDefinitionId: EO_AZ_POLICY_RESOURCE_TYPES_ID
    enforcementMode: 'Default'
    parameters: {
      listOfResourceTypesAllowed: {
        value: EO_AZ_RESOURCE_TYPES_FOR_ASSIGNMENT
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
output configuredAllowedLocations array = EO_AZ_LOCATIONS

@description('Allowed resource types configured')
output configuredAllowedResourceTypes array = EO_AZ_RESOURCE_TYPES_FOR_ASSIGNMENT
