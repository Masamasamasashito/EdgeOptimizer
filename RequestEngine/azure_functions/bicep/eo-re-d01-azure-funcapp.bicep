// ==============================================================================
// Edge Optimizer - Azure Functions Request Engine Infrastructure
// ==============================================================================
// Creates Function App, Key Vault, Storage Account, and RBAC assignments
//
// PREREQUISITES (Must be completed BEFORE deploying this template):
// 1. Entra ID Application (Service Principal) for GitHub Actions:
//    Create manually via Azure Portal: Microsoft Entra ID > App registrations > New registration
//    Name: eo-ghactions-deploy-entra-app-azfunc-{regionShort}
//    See: AZFUNC_BICEP_README.md for detailed steps
//
// 2. Federated Credentials for OIDC:
//    Configure on the Entra ID Application for GitHub Actions authentication
//
// POST-DEPLOYMENT STEPS:
// 1. Update Key Vault secret value with N8N_EO_REQUEST_SECRET from EO_Infra_Docker/.env
// 2. Set GitHub Secrets (EO_AZ_FUNC_JPEAST_DEPLOY_ENTRA_APP_ID_FOR_GITHUB, EO_AZ_TENANT_ID, etc.)
// 3. Assign 'Web Site Contributor' role to Entra ID Application on Resource Group
// 4. Create IAM user 'Key Vault Secrets Officer' for secret management (if needed)
//
// ==============================================================================

// ==============================================================================
// Parameters
// ==============================================================================

// --- Naming Convention ---
@description('Project prefix for resource naming (e.g., eo)')
@minLength(2)
@maxLength(10)
param projectPrefix string = 'eo'

@description('Component identifier (re = Request Engine)')
@minLength(2)
@maxLength(10)
param component string = 're'

@description('Environment identifier (d01 = dev01, p01 = prod01)')
@minLength(2)
@maxLength(10)
param environment string = 'd01'

@description('Region short name for resource naming')
@allowed([
  'jpeast'    // Japan East
  'jpwest'    // Japan West
  'eastus'    // East US
  'westus'    // West US
  'westeu'    // West Europe
])
param regionShort string = 'jpeast'

// --- Azure Settings ---
@description('Azure region for deployment')
@allowed([
  'japaneast'
  'japanwest'
  'eastus'
  'westus'
  'westeurope'
])
param location string = 'japaneast'

@description('Azure AD Tenant ID')
@secure()
param tenantId string

// --- Function App Settings ---
@description('Python runtime version')
@allowed([
  '3.11'
  '3.12'
  '3.13'
])
param pythonVersion string = '3.13'

@description('Function App instance memory size in MB')
@allowed([
  512
  2048
  4096
])
param instanceMemoryMB int = 512

@description('Maximum instance count for scaling')
@minValue(1)
@maxValue(1000)
param maximumInstanceCount int = 100

// --- Key Vault Settings ---
@description('Key Vault soft delete retention days')
@minValue(7)
@maxValue(90)
param softDeleteRetentionDays int = 7

// ==============================================================================
// Variables
// ==============================================================================

// Resource names following naming convention: {project}-{component}-{env}-{resource}-{region}
var functionAppName = '${projectPrefix}-${component}-${environment}-funcapp-${regionShort}'
var keyVaultName = '${projectPrefix}-${component}-${environment}-kv-${regionShort}'
var storageAccountName = '${projectPrefix}${component}${environment}storage'  // No hyphens, max 24 chars
var appServicePlanName = 'ASP-${projectPrefix}${component}${environment}resourcegroup${regionShort}'

// Secret name (hyphens only, no underscores)
var secretName = 'AZFUNC-REQUEST-SECRET'

// Tags
var commonTags = {
  Project: projectPrefix
  Component: component
  Environment: environment
  ManagedBy: 'Bicep'
}

// ==============================================================================
// Resources
// ==============================================================================

// ============================================================================
// Storage Account (for Function App)
// ============================================================================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: commonTags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'Storage'
  properties: {
    defaultToOAuthAuthentication: true
    publicNetworkAccess: 'Enabled'
    allowCrossTenantReplication: false
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        file: {
          keyType: 'Account'
          enabled: true
        }
        blob: {
          keyType: 'Account'
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// Blob Services
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: false
    }
  }
}

// ============================================================================
// Key Vault
// ============================================================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: commonTags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenantId
    enableRbacAuthorization: true  // Use Azure RBAC instead of access policies
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    enableSoftDelete: true
    softDeleteRetentionInDays: softDeleteRetentionDays
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'None'
      defaultAction: 'Allow'
    }
  }
}

// Key Vault Secret (placeholder value - update after deployment)
resource keyVaultSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: secretName
  properties: {
    value: 'REPLACE_WITH_N8N_EO_REQUEST_SECRET'
    contentType: 'Request Engine token verification secret. Update with N8N_EO_REQUEST_SECRET value.'
    attributes: {
      enabled: true
    }
  }
}

// ============================================================================
// App Service Plan (Flex Consumption)
// ============================================================================
resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  tags: commonTags
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  kind: 'functionapp'
  properties: {
    reserved: true  // Required for Linux
    zoneRedundant: false
  }
}

// ============================================================================
// Function App
// ============================================================================
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  tags: commonTags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'  // Enable Managed Identity for Key Vault access
  }
  properties: {
    enabled: true
    serverFarmId: appServicePlan.id
    reserved: true
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
    clientAffinityEnabled: false
    siteConfig: {
      numberOfWorkers: 1
      alwaysOn: false
      http20Enabled: false
      functionAppScaleLimit: maximumInstanceCount
      minimumElasticInstanceCount: 0
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      ftpsState: 'FtpsOnly'
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
        ]
      }
    }
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobcontainer'
          value: 'https://${storageAccount.name}.blob.${az.environment().suffixes.storage}/app-package-${functionAppName}'
          authentication: {
            type: 'storageaccountconnectionstring'
            storageAccountConnectionStringName: 'DEPLOYMENT_STORAGE_CONNECTION_STRING'
          }
        }
      }
      runtime: {
        name: 'python'
        version: pythonVersion
      }
      scaleAndConcurrency: {
        maximumInstanceCount: maximumInstanceCount
        instanceMemoryMB: instanceMemoryMB
      }
    }
  }
}

// Function App - Disable FTP publishing
resource functionAppFtpPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-12-01' = {
  parent: functionApp
  name: 'ftp'
  properties: {
    allow: false
  }
}

// Function App - Disable SCM publishing (basic auth)
resource functionAppScmPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-12-01' = {
  parent: functionApp
  name: 'scm'
  properties: {
    allow: false
  }
}

// Function App - App Settings
// Note: For Flex Consumption plan, runtime settings are configured in functionAppConfig, not in app settings
resource functionAppSettings 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: functionApp
  name: 'appsettings'
  properties: {
    // Key Vault URL for Request Secret retrieval
    EO_AZ_RE_KEYVAULT_URL: keyVault.properties.vaultUri
    // Storage connection string
    AzureWebJobsStorage: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${az.environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
    DEPLOYMENT_STORAGE_CONNECTION_STRING: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${az.environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
  }
}

// ============================================================================
// RBAC - Key Vault Secrets User for Function App Managed Identity
// ============================================================================
// Role Definition ID for 'Key Vault Secrets User': 4633458b-17de-408a-b874-0445c86b69e6
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Allow Function App to read secrets from Key Vault for token verification'
  }
}

// ============================================================================
// Storage Containers (for Function App deployment)
// ============================================================================
resource deploymentContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storageAccount.name}/default/app-package-${functionAppName}'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    blobService
  ]
}

resource webJobsHostsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storageAccount.name}/default/azure-webjobs-hosts'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    blobService
  ]
}

resource webJobsSecretsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storageAccount.name}/default/azure-webjobs-secrets'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    blobService
  ]
}

// ==============================================================================
// Outputs
// ==============================================================================

@description('Function App name')
output functionAppName string = functionApp.name

@description('Function App default hostname')
output functionAppHostname string = functionApp.properties.defaultHostName

@description('Function App resource ID')
output functionAppResourceId string = functionApp.id

@description('Function App Managed Identity Principal ID (for RBAC assignments)')
output functionAppPrincipalId string = functionApp.identity.principalId

@description('Key Vault name')
output keyVaultName string = keyVault.name

@description('Key Vault URI (set this in GitHub Secrets as EO_AZ_RE_KEYVAULT_URL)')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Storage Account name')
output storageAccountName string = storageAccount.name

@description('App Service Plan name')
output appServicePlanName string = appServicePlan.name
