[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://')]
    [string]$ApiBaseUrl,

    [ValidateSet('recommend', 'ask')]
    [string]$Mode = 'recommend',

    [Parameter(Mandatory = $true)]
    [string]$Scenario,

    [Parameter(Mandatory = $true)]
    [string]$Revision,

    [ValidateRange(2, 100)]
    [int]$Runs = 6,

    [Parameter(Mandatory = $true)]
    [string]$OutputCsv,

    [switch]$FirstRequestCold
)

$ErrorActionPreference = 'Stop'

function Get-ResponseHeader {
    param(
        [System.Net.Http.HttpResponseMessage]$Response,
        [string]$Name
    )
    $values = $null
    if ($Response.Headers.TryGetValues($Name, [ref]$values)) {
        return ($values -join ',')
    }
    if ($Response.Content.Headers.TryGetValues($Name, [ref]$values)) {
        return ($values -join ',')
    }
    return $null
}

function Convert-ServerTiming {
    param([string]$HeaderValue)
    $allowed = @(
        'api_to_ml', 'api_ml_transport', 'ml_model_wait', 'ml_embedding', 'ml_db_connect',
        'ml_db_query', 'ml_rerank', 'ml_total', 'gemini'
    )
    $result = @{}
    foreach ($name in $allowed) {
        $result[$name] = $null
    }
    if ([string]::IsNullOrWhiteSpace($HeaderValue)) {
        return $result
    }
    foreach ($entry in $HeaderValue.Split(',')) {
        if ($entry.Trim() -match '^([a-z_]+);dur=([0-9]+(?:\.[0-9]+)?)$') {
            $name = $Matches[1]
            if ($allowed -contains $name) {
                $result[$name] = [double]::Parse(
                    $Matches[2], [System.Globalization.CultureInfo]::InvariantCulture)
            }
        }
    }
    return $result
}

$endpoint = if ($Mode -eq 'ask') { '/api/ask' } else { '/api/policies/recommend' }
$url = $ApiBaseUrl.TrimEnd('/') + $endpoint

# Fixed synthetic input used by the historical baseline. It is never written to CSV.
$payload = @{
    query = '월세 지원'
    age = $null
    region = $null
    k = 5
} | ConvertTo-Json -Compress

$handler = [System.Net.Http.HttpClientHandler]::new()
$client = [System.Net.Http.HttpClient]::new($handler)
$client.Timeout = [TimeSpan]::FromSeconds(180)
$rows = [System.Collections.Generic.List[object]]::new()

try {
    for ($run = 1; $run -le $Runs; $run++) {
        $content = [System.Net.Http.StringContent]::new(
            $payload, [Text.Encoding]::UTF8, 'application/json')
        $startedAt = [System.Diagnostics.Stopwatch]::StartNew()
        $response = $null
        $status = 0
        $resultCount = $null
        $errorType = $null
        $timing = @{}
        $requestId = $null
        $modelLoadMs = $null
        try {
            $response = $client.PostAsync($url, $content).GetAwaiter().GetResult()
            $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
            $status = [int]$response.StatusCode
            $timing = Convert-ServerTiming (Get-ResponseHeader $response 'Server-Timing')
            $requestId = Get-ResponseHeader $response 'X-Request-ID'
            $modelLoad = Get-ResponseHeader $response 'X-ML-Model-Load-Ms'
            if ($modelLoad -match '^[0-9]+(?:\.[0-9]+)?$') {
                $modelLoadMs = [double]::Parse(
                    $modelLoad, [System.Globalization.CultureInfo]::InvariantCulture)
            }
            if ($response.IsSuccessStatusCode) {
                $json = $body | ConvertFrom-Json
                $resultCount = if ($Mode -eq 'ask') { @($json.sources).Count } else { @($json).Count }
            }
        }
        catch {
            # Record only the exception type; messages can contain URLs or environment details.
            $errorType = $_.Exception.GetType().Name
        }
        finally {
            $startedAt.Stop()
            $content.Dispose()
            if ($null -ne $response) { $response.Dispose() }
        }

        $temperature = if ($FirstRequestCold -and $run -eq 1) { 'cold' } else { 'warm' }
        $rows.Add([pscustomobject]@{
            scenario = $Scenario
            revision = $Revision
            run = $run
            temperature = $temperature
            timestamp_utc = [DateTimeOffset]::UtcNow.ToString('o')
            endpoint = $endpoint
            duration_ms = [math]::Round($startedAt.Elapsed.TotalMilliseconds, 3)
            status = $status
            result_count = $resultCount
            request_id = $requestId
            api_to_ml_ms = $timing['api_to_ml']
            api_ml_transport_ms = $timing['api_ml_transport']
            ml_model_wait_ms = $timing['ml_model_wait']
            ml_embedding_ms = $timing['ml_embedding']
            ml_db_connect_ms = $timing['ml_db_connect']
            ml_db_query_ms = $timing['ml_db_query']
            ml_rerank_ms = $timing['ml_rerank']
            ml_total_ms = $timing['ml_total']
            gemini_ms = $timing['gemini']
            ml_model_load_ms = $modelLoadMs
            error_type = $errorType
        })
    }
}
finally {
    $client.Dispose()
    $handler.Dispose()
}

$resolvedOutput = [IO.Path]::GetFullPath($OutputCsv)
$parent = Split-Path -Parent $resolvedOutput
if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent | Out-Null
}
$rows | Export-Csv -LiteralPath $resolvedOutput -NoTypeInformation -Encoding utf8
$rows | Format-Table run, temperature, duration_ms, status, result_count,
    api_to_ml_ms, api_ml_transport_ms, ml_model_wait_ms, ml_embedding_ms, ml_db_connect_ms, ml_db_query_ms,
    ml_total_ms, gemini_ms
Write-Output "Raw CSV: $resolvedOutput"
