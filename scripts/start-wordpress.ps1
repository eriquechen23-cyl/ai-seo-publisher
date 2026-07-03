param(
    [int]$Port = 8080,
    [string]$AdminUser = "demo_admin",
    [string]$AdminPassword = "demo_password_12345",
    [string]$AdminEmail = "demo@example.com"
)

$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DockerConfig = Join-Path $ProjectRoot ".docker"
$BackendEnv = Join-Path $ProjectRoot "backend\.env"
$MuPluginSource = Join-Path $ProjectRoot "wordpress\mu-plugins\allow-application-passwords.php"
$ThemeSource = Join-Path $ProjectRoot "wordpress\themes\ai-seo-demo"
$ThemeSlug = "ai-seo-demo"

New-Item -ItemType Directory -Force $DockerConfig | Out-Null

$Docker = @("--config", $DockerConfig)
$Network = "ai-seo-wordpress-net"
$DbContainer = "ai-seo-wordpress-db"
$WpContainer = "ai-seo-wordpress"
$DbVolume = "ai_seo_wordpress_db"
$WpVolume = "ai_seo_wordpress_data"
$DbName = "wordpress"
$DbUser = "wordpress"
$DbPassword = "wordpress"
$DbRootPassword = "wordpress_root"
$SiteUrl = "http://localhost:$Port"

$ExistingEnv = @{}
if (Test-Path $BackendEnv) {
    foreach ($line in Get-Content -Encoding UTF8 $BackendEnv) {
        if ($line -match '^([^#=]+)=(.*)$') {
            $ExistingEnv[$matches[1].Trim()] = $matches[2].Trim().Trim('"')
        }
    }
}
$ExistingLlmMode = if ($ExistingEnv["LLM_MODE"]) { $ExistingEnv["LLM_MODE"] } else { "openai_compatible" }
$ExistingLlmApiBase = if ($ExistingEnv["LLM_API_BASE"]) { $ExistingEnv["LLM_API_BASE"] } else { "https://generativelanguage.googleapis.com/v1beta/openai/" }
$ExistingLlmApiKey = if ($ExistingEnv["LLM_API_KEY"]) { $ExistingEnv["LLM_API_KEY"] } else { "" }
$ExistingLlmModel = if ($ExistingEnv["LLM_MODEL"]) { $ExistingEnv["LLM_MODEL"] } else { "gemini-3.5-flash" }
$ExistingLlmTimeout = if ($ExistingEnv["LLM_TIMEOUT_SECONDS"]) { $ExistingEnv["LLM_TIMEOUT_SECONDS"] } else { "30" }

function Invoke-Docker {
    param([string[]]$CommandArgs)
    & docker @Docker @CommandArgs
}

function Test-ContainerExists {
    param([string]$Name)
    $existing = Invoke-Docker @("ps", "-a", "--filter", "name=^/$Name$", "--format", "{{.Names}}")
    return $existing -eq $Name
}

function Test-ContainerRunning {
    param([string]$Name)
    $running = Invoke-Docker @("ps", "--filter", "name=^/$Name$", "--filter", "status=running", "--format", "{{.Names}}")
    return $running -eq $Name
}

Write-Host "Preparing Docker network and volumes..."
$networkExists = Invoke-Docker @("network", "ls", "--filter", "name=^$Network$", "--format", "{{.Name}}")
if ($networkExists -ne $Network) {
    Invoke-Docker @("network", "create", $Network) | Out-Null
}
Invoke-Docker @("volume", "create", $DbVolume) | Out-Null
Invoke-Docker @("volume", "create", $WpVolume) | Out-Null

if (-not (Test-ContainerExists $DbContainer)) {
    Write-Host "Starting MariaDB container..."
    Invoke-Docker @(
        "run", "-d",
        "--name", $DbContainer,
        "--network", $Network,
        "-e", "MARIADB_DATABASE=$DbName",
        "-e", "MARIADB_USER=$DbUser",
        "-e", "MARIADB_PASSWORD=$DbPassword",
        "-e", "MARIADB_ROOT_PASSWORD=$DbRootPassword",
        "-v", "${DbVolume}:/var/lib/mysql",
        "mariadb:11"
    ) | Out-Null
} elseif (-not (Test-ContainerRunning $DbContainer)) {
    Write-Host "Starting existing MariaDB container..."
    Invoke-Docker @("start", $DbContainer) | Out-Null
}

if (-not (Test-ContainerExists $WpContainer)) {
    Write-Host "Starting WordPress container..."
    Invoke-Docker @(
        "run", "-d",
        "--name", $WpContainer,
        "--network", $Network,
        "-p", "${Port}:80",
        "-e", "WORDPRESS_DB_HOST=${DbContainer}:3306",
        "-e", "WORDPRESS_DB_USER=$DbUser",
        "-e", "WORDPRESS_DB_PASSWORD=$DbPassword",
        "-e", "WORDPRESS_DB_NAME=$DbName",
        "-v", "${WpVolume}:/var/www/html",
        "wordpress:php8.3-apache"
    ) | Out-Null
} elseif (-not (Test-ContainerRunning $WpContainer)) {
    Write-Host "Starting existing WordPress container..."
    Invoke-Docker @("start", $WpContainer) | Out-Null
}

Write-Host "Waiting for WordPress HTTP endpoint..."
$ready = $false
for ($i = 1; $i -le 60; $i++) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $SiteUrl -TimeoutSec 3
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    throw "WordPress did not become ready at $SiteUrl"
}

Write-Host "Installing local Application Passwords MU plugin..."
Invoke-Docker @("exec", $WpContainer, "mkdir", "-p", "/var/www/html/wp-content/mu-plugins") | Out-Null
Invoke-Docker @("cp", $MuPluginSource, "${WpContainer}:/var/www/html/wp-content/mu-plugins/allow-application-passwords.php") | Out-Null
Invoke-Docker @("exec", $WpContainer, "chown", "-R", "www-data:www-data", "/var/www/html/wp-content") | Out-Null

Write-Host "Installing local WordPress preview theme..."
Invoke-Docker @("exec", $WpContainer, "mkdir", "-p", "/var/www/html/wp-content/themes/$ThemeSlug") | Out-Null
Invoke-Docker @("cp", "${ThemeSource}\.", "${WpContainer}:/var/www/html/wp-content/themes/$ThemeSlug") | Out-Null
Invoke-Docker @("exec", $WpContainer, "chown", "-R", "www-data:www-data", "/var/www/html/wp-content/themes/$ThemeSlug") | Out-Null

Write-Host "Installing WordPress core if needed..."
$coreInstalled = Invoke-Docker @(
    "run", "--rm",
    "--network", $Network,
    "--volumes-from", $WpContainer,
    "-e", "WORDPRESS_DB_HOST=${DbContainer}:3306",
    "-e", "WORDPRESS_DB_USER=$DbUser",
    "-e", "WORDPRESS_DB_PASSWORD=$DbPassword",
    "-e", "WORDPRESS_DB_NAME=$DbName",
    "wordpress:cli",
    "wp", "core", "is-installed",
    "--path=/var/www/html",
    "--url=$SiteUrl"
) 2>$null

if ($LASTEXITCODE -ne 0) {
    Invoke-Docker @(
        "run", "--rm",
        "--network", $Network,
        "--volumes-from", $WpContainer,
        "-e", "WORDPRESS_DB_HOST=${DbContainer}:3306",
        "-e", "WORDPRESS_DB_USER=$DbUser",
        "-e", "WORDPRESS_DB_PASSWORD=$DbPassword",
        "-e", "WORDPRESS_DB_NAME=$DbName",
        "wordpress:cli",
        "wp", "core", "install",
        "--path=/var/www/html",
        "--url=$SiteUrl",
        "--title=AI SEO Publisher Demo",
        "--admin_user=$AdminUser",
        "--admin_password=$AdminPassword",
        "--admin_email=$AdminEmail",
        "--skip-email"
    ) | Out-Null
}

Write-Host "Activating local WordPress preview theme..."
Invoke-Docker @(
    "run", "--rm",
    "--network", $Network,
    "--volumes-from", $WpContainer,
    "-e", "WORDPRESS_DB_HOST=${DbContainer}:3306",
    "-e", "WORDPRESS_DB_USER=$DbUser",
    "-e", "WORDPRESS_DB_PASSWORD=$DbPassword",
    "-e", "WORDPRESS_DB_NAME=$DbName",
    "wordpress:cli",
    "wp", "theme", "activate", $ThemeSlug,
    "--path=/var/www/html",
    "--url=$SiteUrl"
) | Out-Null

Write-Host "Creating WordPress application password..."
$appPassword = Invoke-Docker @(
    "run", "--rm",
    "--network", $Network,
    "--volumes-from", $WpContainer,
    "-e", "WORDPRESS_DB_HOST=${DbContainer}:3306",
    "-e", "WORDPRESS_DB_USER=$DbUser",
    "-e", "WORDPRESS_DB_PASSWORD=$DbPassword",
    "-e", "WORDPRESS_DB_NAME=$DbName",
    "wordpress:cli",
    "wp", "user", "application-password", "create", $AdminUser, "ai-seo-publisher",
    "--path=/var/www/html",
    "--url=$SiteUrl",
    "--porcelain"
)

if (-not $appPassword) {
    throw "Failed to create WordPress application password"
}

$EnvContent = @"
APP_NAME=AI SEO Publisher API
API_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:///backend/demo.db

LLM_MODE=$ExistingLlmMode
LLM_API_BASE=$ExistingLlmApiBase
LLM_API_KEY=$ExistingLlmApiKey
LLM_MODEL=$ExistingLlmModel
LLM_TIMEOUT_SECONDS=$ExistingLlmTimeout

WORDPRESS_URL=$SiteUrl
WORDPRESS_USERNAME=$AdminUser
WORDPRESS_APP_PASSWORD="$appPassword"
"@

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($BackendEnv, $EnvContent, $Utf8NoBom)

Write-Host ""
Write-Host "WordPress is ready:"
Write-Host "  Site:  $SiteUrl"
Write-Host "  Admin: $SiteUrl/wp-admin"
Write-Host "  User:  $AdminUser"
Write-Host "  Pass:  $AdminPassword"
Write-Host ""
Write-Host "backend/.env has been updated with the generated Application Password."
