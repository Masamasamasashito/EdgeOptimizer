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
//     --parameters subscriptionId='<YOUR_SUBSCRIPTION_ID>'
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

// --- Subscription Settings ---
@description('Subscription ID to move under the management group')
param subscriptionId string

// ==============================================================================
// Variables
// ==============================================================================

// Management Group naming (fixed)
var managementGroupName = 'eo-re-d01-az-child-mgmt-grp'
var managementGroupDisplayName = 'Edge Optimizer RE D01 Management Group'

// ==============================================================================
// Resources
// ==============================================================================

// ============================================================================
// Management Group
// ============================================================================
resource managementGroup 'Microsoft.Management/managementGroups@2023-04-01' = {
  name: managementGroupName
  properties: {
    displayName: managementGroupDisplayName
  }
}

// ============================================================================
// Subscription Assignment to Management Group
// ============================================================================
resource subscriptionAssignment 'Microsoft.Management/managementGroups/subscriptions@2023-04-01' = {
  parent: managementGroup
  name: subscriptionId
}

// ==============================================================================
// Outputs
// ==============================================================================

@description('Management Group ID')
output managementGroupId string = managementGroup.id

@description('Management Group name')
output managementGroupName string = managementGroup.name

@description('Subscription ID assigned to Management Group')
output assignedSubscriptionId string = subscriptionId
