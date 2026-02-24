// Request Engine Instance config: ../instances_conf/funcapp001.env
// ==============================================================================
// Edge Optimizer - Azure Functions Request Engine Infrastructure
// ==============================================================================
// Creates Function App, Key Vault, Storage Account, and RBAC assignments
//
// PREREQUISITES (Must be completed BEFORE deploying this template):
// 1. Entra ID Application (Service Principal) for GitHub Actions:
//    Create manually via Azure Portal: Microsoft Entra ID > App registrations > New registration
//    Name: eo-ghactions-deploy-entra-app-azfunc-{regionShort}
//    See: EO_Documents/Manuals/py/AZFUNC_BICEP_README.md for detailed steps
//
// 2. Federated Credentials for OIDC:
//    Configure on the Entra ID Application for GitHub Actions authentication
//
// POST-DEPLOYMENT STEPS:
// 1. Update Key Vault secret value with N8N_EO_REQUEST_SECRET from EO_Infra_Docker/.env
// 2. Set GitHub Secrets (EO_AZ_FUNC_JPE_DEPLOY_ENTRA_APP_ID_FOR_GITHUB, EO_AZ_TENANT_ID, etc.)
// 3. Assign 'Web Site Contributor' role to Entra ID Application on Resource Group
// 4. Create IAM user 'Key Vault Secrets Officer' for secret management (if needed)
//
// ==============================================================================

// ==============================================================================
// Parameters
// ==============================================================================

// --- Naming Convention (EO_Documents/Manuals/py/AZFUNC_BICEP_README.md の環境変数名と統一) ---
@description('Project prefix (e.g., eo). README: EO_PROJECT')
@minLength(2)
@maxLength(10)
param EO_PROJECT string = 'eo'

@description('Component identifier (re = Request Engine). README: EO_COMPONENT')
@minLength(2)
@maxLength(10)
param EO_COMPONENT string = 're'

@description('Environment identifier (d01 = dev01). README: EO_ENV')
@minLength(2)
@maxLength(10)
param EO_ENV string = 'd01'

@description('Region short name. README: EO_REGION_SHORT')
@allowed([
  'jpe'       // Japan East
  'jpw'       // Japan West
  'eus'       // East US
  'wus'       // West US
  'weu'       // West Europe
])
param EO_REGION_SHORT string = 'jpe'

@description('Instance identifier (e.g., 001). README: EO_RE_INSTANCE_ID')
@minLength(1)
@maxLength(8)
param EO_RE_INSTANCE_ID string = '001'

@description('Global project-environment ID for Key Vault/Storage. Max 4 chars recommended. README: EO_GLOBAL_PRJ_ENV_ID')
@minLength(1)
@maxLength(6)
param EO_GLOBAL_PRJ_ENV_ID string = 'a1b2'

@description('Secret service identifier for Key Vault naming (e.g., kv). README: EO_SECRET_SERVICE')
@minLength(2)
@maxLength(4)
param EO_SECRET_SERVICE string = 'kv'

@description('Storage service identifier (e.g., st). README: EO_STORAGE_SERVICE')
@minLength(2)
@maxLength(4)
param EO_STORAGE_SERVICE string = 'st'

// --- Azure Settings ---
@description('Azure region for deployment. README: EO_REGION')
@allowed([
  'japaneast'
  'japanwest'
  'eastus'
  'westus'
  'westeurope'
])
param EO_REGION string = 'japaneast'

@description('Azure AD Tenant ID. README: EO_AZ_ENTRA_TENANT_ID')
@secure()
param EO_AZ_ENTRA_TENANT_ID string

// --- Function App Settings ---
@description('Azure Function App の Python ランタイム版。README: EO_AZ_RE_FUNCAPP_PYTHON_VERSION')
@allowed([
  '3.11'
  '3.12'
  '3.13'
])
param EO_AZ_RE_FUNCAPP_PYTHON_VERSION string = '3.13'

@description('Azure Function App のインスタンスメモリ (MB)。README: EO_AZ_RE_FUNCAPP_INSTANCE_MEMORY_MB')
@allowed([
  512
  2048
  4096
])
param EO_AZ_RE_FUNCAPP_INSTANCE_MEMORY_MB int = 512

@description('Azure Function App の最大インスタンス数。README: EO_AZ_RE_FUNCAPP_MAXIMUM_INSTANCE_COUNT')
@minValue(1)
@maxValue(1000)
param EO_AZ_RE_FUNCAPP_MAXIMUM_INSTANCE_COUNT int = 1

// --- Key Vault Settings ---
@description('Key Vault soft delete retention days. README: EO_SOFT_DELETE_RETENTION_DAYS')
@minValue(7)
@maxValue(90)
param EO_SOFT_DELETE_RETENTION_DAYS int = 7

// ==============================================================================
// Variables
// ==============================================================================

// Resource names per EO_Documents/Manuals/py/AZFUNC_BICEP_README.md (Key Vault & Storage: 24-char limit, 22-char target for buffer)
var FUNCTION_APP_NAME = '${EO_PROJECT}-${EO_COMPONENT}-${EO_ENV}-funcapp-${EO_REGION_SHORT}-${EO_RE_INSTANCE_ID}'
var KEY_VAULT_NAME = '${EO_PROJECT}-${EO_SECRET_SERVICE}-${EO_ENV}-${EO_REGION_SHORT}-${EO_RE_INSTANCE_ID}-${EO_GLOBAL_PRJ_ENV_ID}'  // e.g. eo-kv-d01-jpe-001-a1b2 (22 chars)
var STORAGE_ACCOUNT_NAME = '${EO_PROJECT}${EO_COMPONENT}${EO_STORAGE_SERVICE}${EO_ENV}${EO_REGION_SHORT}${EO_RE_INSTANCE_ID}${EO_GLOBAL_PRJ_ENV_ID}'  // No hyphens, max 24 chars; e.g. eorestd01jpe001a1b2 (19 chars)
var APP_SERVICE_PLAN_NAME = 'ASP-${EO_PROJECT}${EO_COMPONENT}${EO_ENV}resourcegrp${EO_REGION_SHORT}'

// Secret name (hyphens only, no underscores)
var SECRET_NAME = 'AZFUNC-REQUEST-SECRET'

// Tags
var COMMON_TAGS = {
  Project: EO_PROJECT
  Component: EO_COMPONENT
  Environment: EO_ENV
  ManagedBy: 'Bicep'
}

// ==============================================================================
// Resources
// ==============================================================================

// ============================================================================
// Storage Account (for Function App)
// ============================================================================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: STORAGE_ACCOUNT_NAME
  location: EO_REGION
  tags: COMMON_TAGS
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
  name: KEY_VAULT_NAME
  location: EO_REGION
  tags: COMMON_TAGS
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: EO_AZ_ENTRA_TENANT_ID
    enableRbacAuthorization: true  // Use Azure RBAC instead of access policies
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    enableSoftDelete: true
    softDeleteRetentionInDays: EO_SOFT_DELETE_RETENTION_DAYS
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
  name: SECRET_NAME
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
  name: APP_SERVICE_PLAN_NAME
  location: EO_REGION
  tags: COMMON_TAGS
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
  name: FUNCTION_APP_NAME
  location: EO_REGION
  tags: COMMON_TAGS
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
      functionAppScaleLimit: EO_AZ_RE_FUNCAPP_MAXIMUM_INSTANCE_COUNT
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
          value: 'https://${storageAccount.name}.blob.${az.environment().suffixes.storage}/app-package-${FUNCTION_APP_NAME}'
          authentication: {
            type: 'storageaccountconnectionstring'
            storageAccountConnectionStringName: 'DEPLOYMENT_STORAGE_CONNECTION_STRING'
          }
        }
      }
      runtime: {
        name: 'python'
        version: EO_AZ_RE_FUNCAPP_PYTHON_VERSION
      }
      scaleAndConcurrency: {
        maximumInstanceCount: EO_AZ_RE_FUNCAPP_MAXIMUM_INSTANCE_COUNT
        instanceMemoryMB: EO_AZ_RE_FUNCAPP_INSTANCE_MEMORY_MB
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
  name: '${storageAccount.name}/default/app-package-${FUNCTION_APP_NAME}'
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
