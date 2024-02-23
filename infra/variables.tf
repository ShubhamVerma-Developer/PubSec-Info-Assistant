variable "environmentName" {
  description = "Name of the the environment which is used to generate a short unique hash used in all resources."
  type        = string
}

variable "location" {
  description = "Primary location for all resources"
  type        = string
}

variable "resourceGroupName" {
  type    = string
  default = ""
}

variable "tenantId" {
  type    = string
  default = ""
}

variable "subscriptionId" {
  type    = string
  default = ""
}

variable "buildNumber" {
  type    = string
  default = "local"
}

variable "isGovCloudDeployment" {
  type    = bool
  default = false
}

variable "cuaEnabled" {
  type    = bool
  default = false
}

variable "cuaId" {
  type    = string
  default = ""
}

variable "requireWebsiteSecurityMembership" {
  type    = bool
  default = false
}
////
// variables that can vary based on the Azure environment being targeted
////
variable "webAppSuffix" {
  type        = string
}

////

////
// Variables that are used for CI/CD automation
////
variable "isInAutomation" {
  type    = bool
  default = false
}

variable "aadWebClientId" {
  type    = string
  default = ""
}

variable "aadMgmtClientId" {
  type    = string
  default = ""
}

variable "aadMgmtClientSecret" {
  type      = string
  default   = ""
  sensitive = true
}

variable "aadMgmtServicePrincipalId" {
  type = string
  default = ""
}
////

////
// Variables that are used for the Azure OpenAI service
////
variable "useExistingAOAIService" {
  type = bool
}

variable "azureOpenAIServiceName" {
  type = string
}

variable "azureOpenAIResourceGroup" {
  type = string
}

variable "azureOpenAIServiceKey" {
  type      = string
  sensitive = true
}

variable "openAIServiceName" {
  type = string
  default = ""
}

variable "openAiSkuName" {
  type    = string
  default = "S0"
}

variable "chatGptDeploymentName" {
  type    = string
  default = "gpt-35-turbo-16k"
}

variable "azureOpenAIEmbeddingDeploymentName" {
  type    = string
  default = "text-embedding-ada-002"
}

variable "azureOpenAIEmbeddingsModelName" {
  type    = string
  default = "text-embedding-ada-002"
}

variable "azureOpenAIEmbeddingsModelVersion" {
  type    = string
  default = "2"
}

variable "useAzureOpenAIEmbeddings" {
  type    = bool
  default = true
}

variable "sentenceTransformersModelName" {
  type    = string
  default = "BAAI/bge-small-en-v1.5"
}

variable "sentenceTransformerEmbeddingVectorSize" {
  type    = string
  default = "384"
}

variable "embeddingsDeploymentCapacity" {
  type    = number
  default = 240
}
////

variable "formRecognizerSkuName" {
  type    = string
  default = "S0"
}

variable "enrichmentSkuName" {
  type    = string
  default = "S0"
}

variable "appServicePlanName" {
  type    = string
  default = ""
}

variable "enrichmentAppServicePlanName" {
  type    = string
  default = ""
}

variable "logAnalyticsName" {
  type    = string
  default = ""
}

variable "applicationInsightsName" {
  type    = string
  default = ""
}

variable "backendServiceName" {
  type    = string
  default = ""
}

variable "enrichmentServiceName" {
  type    = string
  default = ""
}

variable "functionsAppName" {
  type    = string
  default = ""
}

variable "videoIndexerName" {
  type    = string
  default = ""
}

variable "searchServicesName" {
  type    = string
  default = ""
}

variable "searchServicesSkuName" {
  type    = string
  default = "standard"
}

variable "storageAccountName" {
  type    = string
  default = ""
}

variable "contentContainerName" {
  type    = string
  default = "content"
}

variable "uploadContainerName" {
  type    = string
  default = "upload"
}

variable "functionLogsContainerName" {
  type    = string
  default = "logs"
}

variable "searchIndexName" {
  type    = string
  default = "vector-index"
}

variable "chatWarningBannerText" {
  type    = string
  default = ""
}

variable "chatGptModelName" {
  type    = string
  default = "gpt-35-turbo-16k"
}

variable "chatGptModelVersion" {
  type    = string
  default = "0613"
}

variable "chatGptDeploymentCapacity" {
  type    = number
  default = 240
}

variable "chunkTargetSize" {
  type    = string
  default = "750"
}

variable "targetPages" {
  type    = string
  default = "ALL"
}

variable "formRecognizerApiVersion" {
  type    = string
  default = "2023-07-31"
}

variable "queryTermLanguage" {
  type    = string
  default = "English"
}

variable "maxSecondsHideOnUpload" {
  type    = string
  default = "300"
}

variable "maxSubmitRequeueCount" {
  type    = string
  default = "10"
}

variable "pollQueueSubmitBackoff" {
  type    = string
  default = "60"
}

variable "pdfSubmitQueueBackoff" {
  type    = string
  default = "60"
}

variable "maxPollingRequeueCount" {
  type    = string
  default = "10"
}

variable "submitRequeueHideSeconds" {
  type    = string
  default = "1200"
}

variable "pollingBackoff" {
  type    = string
  default = "30"
}

variable "maxReadAttempts" {
  type    = string
  default = "5"
}

variable "maxEnrichmentRequeueCount" {
  type    = string
  default = "10"
}

variable "enrichmentBackoff" {
  type    = string
  default = "60"
}

variable "targetTranslationLanguage" {
  type    = string
  default = "en"
}

variable "pdfSubmitQueue" {
  type    = string
  default = "pdf-submit-queue"
}

variable "pdfPollingQueue" {
  type    = string
  default = "pdf-polling-queue"
}

variable "nonPdfSubmitQueue" {
  type    = string
  default = "non-pdf-submit-queue"
}

variable "mediaSubmitQueue" {
  type    = string
  default = "media-submit-queue"
}

variable "textEnrichmentQueue" {
  type    = string
  default = "text-enrichment-queue"
}

variable "imageEnrichmentQueue" {
  type    = string
  default = "image-enrichment-queue"
}

variable "embeddingsQueue" {
  type    = string
  default = "embeddings-queue"
}

variable "applicationtitle" {
  type    = string
  default = ""
}

variable "enableDevCode" {
  type    = bool
  default = false
}