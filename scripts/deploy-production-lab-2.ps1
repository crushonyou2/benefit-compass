[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('Ml', 'Api')]
    [string]$Stage,

    [Parameter(Mandatory)]
    [ValidatePattern('@sha256:[A-Fa-f0-9]{64}$')]
    [string]$Image,

    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9-]+$')]
    [string]$RevisionSuffix,

    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9-]+$')]
    [string]$Tag,

    [ValidatePattern('^https://')]
    [string]$MlBaseUrl,

    [ValidateSet('0', '1')]
    [string]$ModelLocalOnly = '1',

    [ValidateRange(1, 120)]
    [int]$StartupFailureThreshold = 120,

    [ValidateRange(1, 65535)]
    [int]$ContainerPort = 8080,

    [string]$Project = 'healthy-clock-465504-t5',
    [string]$Region = 'asia-northeast3',
    [switch]$Execute
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($Stage -eq 'Api' -and [string]::IsNullOrWhiteSpace($MlBaseUrl)) {
    throw '-MlBaseUrl is required for the Api stage.'
}

$service = if ($Stage -eq 'Ml') { 'benefit-ml' } else { 'benefit-api' }
$deployArgs = @(
    'run', 'deploy', $service,
    "--project=$Project",
    "--region=$Region",
    "--image=$Image",
    "--revision-suffix=$RevisionSuffix",
    "--tag=$Tag",
    '--no-traffic',
    '--min=0',
    '--cpu-boost',
    "--port=$ContainerPort",
    '--quiet'
)

if ($Stage -eq 'Ml') {
    $deployArgs += @('--cpu=2', '--memory=2Gi', '--concurrency=160', '--timeout=300', '--max=10')
    $deployArgs += "--update-env-vars=MODEL_LOCAL_ONLY=$ModelLocalOnly"
    # The probe budget gates container admission. MODEL_READY_TIMEOUT_SECONDS separately
    # protects direct/local requests that race readiness without Cloud Run gating.
    # Passing /ready gates traffic on model readiness while /health remains liveness-only.
    $deployArgs += "--startup-probe=httpGet.path=/ready,httpGet.port=$ContainerPort,initialDelaySeconds=0,failureThreshold=$StartupFailureThreshold,timeoutSeconds=1,periodSeconds=2"
} else {
    $deployArgs += @('--cpu=1', '--memory=1Gi', '--concurrency=80', '--timeout=300', '--max=20')
    $deployArgs += "--update-env-vars=ML_BASE_URL=$MlBaseUrl"
}

if (-not $Execute) {
    Write-Output 'DRY RUN: no Cloud Run state was changed.'
    Write-Output ('gcloud ' + ($deployArgs -join ' '))
    exit 0
}

& gcloud @deployArgs
if ($LASTEXITCODE -ne 0) {
    throw "gcloud run deploy failed for $service with exit code $LASTEXITCODE"
}

Write-Output "Deployment submitted for $service with --no-traffic and min instances 0."
