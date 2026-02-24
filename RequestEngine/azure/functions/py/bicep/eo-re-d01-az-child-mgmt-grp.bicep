// ==============================================================================
// Edge Optimizer - Azure Management Group Infrastructure
// ==============================================================================
// Creates Management Group and assigns subscription
//
// PREREQUISITES:
// 1. Azure AD Global Administrator role
// 2. "Azure リソースのアクセス管理" enabled in Entra ID properties
//    (Entra ID > プロパティ > Azure リソースのアクセス管理 > はい)
//
// DEPLOYMENT:
// This template requires TENANT scope deployment:
//   az deployment tenant create \
//     --location japaneast \
//     --template-file eo-re-d01-az-child-mgmt-grp.bicep \
//     --parameters EO_AZ_CHILD_MANAGEMENT_GROUP_ID=$Env:EO_AZ_CHILD_MANAGEMENT_GROUP_ID EO_AZ_CHILD_MANAGEMENT_GROUP_DISPLAY_NAME=$Env:EO_AZ_CHILD_MANAGEMENT_GROUP_DISPLAY_NAME EO_AZ_SUBSC_ID='<YOUR_SUBSCRIPTION_ID>'
//
// POST-DEPLOYMENT:
// 1. Deploy eo-re-d01-az-child-mgmt-grp-policies.bicep for policy assignments
// 2. Deploy eo-re-d01-azure-funcapp.bicep to resource group under this subscription
//
// ==============================================================================

targetScope = 'tenant'

// ==============================================================================
// Parameters
// ==============================================================================

// --- Management Group (README: EO_AZ_CHILD_MANAGEMENT_GROUP_ID, EO_AZ_CHILD_MANAGEMENT_GROUP_DISPLAY_NAME) ---
@description('Management Group name. README: EO_AZ_CHILD_MANAGEMENT_GROUP_ID')
param EO_AZ_CHILD_MANAGEMENT_GROUP_ID string = 'eo-re-d01-az-child-mgmt-grp'

@description('子管理グループ（本テンプレートで作成する、名前が EO_AZ_CHILD_MANAGEMENT_GROUP_ID の管理グループ）の表示名。README: EO_AZ_CHILD_MANAGEMENT_GROUP_DISPLAY_NAME')
param EO_AZ_CHILD_MANAGEMENT_GROUP_DISPLAY_NAME string = 'Edge Optimizer RE D01 Management Group'

// --- Subscription Settings (README: EO_AZ_SUBSC_ID) ---
@description('Subscription ID to move under the management group')
param EO_AZ_SUBSC_ID string

// ==============================================================================
// Resources
// ==============================================================================

// ============================================================================
// Management Group
// ============================================================================
resource managementGroup 'Microsoft.Management/managementGroups@2023-04-01' = {
  name: EO_AZ_CHILD_MANAGEMENT_GROUP_ID
  properties: {
    displayName: EO_AZ_CHILD_MANAGEMENT_GROUP_DISPLAY_NAME
  }
}

// ============================================================================
// Subscription Assignment to Management Group
// ============================================================================
resource subscriptionAssignment 'Microsoft.Management/managementGroups/subscriptions@2023-04-01' = {
  parent: managementGroup
  name: EO_AZ_SUBSC_ID
}

// ==============================================================================
// Outputs
// ==============================================================================

@description('Management Group ID')
output managementGroupId string = managementGroup.id

@description('Management Group name')
output managementGroupName string = managementGroup.name

@description('Subscription ID assigned to Management Group')
output assignedSubscriptionId string = EO_AZ_SUBSC_ID
