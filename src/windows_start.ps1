# ============================ Configuration ============================
# Sry but this file is under heavy development, its an importend thing
# You need often to edit defaultPythonPath, srcDir, extensionsPath
# Version 1.04
#
#
param(
    [switch]$UpdateIni = $true,   # if set, update values in AutoPyPlusPlus\extensions_path.ini
    [switch]$IniDryRun = $false   # if set, only show what would change (no write)
)


$UI = @{
  HeaderBg = 'DarkBlue'; HeaderFg = 'White'
  Border   = 'Cyan'
  Text     = 'Gray'
  Muted    = 'DarkGray'
  Ok       = 'Green'
  Warn     = 'Yellow'
  Err      = 'Red'
  Info     = 'DarkCyan'
}

function Out-Rule([string]$ch='-', [int]$width=0){
    if($width -le 0){
        try { $width = [Math]::Max(40, [Console]::WindowWidth - 2) } catch { $width = 78 }
    }
    Write-Host ($ch * $width) -ForegroundColor $UI.Border
}
function Out-Title([string]$text){
    Out-Rule '='
    Write-Host (" " + $text) -ForegroundColor $UI.HeaderFg -BackgroundColor $UI.HeaderBg
    Out-Rule '='
}

function Out-Panel([string]$Title, [string[]]$Lines=@(), [int]$Width=0){
    if($Width -le 0){
        try { $Width = [Math]::Max(40, [Console]::WindowWidth - 2) } catch { $Width = 78 }
    }
    $inner = $Width - 4
    $top = "+{0}+" -f ('-' * ($Width-2))
    $sep = $top
    $bot = $top
    Write-Host $top -ForegroundColor $UI.Border
    if($Title){
        $t = if($Title.Length -gt $inner){ $Title.Substring(0,$inner) } else { $Title }
        $pad = ' ' * ($inner - $t.Length)
        Write-Host ("| " + $t + $pad + " |")
        Write-Host $sep -ForegroundColor $UI.Border
    }
    foreach($ln in $Lines){
        $line = "$ln"
        while($line.Length -gt $inner){
            $chunk = $line.Substring(0,$inner)
            Write-Host ("| " + $chunk + " |")
            $line = $line.Substring($inner)
        }
        $pad = ' ' * ($inner - $line.Length)
        Write-Host ("| " + $line + $pad + " |")
    }
    Write-Host $bot -ForegroundColor $UI.Border
}

# Streaming-Panel (optional)
$script:__panel = @{ open=$false; width=0; inner=0 }
function Panel-Begin([string]$Title, [int]$Width=0){
    if($Width -le 0){
        try { $Width = [Math]::Max(40, [Console]::WindowWidth - 2) } catch { $Width = 78 }
    }
    $script:__panel.open=$true; $script:__panel.width=$Width; $script:__panel.inner=$Width-4
    $top = "+{0}+" -f ('-' * ($Width-2))
    Write-Host $top -ForegroundColor $UI.Border
    if($Title){
        $t = if($Title.Length -gt $script:__panel.inner){ $Title.Substring(0,$script:__panel.inner) } else { $Title }
        $pad = ' ' * ($script:__panel.inner - $t.Length)
        Write-Host ("| " + $t + $pad + " |")
        Write-Host $top -ForegroundColor $UI.Border
    }
}
function Panel-Line([string]$Text){
    if(-not $script:__panel.open){ return }
    $inner = $script:__panel.inner
    $line = "$Text"
    while($line.Length -gt $inner){
        $chunk = $line.Substring(0,$inner)
        Write-Host ("| " + $chunk + " |")
        $line = $line.Substring($inner)
    }
    $pad = ' ' * ($inner - $line.Length)
    Write-Host ("| " + $line + $pad + " |")
}
function Panel-End(){
    if(-not $script:__panel.open){ return }
    $bot = "+{0}+" -f ('-' * ($script:__panel.width-2))
    Write-Host $bot -ForegroundColor $UI.Border
    $script:__panel.open=$false
}

# ===== Re-mapped Say-* & Helpers (ASCII, farbig, konsistent) =====
function Say-Section([string]$Text){ Out-Title $Text }
function Say-Step   ([string]$Text){ Write-Host ("[STEP] " + $Text) -ForegroundColor $UI.Border }
function Say-Info   ([string]$Text){ Write-Host ("[INFO] " + $Text) -ForegroundColor $UI.Info }
function Say-Ok     ([string]$Text){ Write-Host ("[OK]   " + $Text) -ForegroundColor $UI.Ok }
function Say-Warn   ([string]$Text){ Write-Host ("[WARN] " + $Text) -ForegroundColor $UI.Warn }
function Say-Err    ([string]$Text){ Write-Host ("[ERR]  " + $Text) -ForegroundColor $UI.Err }

function Show-Check {
    param([Parameter(Mandatory)][string]$Label,[Parameter(Mandatory)][bool]$Ok,[string]$Detail="")
    if ($Ok) { Write-Host ("[OK]   {0}" -f $Label) -ForegroundColor $UI.Ok }
    else     { Write-Host ("[ERR]  {0}" -f $Label) -ForegroundColor $UI.Err }
    if ($Detail) { Write-Host ("       - {0}" -f $Detail) -ForegroundColor $UI.Muted }
}
function Show-Item {
    param([Parameter(Mandatory)][string]$Name,[string]$Value,[ConsoleColor]$Color=[ConsoleColor]::Gray)
    Write-Host (" - {0}: " -f $Name) -NoNewline -ForegroundColor $Color
    Write-Host $Value -ForegroundColor $UI.Muted
}

#########################################################################################################################
#   EDIT THIS !!!!
$defaultPythonPath     = 'C:\Users\melatroid\AppData\Local\Programs\Python\Python310\python.exe'
$srcDir                = 'C:\Users\melatroid\Desktop\autoPy++\AutoPyPlusPlus\src'
$extensionsPath        = 'C:\Users\melatroid\Desktop\autoPy++\AutoPyPlusPlus\src\AutoPyPlusPlus\extensions_path.ini'
#########################################################################################################################
#   EDIT THIS NOT!!!!
$ProtectedKeys = @('tcl_base','msvc','cpp')
$desiredPythonVersion  = '3.10.11'
$expectedMinor         = '3.10'
$venvRoot              = "$env:LOCALAPPDATA\AutoPyPP\envs"
$venvName              = "autopypp-Env-$($desiredPythonVersion -replace '\.','_')"
$allowInstallPython    = $true
$autoInstallMissing    = $true
$enforceToolPresence   = $false
$enforceMinor          = $false

$art = @'

                  _         _        ____                    
                 / \  _   _| |_ ___ |  _ \ _   _   _     _   
                / _ \| | | | __/ _ \| |_) | | | |_| |_ _| |_ 
               / ___ \ |_| | || (_) |  __/| |_| |_   _|_   _|
              /_/   \_\__,_|\__\___/|_|    \__, | |_|   |_|                         
            /^\/^\                         |___/     /^\/^\
         __|__|o |                                 _|_o|  o|
\/     /~     \_/ \                              /~     \_/ \
 \____|__________/  \                           |__________/ \
        \_______      \                         \_______      \
                `\     \                  \              \     \                    \
                  |     |                   \            |     |                      \
                 /      /                    \\          /     /                       \\
                /     /                       \\        /     /                         \ \
              /      /                         \ \      /     /                          \  \
             /     /                            \  \   /     /                             \  \
           /     /             _----_            \   \ /     /             _----_           \   \
          /     /           _-~      ~-_         |   |/     /           _-~      ~-_         |   |
         (     (         _-~    _--_    ~-_     _/   (     (         _-~    _--_    ~-_     _/   |
          \      ~-____-~    _-~    ~-_    ~-_-~    / \      ~-____-~    _-~    ~-_    ~-_-~    /
            ~-_           _-~          ~-_       _-~   ~-_           _-~          ~-_       _-~
               ~--______-~                ~-___-~         ~--______-~                ~-___-~
'@
Write-Host $art -ForegroundColor Blue

Say-Section "####  Preflight Checks ####"
Show-Check -Label "Default Python found! ($defaultPythonPath)" -Ok (Test-Path $defaultPythonPath)
Show-Check -Label "Working Folder ($srcDir)" -Ok (Test-Path $srcDir)
Show-Check -Label "Extensions_path.ini ($extensionsPath)" -Ok (Test-Path $extensionsPath)


# ============================ Helpers: Console =========================
function Read-LineWithTimeout {
    param([int]$Seconds = 7)
    $deadline = (Get-Date).AddSeconds($Seconds)
    $sb = New-Object System.Text.StringBuilder
    while ((Get-Date) -lt $deadline) {
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            if ($key.Key -eq 'Enter') { break }
            elseif ($key.Key -eq 'Backspace') { if ($sb.Length -gt 0) { $sb.Length--; Write-Host "`b `b" -NoNewline } }
            else { [void]$sb.Append($key.KeyChar); Write-Host $key.KeyChar -NoNewline }
        } else { Start-Sleep -Milliseconds 50 }
    }
    return $sb.ToString()
}

# --- Name-Validation (nur A–Z, a–z, 0–9) ---
function Read-EnvNameAlnum {
    param(
        [int]$Seconds = 15,
        [string]$Prompt = 'Enter a unique environment name (letters/digits only, required): '
    )
    Write-Host $Prompt -ForegroundColor Yellow -NoNewline
    $name = Read-LineWithTimeout -Seconds $Seconds
    Write-Host ''
    if ([string]::IsNullOrWhiteSpace($name)) { return $null }
    $name = $name.Trim()
    if ($name -notmatch '^[A-Za-z0-9]+$') {
        Say-Err 'Invalid name. Allowed are letters and digits only (A-Z, a-z, 0-9).'
        return $null
    }
    return $name
}

# ============================ Helpers: Python Install ==================
function Test-WingetAvailable {
    try { Get-Command winget -ErrorAction Stop | Out-Null; $true }
    catch { $false }
}

function Ensure-PyenvWin {
    $root = Join-Path $env:USERPROFILE ".pyenv\pyenv-win"
    if (Test-Path $root) { return $true }

    # TLS 1.2 sicherstellen 
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

    # 1) Versuche GitHub RAW
    $urls = @(
        'https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1',
        'https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1?raw=1'
    )
    foreach ($u in $urls) {
        try {
            Say-Info "Downloading pyenv-win installer: $u"
            $tmp = Join-Path $env:TEMP "install-pyenv-win.ps1"
            Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $tmp
            & $tmp
            Remove-Item $tmp -Force -ErrorAction SilentlyContinue
            break
        } catch {
            Say-Warn ("pyenv-win RAW download failed: {0}" -f $_.Exception.Message)
        }
    }

    # 2) winget Fallback
    if (-not (Test-Path $root)) {
        try {
            if (Get-Command winget -ErrorAction SilentlyContinue) {
                Say-Info "Installing pyenv-win via winget..."
                winget install --id pyenv-win.pyenv-win -e --accept-source-agreements --accept-package-agreements
            }
        } catch {
            Say-Warn ("winget install failed: {0}" -f $_.Exception.Message)
        }
    }

    # 3) Git Fallback
    if (-not (Test-Path $root)) {
        try {
            if (Get-Command git -ErrorAction SilentlyContinue) {
                Say-Info "Cloning pyenv-win via git..."
                git clone https://github.com/pyenv-win/pyenv-win.git $root
            }
        } catch {
            Say-Warn ("git clone failed: {0}" -f $_.Exception.Message)
        }
    }

    # PATH ergänzen
    $pyenvBin = Join-Path $env:USERPROFILE ".pyenv\pyenv-win\bin"
    $pyenvShm = Join-Path $env:USERPROFILE ".pyenv\pyenv-win\shims"
    if (Test-Path $pyenvBin) {
        $env:Path = "$pyenvBin;$pyenvShm;$env:Path"
        Say-Ok "pyenv-win installiert."
        return $true
    }

    Say-Err "pyenv-win installation failed (all methods)."
    return $false
}


function Test-PyenvAvailable {
    try { Get-Command pyenv -ErrorAction Stop | Out-Null; $true } catch {
        $pyenvBin = Join-Path $env:USERPROFILE ".pyenv\pyenv-win\bin"
        $pyenvShm = Join-Path $env:USERPROFILE ".pyenv\pyenv-win\shims"
        if (Test-Path $pyenvBin) { $env:Path = "$pyenvBin;$pyenvShm;$env:Path" }
        try { Get-Command pyenv -ErrorAction Stop | Out-Null; $true } catch { $false }
    }
}

function Install-Python-WithPyenv {
    param([string]$Version)
    if (-not (Test-PyenvAvailable)) {
        if (-not (Ensure-PyenvWin)) { return $false }
        if (-not (Test-PyenvAvailable)) { return $false }
    }
    Say-Info ("Installing Python {0} via pyenv-win..." -f $Version)
    try { pyenv install -q $Version; Say-Ok ("Python {0} install (pyenv)" -f $Version); return $true }
    catch { Say-Err ("pyenv install failed: {0}" -f $_.Exception.Message); return $false }
}

function Find-PyenvPythonPath {
    param([string]$Version)
    $base = Join-Path $env:USERPROFILE ".pyenv\pyenv-win\versions\$Version"
    $py = Join-Path $base "python.exe"
    if (Test-Path $py) { return $py }
    $cand = Get-ChildItem -Path $base -Recurse -Filter python.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cand) { return $cand.FullName }
    return $null
}

function Install-Python-WithWinget {
    param([string]$Minor) # "3.10"
    if (-not (Test-WingetAvailable)) { return $false }
    $idMap = @{
        '3.7'='Python.Python.3.7'; '3.8'='Python.Python.3.8'; '3.9'='Python.Python.3.9'
        '3.10'='Python.Python.3.10'; '3.11'='Python.Python.3.11'; '3.12'='Python.Python.3.12'
        '3.13'='Python.Python.3.13'; '3.14'='Python.Python.3.14'
    }
    $pkgId = $idMap[$Minor]
    if (-not $pkgId) { Say-Warn ("winget: no mapping for Python {0}" -f $Minor); return $false }
    Say-Info ("Installing Python {0} via winget ({1})..." -f $Minor, $pkgId)
    try { winget install --id $pkgId --silent --accept-source-agreements --accept-package-agreements; Say-Ok ("Python {0} installiert (winget)" -f $Minor); return $true }
    catch { Say-Err "winget install failed."; return $false }
}

function Ensure-Python-Version {
    param([string]$Desired)

    if ($Desired -match '^\d+\.\d+\.\d+$') {
        if (Install-Python-WithPyenv -Version $Desired) {
            $pp = Find-PyenvPythonPath -Version $Desired
            if ($pp) { return $pp }
        }
    } else {
        if (Install-Python-WithPyenv -Version $Desired) {
            try {
                $vers = (& pyenv versions --bare) 2>$null
                if ($vers) {
                    $patch = ($vers -split "(`r`n|`n|`r)" |
                              Where-Object { $_ -like "$Desired.*" } |
                              Sort-Object { [version]$_ } -Descending |
                              Select-Object -First 1)
                    if ($patch) {
                        $pp = Find-PyenvPythonPath -Version $patch
                        if ($pp) { return $pp }
                    }
                }
            } catch {}
        }
        if (Install-Python-WithWinget -Minor $Desired) {
            $guesses = @(
                "$env:LOCALAPPDATA\Programs\Python\Python$($Desired -replace '\.','')\python.exe",
                "C:\Python$($Desired -replace '\.','')\python.exe"
            )
            foreach ($g in $guesses) { if (Test-Path $g) { return $g } }
        }
    }
    return $null
}


# ============================ Helpers: venv / pip ======================
function Ensure-Pip {
    param([string]$PythonExe)
    try { & $PythonExe -m pip --version 2>$null | Out-Null; if ($LASTEXITCODE -ne 0) { throw "pip missing" } }
    catch {
        Say-Warn "pip not found - bootstrapping via ensurepip..."
        try { & $PythonExe -m ensurepip --upgrade | Out-Null } catch {}
    }
    try { & $PythonExe -m pip install --upgrade --disable-pip-version-check pip | Out-Null } catch {}
}

function New-IsolatedVenv {
    param([string]$BasePythonExe, [string]$VenvRoot, [string]$VenvName)
    if (-not (Test-Path $VenvRoot)) { New-Item -ItemType Directory -Path $VenvRoot -Force | Out-Null }
    $venvPath = Join-Path $VenvRoot $VenvName
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if (Test-Path $venvPython) { return $venvPython }
    Say-Info ("Creating venv: {0}" -f $venvPath)
    & $BasePythonExe -m venv $venvPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) { Say-Err "Failed to create venv."; return $null }
    Say-Ok "venv erstellt."
    return $venvPython
}

# ============================ Helpers: Detection =======================
function Get-PythonCandidates {
    param([string]$expectedMinor)
    $candidates = @()
    try {
        $list = (& py -0p) 2>$null
        if ($list) {
            foreach ($line in $list) {
                if ($line -match '^\s*-\w*V:(?<ver>\d+\.\d+)(?:\s+\*)?\s+(?<path>.+python\.exe)\s*$') {
                    $ver  = $Matches['ver']; $path = $Matches['path'].Trim(); $isDefault = ($line -match '\s\*')
                    $candidates += [pscustomobject]@{ Version=$ver; Path=$path; IsDefault=$isDefault; Source='py -0p'; Bits=$null }
                }
            }
        }
    } catch {}
    if ($defaultPythonPath -and (Test-Path $defaultPythonPath)) {
        if (-not ($candidates | Where-Object { $_.Path -ieq $defaultPythonPath })) {
            try {
                $verOut = & $defaultPythonPath --version 2>$null
                if ($verOut -match 'Python\s+(?<v>\d+\.\d+)') {
                    $candidates += [pscustomobject]@{ Version=$Matches['v']; Path=$defaultPythonPath; IsDefault=$false; Source='configured'; Bits=$null }
                }
            } catch {}
        }
    }
    $pyenvRoot = Join-Path $env:USERPROFILE ".pyenv\pyenv-win\versions"
    if (Test-Path $pyenvRoot) {
        $vers = Get-ChildItem -Path $pyenvRoot -Directory -ErrorAction SilentlyContinue
        foreach ($v in $vers) {
            $pyexe = Get-ChildItem -Path $v.FullName -Recurse -Filter python.exe -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($pyexe) {
                try {
                    $verOut = & $pyexe.FullName --version 2>$null
                    if ($verOut -match 'Python\s+(?<v>\d+\.\d+)') {
                        $candidates += [pscustomobject]@{ Version=$Matches['v']; Path=$pyexe.FullName; IsDefault=$false; Source='pyenv'; Bits=$null }
                    }
                } catch {}
            }
        }
    }

    $candidates = $candidates | Sort-Object Path -Unique
    foreach ($c in $candidates) {
        try { $bits = & $c.Path -c "import struct; print(struct.calcsize('P')*8)" 2>$null; if ($bits) { $c.Bits = [string]$bits.Trim() } }
        catch { $c.Bits = $null }
    }
    $candidates = $candidates | Sort-Object `
        @{ Expression = { if ($expectedMinor -and $_.Version -eq $expectedMinor) { 0 } else { 1 } }; Ascending = $true }, `
        @{ Expression = { if ($_.IsDefault) { 0 } else { 1 } }; Ascending = $true }, `
        @{ Expression = { [version]("{0}.0" -f $_.Version) }; Descending = $true }
    return $candidates
}

# ---- Liste vorhandener venvs finden ----
function Get-ExistingVenvs {
    param([string]$VenvRoot)

    $venvs = @()
    $root  = [System.Environment]::ExpandEnvironmentVariables($VenvRoot)

    Say-Info ("Scanning for venvs in: {0}" -f $root)
    if (-not (Test-Path $root)) {
        Say-Info ("Venv root not found: {0}" -f $root)
        return $venvs
    }

    $candidates = @()
    try {
        $candidates += Get-ChildItem -Path $root -Directory -Recurse -ErrorAction SilentlyContinue
    } catch {}
    $rootAsDir = Get-Item -Path $root -ErrorAction SilentlyContinue
    if ($rootAsDir -and $rootAsDir.PSIsContainer) { $candidates += $rootAsDir }

    foreach ($d in ($candidates | Sort-Object FullName -Unique)) {
        $py = Join-Path $d.FullName "Scripts\python.exe"
        if (-not (Test-Path $py)) {
            $pyw = Join-Path $d.FullName "Scripts\pythonw.exe"
            if (Test-Path $pyw) { $py = $pyw } else { continue }
        }

        $ver = ""
        try { $ver = (& $py -c "import sys; print('%d.%d.%d' % sys.version_info[:3])") 2>$null } catch {}
        $venvs += [pscustomobject]@{
            Name    = (Split-Path $d.FullName -Leaf)
            Path    = (Resolve-Path $py).Path
            Version = $ver
        }
    }

    $venvs = @($venvs | Sort-Object Path -Unique)
    Say-Info ("Found {0} venv(s) under {1}" -f $venvs.Count, $root)
    return $venvs
}

function Remove-Venv {
    param([Parameter(Mandatory=$true)][string]$VenvRoot)

    $venvs = Get-ExistingVenvs -VenvRoot $VenvRoot
    $venvs = @($venvs)  # <- erzwinge Array, auch wenn nur 1 Element

    if (-not $venvs -or $venvs.Count -eq 0) {
        Say-Warn "No environments found under: $VenvRoot"
        return
    }

    Say-Section "Delete environment"

    # Index-Lookup aufbauen (stabiler als $venvs[$idx-1])
    $indexMap = @{}
    $i = 1
    foreach ($v in $venvs) {
        $venvDir = Split-Path -Parent (Split-Path -Parent $v.Path)
        $verLabel = if ($v.Version) { $v.Version } else { '?' }
        Write-Host ("[{0}] {1,-21} -> {2}  (Python {3})" -f $i, $v.Name, $venvDir, $verLabel)
        $indexMap[$i] = [pscustomobject]@{
            Name    = $v.Name
            Path    = $v.Path
            Dir     = $venvDir
            Version = $v.Version
        }
        $i++
    }
    Write-Host "[X] Cancel`n"
    Write-Host "Enter the number of the environment to delete (auto-cancel in 20s):" -ForegroundColor Yellow
    Write-Host -NoNewline "> "
    $choice = Read-LineWithTimeout -Seconds 20
    Write-Host ""

    # Eingabe normalisieren
    $choice = ($choice -replace '[^\x20-\x7E]', '').Trim()

    if ([string]::IsNullOrWhiteSpace($choice) -or $choice -match '^[Xx]$') {
        Say-Info "Delete cancelled."
        return
    }

    if ($choice -notmatch '^\d+$') {
        Say-Warn "Invalid selection."
        return
    }

    $idx = [int]$choice
    if (-not $indexMap.ContainsKey($idx)) {
        Say-Warn "Invalid selection."
        return
    }

    $sel = $indexMap[$idx]
    $venvDirFull  = (Resolve-Path $sel.Dir).Path

    # Safety-Check: nur unter $VenvRoot löschen
    $rootExpanded = [System.Environment]::ExpandEnvironmentVariables($VenvRoot)
    $rootFull     = (Resolve-Path $rootExpanded).Path
    if ($venvDirFull -notlike ($rootFull + "\*")) {
        Say-Err "Safety check failed: Refusing to delete outside of $rootFull"
        return
    }

    try {
        Say-Info ("Deleting: {0}" -f $venvDirFull)
        Remove-Item -LiteralPath $venvDirFull -Recurse -Force -ErrorAction Stop
        Say-Ok ("Environment '{0}' deleted." -f $sel.Name)
    } catch {
        Say-Err ("Failed to delete environment: {0}" -f $_.Exception.Message)
    }
}
function Get-PyenvInstallableVersions {
    # Liefert alle von pyenv installierbaren CPython-Versionen als Liste (z.B. 3.10.11, 3.11.9, 3.12.6 ...)
    if (-not (Test-PyenvAvailable)) {
        if (-not (Ensure-PyenvWin)) { return @() }
    }
    try {
        $out = (& pyenv install -l) 2>$null
        if (-not $out) { return @() }
        # nur "3.x.y", keine dev/stackless/micro etc.
        $list = @()
        foreach ($line in $out) {
            $t = $line.Trim()
            if ($t -match '^(?<maj>\d+)\.(?<min>\d+)\.(?<pat>\d+)$') {
                $list += $t
            }
        }
        return $list
    } catch { return @() }
}

function Pick-PythonVersionFromList {
    param(
        [string]$preferredMinor = '3.10', 
        [string]$pyarmorMin = '3.7',
        [string]$pyarmorMax1 = '3.11',
        [string]$pyarmorMax2 = '3.13'     
    )

    $all = Get-PyenvInstallableVersions
    if ($all.Count -eq 0) {
        Say-Warn "pyenv liefert keine installierbaren Versionen. Fallback: manuelle Eingabe."
        return $null
    }

    # Nur 3.x anzeigen, und visuell kennzeichnen ob PyArmor kompatibel
    $candidates = $all | Where-Object { $_ -match '^3\.\d+\.\d+$' }

    # sortieren: bevorzugtes Minor nach oben, dann neueste zuerst
    $candidates = $candidates | Sort-Object {
        $m = [version]($_)
        $bias = if ($_.StartsWith($preferredMinor + '.')) { 0 } else { 1 }
        "{0}-{1:0000000000}" -f $bias, ([int64]$m.Build + 1000*[int64]$m.Revision + 100000*[int64]$m.Minor + 10000000*[int64]$m.Major)
    }

    # Liste rendern (max. 30 Items, sonst zu lang)
    $show = $candidates | Select-Object -First 30
    Say-Section "Installable Python-Versions (pyenv)"
    $i = 1
    foreach ($v in $show) {
        $majmin = [version]$v
        $minor  = "{0}.{1}" -f $majmin.Major, $majmin.Minor
        $ok =
            (($majmin -ge [version]$pyarmorMin) -and ($majmin -le [version]$pyarmorMax1)) -or
            (($majmin -ge [version]'3.12') -and ($majmin -le [version]$pyarmorMax2))
        $tag = if ($ok) { "[PyArmor - OK]" } else { "[No PyArmor!]" }
        $fc = if ($ok) { 'Green' } else { 'Yellow' }
		Write-Host ("[{0}] {1}  {2}" -f $i, $v, $tag) -ForegroundColor $fc

        $i++
    }
    Write-Host "[M] Type Value"
    Write-Host "[X] Cancel"
    Write-Host -NoNewline "> "
    $choice = Read-LineWithTimeout -Seconds 20
    Write-Host ""

    if ([string]::IsNullOrWhiteSpace($choice)) { return $null }
    if ($choice -match '^[Xx]$') { return $null }
    if ($choice -match '^[Mm]$') {
        Write-Host "Set Version:" -ForegroundColor Yellow
        Write-Host -NoNewline "> "
        $manual = Read-LineWithTimeout -Seconds 20
        return ($manual.Trim())
    }

    $idx = 0
    if ([int]::TryParse($choice, [ref]$idx)) {
        if ($idx -ge 1 -and $idx -le $show.Count) { return $show[$idx-1] }
    }
    Say-Warn "Ungültige Auswahl."
    return $null
}

# ---- UPDATED: Auswahl inkl. vorhandener venvs + Custom-Namen für neue venvs ----
function Choose-Existing-Or-Venv {
    param(
        [array]$candidates,
        [string]$defaultPath,
        [string]$venvRoot
    )

    $candidates = @($candidates)
    $venvs      = @($(Get-ExistingVenvs -VenvRoot $venvRoot))

    if (($candidates.Count -eq 0) -and ($venvs.Count -eq 0)) {
        Say-Warn "No existing Pythons or venvs found. Press [Enter] to attempt venv creation..."
        return [pscustomobject]@{ Mode='venv'; PythonPath=$null; DesiredVersion=$null }
    }

    Write-Host ""
    Say-Section "Available Python Versions"
    $items = @()
    $i = 1

    foreach ($c in $candidates) {
        $tagDefault = if ($c.IsDefault) { " *" } else { "" }
        $bitsLabel  = if ($c.Bits) { " ($($c.Bits)-bit)" } else { "" }
        Write-Host ("[{0}] Python {1}{2}  -> {3}{4}" -f $i, $c.Version, $bitsLabel, $c.Path, $tagDefault)
        $items += [pscustomobject]@{ Kind='sys'; Path=$c.Path }
        $i++
    }

    Say-Section ("Virtual environments ({0})" -f $venvRoot)
    if ($venvs.Count -gt 0) {
        foreach ($v in $venvs) {
            Write-Host ("[{0}] {1,-21} -> {2}  (Python {3})" -f $i, $v.Name, $v.Path, ($v.Version -or '?'))
            $items += [pscustomobject]@{ Kind='venv'; Path=$v.Path }
            $i++
        }
    } else {
        Write-Host "  (none found here)" -ForegroundColor DarkGray
    }
    Say-Section ("More Options" -f $venvRoot)
    Write-Host "[V] New environment (Experimental, check Extensions in GUI -> pyinstaller path)"
    Write-Host "[D] Delete environment"
    Write-Host "[X] Cancel`n"

    $defaultCandidatePath = $null
    if ($defaultPath -and (Test-Path $defaultPath)) {
        $defaultCandidatePath = $defaultPath
    } elseif ($candidates.Count -gt 0) {
        $defaultCandidatePath = $candidates[0].Path
    } elseif ($venvs.Count -gt 0) {
        $defaultCandidatePath = $venvs[0].Path
    }

    Write-Host ("Press a number...")
    Write-Host ("or press [V] to create a new isolated venv.")
    if ($defaultCandidatePath) {
        Write-Host ("Auto-Start in 10s: {0}" -f $defaultCandidatePath) -ForegroundColor Yellow
    }
    Write-Host -NoNewline "> "

    $choice = Read-LineWithTimeout -Seconds 10
    Write-Host ""
    $choice = ($choice -replace '[^\x20-\x7E]', '').Trim()

    if ([string]::IsNullOrWhiteSpace($choice)) {
        if ($defaultCandidatePath) {
            return [pscustomobject]@{ Mode='existing'; PythonPath=$defaultCandidatePath; DesiredVersion=$null }
        } else {
            return [pscustomobject]@{ Mode='venv'; PythonPath=$null; DesiredVersion=$null }
        }
    }

    if ($choice -match '^[Xx]$') { return $null }
    if ($choice -match '^[Dd]$') {
        Remove-Venv -VenvRoot $venvRoot
        return Choose-Existing-Or-Venv -candidates (Get-PythonCandidates -expectedMinor $expectedMinor) -defaultPath $defaultPythonPath -venvRoot $venvRoot
    }
    if ($choice -match '^[VvNn]$') {
		$verChoice = Pick-PythonVersionFromList -preferredMinor $expectedMinor
		if ([string]::IsNullOrWhiteSpace($verChoice)) {
			Say-Info ("Keine Auswahl getroffen - nehme Default {0}" -f $desiredPythonVersion)

			$verChoice = $desiredPythonVersion
		}
        $envName = Read-EnvNameAlnum -Seconds 20 -Prompt 'Enter a unique environment name (letters/digits only, required): '
        if (-not $envName) {
            Say-Err 'No valid name provided. Cancelling.'
            return $null
        }

        return [pscustomobject]@{
            Mode='venv'
            PythonPath=$null
            DesiredVersion=$verChoice
            CustomName=$envName
        }
    }

    $idx = 0
    if ([int]::TryParse($choice, [ref]$idx)) {
        if ($idx -ge 1 -and $idx -le $items.Count) {
            $picked = $items[$idx-1]
            return [pscustomobject]@{ Mode='existing'; PythonPath=$picked.Path; DesiredVersion=$null }
        } else {
            Say-Warn "Invalid selection."
            return $null
        }
    }

    $norm = $choice.Trim('"', "'"); $norm = $norm -replace '/', '\'
    if ($norm -match '(?i)python\.exe$' -and (Test-Path $norm)) {
        return [pscustomobject]@{ Mode='existing'; PythonPath=$norm; DesiredVersion=$null }
    }

    Say-Warn "Please enter a valid number, 'V' for venv, or an existing path to python.exe."
    return $null
}

# ============================ Tool detection/where =====================
function Get-PyDistVersion { param([string]$PythonExe,[string]$DistName)
$py=@"
import sys
try:
    try:
        from importlib.metadata import version, PackageNotFoundError
    except Exception:
        from importlib_metadata import version, PackageNotFoundError
    try:
        print(version('$DistName'))
    except PackageNotFoundError:
        print('')
except Exception:
    print('')
"@; try {$out=& $PythonExe -c $py 2>$null; if($out){$out.Trim()}} catch { $null } }

function Get-PyModuleVersion {
    param([string]$PythonExe,[string]$Module,[string]$Regex,[string]$AltModule)
    try {
        $raw = & $PythonExe -m $Module --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $raw) {
            $m = [regex]::Match($raw, $Regex)
            if ($m.Success) { return $m.Groups['v'].Value.Trim() }
        }
    } catch {}

    if ($AltModule) {
        try {
            $raw = & $PythonExe -m $AltModule --version 2>$null
            if ($LASTEXITCODE -eq 0 -and $raw) {
                $m = [regex]::Match($raw, $Regex)
                if ($m.Success) { return $m.Groups['v'].Value.Trim() }
            }
        } catch {}
    }

    try {
        $py = @"
import importlib, sys
try:
    m = importlib.import_module('$Module')
    v = getattr(m, '__version__', None)
    if v is None and '$Module' == 'nuitka':
        try:
            from nuitka import Version
            v = getattr(Version, 'getNuitkaVersion', lambda: None)()
        except Exception:
            v = None
    print(v or '')
except Exception:
    print('')
"@
        $out = & $PythonExe -c $py 2>$null
        if ($out -and $out.Trim().Length -gt 0) { return $out.Trim() }
    } catch {}

    return $null
}

function Get-PyModulePath { param([string]$PythonExe,[string]$Module)
$py=@"
import importlib, importlib.util, sys, os
try:
    m = importlib.import_module('$Module')
    p = getattr(m, '__file__', None)
    if p:
        print(os.path.dirname(os.path.abspath(p)))
    else:
        spec = importlib.util.find_spec('$Module')
        if spec and spec.submodule_search_locations:
            print(os.path.abspath(list(spec.submodule_search_locations)[0]))
        else:
            print('')
except Exception:
    print('')
"@; try {$out=& $PythonExe -c $py 2>$null; if($out){$out.Trim()}} catch { $null } }

function Get-PyScriptsDir { param([string]$PythonExe)
    $py=@"
import sysconfig
try:
    print(sysconfig.get_path('scripts'))
except Exception:
    print('')
"@; try {$out=& $PythonExe -c $py 2>$null; if($out){return $out.Trim()}} catch { } return $null }

# --- NEW: User-Scripts & Multi-Dirs
function Get-PyUserScriptsDir {
    param([string]$PythonExe)
    $py=@"
import sysconfig, site, os
try:
    p = sysconfig.get_paths('nt_user').get('scripts','')
    if not p:
        p = os.path.join(site.USER_BASE, 'Scripts')
    print(p)
except Exception:
    try:
        import site, os
        print(os.path.join(site.USER_BASE, 'Scripts'))
    except Exception:
        print('')
"@
    try { $out = & $PythonExe -c $py 2>$null; if ($out) { return $out.Trim() } } catch {}
    return $null
}

function Resolve-ToolPath-InDirs {
    param([string[]]$Dirs,[string]$ExecName)
    foreach ($d in $Dirs) {
        if (-not $d) { continue }
        $c1 = Join-Path $d ($ExecName + ".exe"); if (Test-Path $c1) { return (Resolve-Path $c1).Path }
        $c2 = Join-Path $d ($ExecName + ".cmd"); if (Test-Path $c2) { return (Resolve-Path $c2).Path }
        $c3 = Join-Path $d ($ExecName);          if (Test-Path $c3) { return (Resolve-Path $c3).Path }
    }
    return $null
}

function Resolve-ExecPath { param([string]$PythonExe,[string]$Name)
    try { $cmd = Get-Command $Name -ErrorAction SilentlyContinue } catch { $cmd=$null }
    if ($cmd) { return $cmd.Path }
    $scripts = Get-PyScriptsDir -PythonExe $PythonExe
    if ($scripts) {
        $c1 = Join-Path $scripts ($Name + '.exe'); if (Test-Path $c1) { return $c1 }
        $c2 = Join-Path $scripts ($Name); if (Test-Path $c2) { return $c2 }
        $c3 = Join-Path $scripts ($Name + '.cmd'); if (Test-Path $c3) { return $c3 }
    }
    return $null
}

function Resolve-ByWhere {
    param([Parameter(Mandatory)][string]$ExecName)
    try {
        $out = & where.exe $ExecName 2>$null
        if ($out) {
            return ($out -split "(`r`n|`n|`r)")[0].Trim()
        }
    } catch {}
    return $null
}

$tools = @(
	@{ Name='PyInstaller'; Dist='pyinstaller'; Module='PyInstaller'; AltModule=$null; Pkg='pyinstaller'; Regex='(?i)(?<v>\d+(\.\d+){1,3})'; Exec='pyinstaller' },
	@{ Name='PyArmor'; Dist='pyarmor'; Module='pyarmor'; AltModule='pyarmor.cli'; Pkg='pyarmor>=9.1.6'; Regex='(?i)(?<v>\d+(\.\d+){1,3})'; Exec='pyarmor' },
    @{ Name='Nuitka';  Dist='nuitka';  Module='nuitka';  AltModule=$null;          Pkg='nuitka';         Regex='(?i)(?<v>\d+(\.\d+){1,3})'; Exec='nuitka' },
	@{ Name='Cython';  Dist='Cython';  Module='Cython';  AltModule=$null;          Pkg='cython';         Regex='(?i)(?<v>\d+(\.\d+){1,3})'; Exec='cython' },
    @{ Name='Pytest';  Dist='pytest';  Module='pytest';  AltModule=$null;          Pkg='pytest';         Regex='(?i)pytest\s+(?<v>\d+(\.\d+){1,3})'; Exec='pytest' },
    @{ Name='Sphinx';  Dist='Sphinx';  Module='sphinx';  AltModule=$null;          Pkg='sphinx';         Regex='(?i)(sphinx\s+)?(?<v>\d+(\.\d+){1,3})'; Exec='sphinx-build' }
	
)

$global:toolResults = @()

function Show-ToolStatus {
    param([string]$Header, [string]$PythonExe)
    Say-Section $Header
    $missing = @(); $results=@()
    foreach ($t in $tools) {
        $ver = Get-PyDistVersion -PythonExe $PythonExe -DistName $t.Dist
        if (-not $ver) { $ver = Get-PyModuleVersion -PythonExe $PythonExe -Module $t.Module -Regex $t.Regex -AltModule $t.AltModule }
        if ($ver) {
            Write-Host ("[OK]   {0,-8}: v{1}" -f $t.Name, $ver) -ForegroundColor Green
            $modPath  = Get-PyModulePath -PythonExe $PythonExe -Module $t.Module
            $execPath = if ($t.Exec) { Resolve-ExecPath -PythonExe $PythonExe -ExecName $t.Exec } else { $null }
            $results += [pscustomobject]@{ Name=$t.Name; Version=$ver; ModulePath=$modPath; ExecPath=$execPath }
        } else {
            Write-Host ("[ERR]  {0,-8}: NOT FOUND" -f $t.Name) -ForegroundColor Red
            $missing += $t
        }
    }
    $global:toolResults = $results
    return ,$missing
}

# ============================ Auswahl: bestehend ODER venv =============
$candidates = Get-PythonCandidates -expectedMinor $expectedMinor
$selection  = Choose-Existing-Or-Venv -candidates $candidates -defaultPath $defaultPythonPath -venvRoot $venvRoot
if (-not $selection) { Say-Warn "Cancelled."; exit 1 }

$pythonPath = $null
$usedVenv   = $false

if ($selection.Mode -eq 'existing') {
    $pythonPath = $selection.PythonPath
    Show-Check -Label ("Chosen Python-Exe: {0}" -f $pythonPath) -Ok (Test-Path $pythonPath)
    $usedVenv = ($pythonPath -like "$venvRoot*")
    Ensure-Pip -PythonExe $pythonPath
} elseif ($selection.Mode -eq 'venv') {
    $usedVenv = $true
    $want = $selection.DesiredVersion
    if ([string]::IsNullOrWhiteSpace($want)) { $want = $desiredPythonVersion }
    $basePy = $null

    $already = Get-PythonCandidates -expectedMinor ''
    $basePy = ($already | Where-Object {
        if ($want -match '^\d+\.\d+\.\d+$') { $_.Path -and (& $_.Path -c "import sys; print('.'.join(map(str,sys.version_info[:3])))") -eq $want }
        else { $_.Version -eq ($want -replace '^(\d+\.\d+).*','$1') }
    } | Select-Object -First 1).Path

    if (-not $basePy -and $allowInstallPython) {
        $basePy = Ensure-Python-Version -Desired $want
    }
    if (-not $basePy) {
        Say-Err ("Could not find or install Python {0}." -f $want)
        exit 10
    }

    $custom = $selection.CustomName
    if (-not $custom) {
        $custom = (Get-Date -Format 'yyyyMMddHHmmss')
        Say-Warn ("Empty custom name; using timestamp: {0}" -f $custom)
    }
    $venvName = "autopypp-$($want -replace '\.','_')-$custom"
    $pythonPath = New-IsolatedVenv -BasePythonExe $basePy -VenvRoot $venvRoot -VenvName $venvName
    if (-not $pythonPath) { exit 11 }
    Ensure-Pip -PythonExe $pythonPath
}

if (!(Test-Path $srcDir)) { Say-Err "Folder not found: $srcDir"; exit 1 }

# ============================ Diagnostics ==============================
Say-Section "Python/AutoPy++ Diagnostic"
& $pythonPath --version
$pyMajMin  = & $pythonPath -c "import sys; print('%d.%d' % (sys.version_info[0], sys.version_info[1]))"
$pyPatch   = & $pythonPath -c "import sys; print(sys.version_info[2])"
$pyverFull = & $pythonPath -c "import sys; print(sys.version.replace('\n',' '))"
Show-Item -Name "Selected Python" -Value ("{0}.{1}  (full: {2})" -f $pyMajMin, $pyPatch, $pyverFull)

if ($expectedMinor -and ($pyMajMin -ne $expectedMinor)) {
    Say-Warn ("Preferred minor is {0}, but you selected {1}.{2}. Continuing..." -f $expectedMinor, $pyMajMin, $pyPatch)
} else {
    Say-Ok ("Minor-Version passt: {0}" -f $pyMajMin)
}

& $pythonPath -c "import sys,platform,struct; 
print('sys.version =', sys.version.replace('\n',' '));
print('build       =', platform.python_build());
print('arch        =', platform.architecture());
print('bits        =', struct.calcsize('P')*8);
print('executable  =', sys.executable);
print('prefix      =', sys.prefix);
print('base_prefix =', sys.base_prefix);
print('in_venv     =', sys.prefix != sys.base_prefix)
"

& $pythonPath -c "import sys,site;
print('sys.path:'); [print('  ',p) for p in sys.path];
print('site-packages:' );
try:
    [print('  ',p) for p in site.getsitepackages()]
except Exception:
    print('  ', site.getusersitepackages())
"

& $pythonPath -m pip --version

# ============================ PyArmor Suitability ======================
Say-Section "PyArmor Compatibility Recommendation"
$pyMajor     = [int]($pyMajMin.Split('.')[0])
$pyMinorNum  = [int]($pyMajMin.Split('.')[1])
$pyVersion   = [version]("$pyMajor.$pyMinorNum")
$pyarmorSupported      = $true
$pyarmorBestTargets    = 'Best targets: Python 3.10 or 3.11 for stability and broad tooling support.'
$pyarmorRecommendation = ''

if ($pyVersion -lt [version]'3.7') {
    $pyarmorSupported = $false
    $pyarmorRecommendation = ("NO PyArmor support for Python {0}. Please use Python 3.10 or 3.11 with PyArmor 8.x or 9.x." -f $pyMajMin)
}
elseif ($pyVersion -ge [version]'3.7' -and $pyVersion -le [version]'3.11') {
    $pyarmorRecommendation = ("Use PyArmor 8.x or 9.x with Python {0}. {1}" -f $pyMajMin, $pyarmorBestTargets)
}
elseif ($pyVersion -ge [version]'3.12' -and $pyVersion -le [version]'3.13') {
    $pyarmorRecommendation = ("Use PyArmor 9.x (>= 9.1.6 preferred) with Python {0}. {1}" -f $pyMajMin, $pyarmorBestTargets)
}
else {
    $pyarmorSupported = $false
    $pyarmorRecommendation = ("NO official PyArmor support known for Python {0}. {1}" -f $pyMajMin, $pyarmorBestTargets)
}

if (-not $pyarmorSupported) {
    Say-Err "Supported by PyArmor: NO"
    Write-Host ("Recommendation: {0}" -f $pyarmorRecommendation)
    Say-Err "Aborting due to missing PyArmor support."
    exit 2
} else {
    Say-Ok "Supported by PyArmor: YES"
    Write-Host ("Recommendation: {0}" -f $pyarmorRecommendation)
}

Write-Host "Version matrix:"
Write-Host " - Python 3.7 - 3.11  -> PyArmor 8.x or 9.x"
Write-Host " - Python 3.12 - 3.13 -> PyArmor 9.x (>= 9.1.6 preferred)"
Write-Host " - Other versions     -> Not supported by PyArmor"

# ============================ Tools: install & where ===================
$missing = Show-ToolStatus -Header "Tool Presence (selected Python env)" -PythonExe $pythonPath
if ($missing.Count -gt 0 -and $autoInstallMissing) {
    Say-Section "Installing missing tools into the selected Python environment..."
    foreach ($t in $missing) {
        try {
            Say-Info ("pip install {0}" -f $t.Pkg)
            & $pythonPath -m pip install --disable-pip-version-check $t.Pkg
        } catch {
            Say-Err ("Install failed for {0}" -f $t.Name)
        }
    }
    $missing = Show-ToolStatus -Header "Tool Presence (re-check)" -PythonExe $pythonPath
}

if ($missing.Count -gt 0) {
    $names = ($missing | ForEach-Object { $_.Name }) -join ', '
    Say-Warn ("Missing: {0}" -f $names)
    if ($enforceToolPresence) {
        Say-Err "Aborting because required tools are missing."
        exit 3
    } else {
        Write-Host "Note: continuing despite missing tools (set `$enforceToolPresence = `$true to abort)." -ForegroundColor DarkYellow
    }
} else {
    Say-Ok "All tools present."
}

# Ausgabe der Ablageorte ("where")
if ($global:toolResults.Count -gt 0) {
    Say-Section "Tool Locations (selected Python env)"
    foreach ($r in $global:toolResults) {
        Write-Host ("{0,-8}: v{1}" -f $r.Name, $r.Version) -ForegroundColor Green
        if ($r.ModulePath) { Write-Host ("  module: {0}" -f $r.ModulePath) -ForegroundColor DarkGray }
        if ($r.ExecPath)   { Write-Host ("  exec  : {0}" -f $r.ExecPath)   -ForegroundColor DarkGray }
    }
}

# ============================ extensions_path.ini Support =====================
function Get-ExtensionsIniPath {
    param([string]$ExplicitIniPath)

    if ($ExplicitIniPath) {
        $p = $ExplicitIniPath.Trim('"','''')
        $p = [System.Environment]::ExpandEnvironmentVariables($p)
        $rp = Resolve-Path -Path $p -ErrorAction SilentlyContinue
        if ($rp) { return $rp.Path }
    }

    $scriptDir = $PSScriptRoot
    if (-not $scriptDir -or $scriptDir.Trim().Length -eq 0) {
        $scriptPath = $MyInvocation.MyCommand.Path
        if ($scriptPath) { $scriptDir = Split-Path -Parent $scriptPath }
    }
    if (-not $scriptDir) { $scriptDir = (Get-Location).Path }

    $candidates = New-Object System.Collections.Generic.List[string]
    $candidates.Add( (Join-Path $scriptDir "extensions_path.ini") )
    $cur = $scriptDir
    for ($i=0; $i -lt 4; $i++) {
        $cur = Split-Path -Parent $cur
        if (-not $cur) { break }
        $candidates.Add( (Join-Path $cur "extensions_path.ini") )
    }

    if ($script:srcDir -or $srcDir) {
        $base = if ($script:srcDir) { $script:srcDir } else { $srcDir }
        $projRoot = Split-Path -Parent $base
        if ($projRoot) { $candidates.Add( (Join-Path $projRoot "extensions_path.ini") ) }
        $subCandidate = Join-Path $base "AutoPyPlusPlus\extensions_path.ini"
        $candidates.Add($subCandidate)
    }

    foreach ($c in $candidates) {
        $rp = Resolve-Path -Path $c -ErrorAction SilentlyContinue
        if ($rp -and (Test-Path $rp.Path)) { return $rp.Path }
    }
    return $null
}

# (alter Single-Dir-Resolver bleibt für andere Call-Sites erhalten)
function Resolve-ToolPath {
    param([string]$PythonExe,[string]$Name)
    $scripts = Get-PyScriptsDir -PythonExe $PythonExe
    if ($scripts) {
        $cands = @(
            (Join-Path $scripts ($Name + ".exe")),
            (Join-Path $scripts ($Name + ".cmd")),
            (Join-Path $scripts $Name)
        )
        foreach ($c in $cands) { if (Test-Path $c) { return (Resolve-Path $c).Path } }
    }
    try { $cmd = Get-Command $Name -ErrorAction SilentlyContinue; if ($cmd) { return $cmd.Source } } catch {}
    return $null
}

function Build-IniUpdatesFromEnv {
    param(
        [Parameter(Mandatory=$true)] [string]$PythonExe,
        [Parameter(Mandatory=$false)] $ToolResults,
        [switch]$VenvOnly = $true,               # erzwinge venv-Scripts für Python-Tools
        [switch]$IncludeEmptyForMissing = $false,# Standard: KEINE leeren Platzhalter schreiben
        [switch]$AllowGlobalFallback = $false,   # falls venv-Tool fehlt: global erlauben?
        [string[]]$ExcludeKeys = @('tcl_base','msvc','cpp')  # niemals anfassen
    )

    $updates = @{}

    # Scripts-Verzeichnisse vorbereiten
    $baseScripts = Get-PyScriptsDir -PythonExe $PythonExe
    $userScripts = Get-PyUserScriptsDir -PythonExe $PythonExe
    $venvDirs    = @(); if ($baseScripts) { $venvDirs += $baseScripts }
    $allDirs     = @(); if ($baseScripts) { $allDirs += $baseScripts }
    if (-not $VenvOnly -and $userScripts) { $allDirs += $userScripts }

    $pyTools = @(
	    @{ key='pyinstaller';        execs=@('pyinstaller','pyinstaller3') }
        @{ key='cython';             execs=@('cython','cython3') },
        @{ key='nuitka';             execs=@('nuitka','nuitka3') },
        @{ key='pyarmor';            execs=@('pyarmor') },
        @{ key='pytest';             execs=@('pytest','py.test') },
        @{ key='sphinx-build';       execs=@('sphinx-build') },
        @{ key='sphinx-quickstart';  execs=@('sphinx-quickstart') }
    )

    foreach ($t in $pyTools) {
        foreach ($exe in $t.execs) {
            $path = $null

            if ($VenvOnly) {
                $path = Resolve-ToolPath-InDirs -Dirs $venvDirs -ExecName $exe
            } else {
                # 1) Basis + User-Scripts
                $path = Resolve-ToolPath-InDirs -Dirs $allDirs -ExecName $exe
				# 2) PATH
				if (-not $path -and $AllowGlobalFallback) {
					try {
						$cmd = Get-Command $exe -ErrorAction SilentlyContinue
						if ($cmd) { $path = $cmd.Path }
					} catch {}
				}
				# 3) where.exe
				if (-not $path -and $AllowGlobalFallback) {
					$path = Resolve-ByWhere -ExecName $exe
				}
            }

            if ($path) {
                if (-not $updates.ContainsKey($t.key)) { $updates[$t.key] = (Resolve-Path $path).Path }
                break
            }
        }

        if (-not $updates.ContainsKey($t.key) -and $IncludeEmptyForMissing) {
            $updates[$t.key] = ''
        }
    }

    # --- Externe Tools, die NICHT an Python-venv gebunden sind ---
    if (-not ($ExcludeKeys -contains 'cpp')) {
        $cppPath = $null
        try { $gppCmd = Get-Command g++ -ErrorAction SilentlyContinue; if ($gppCmd) { $cppPath = $gppCmd.Path } } catch {}
        if (-not $cppPath) { try { $clangppCmd = Get-Command clang++ -ErrorAction SilentlyContinue; if ($clangppCmd) { $cppPath = $clangppCmd.Path } } catch {} }
        if ($cppPath) { $updates['cpp'] = (Resolve-Path $cppPath).Path } elseif ($IncludeEmptyForMissing) { $updates['cpp'] = '' }
    }

    if (-not ($ExcludeKeys -contains 'msvc')) {
        try {
            $cl = Get-Command cl.exe -ErrorAction SilentlyContinue
            if ($cl -and (Test-Path $cl.Source)) { $updates['msvc'] = $cl.Source }
            elseif ($IncludeEmptyForMissing) { $updates['msvc'] = '' }
        } catch { if ($IncludeEmptyForMissing) { $updates['msvc'] = '' } }
    }

    if (-not ($ExcludeKeys -contains 'tcl_base')) {
        if ($env:TCL_LIBRARY -and (Test-Path $env:TCL_LIBRARY)) {
            $updates['tcl_base'] = (Resolve-Path $env:TCL_LIBRARY).Path
        } elseif ($IncludeEmptyForMissing) {
            $updates['tcl_base'] = ''
        }
    }

    # Finale Schutzmaßnahme: ausgeschlossenes entfernen
    foreach ($k in $ExcludeKeys) {
        if ($updates.ContainsKey($k)) { [void]$updates.Remove($k) }
    }

    return $updates
}


function Update-ExtensionsIniValues {
    param(
        [Parameter(Mandatory=$true)] [string]$IniPath,
        [Parameter(Mandatory=$true)] [hashtable]$NewValues,
        [switch]$DryRun = $false,
        [string[]]$ProtectedKeys = @('tcl_base','msvc','cpp','gcc') 
    )

    if (!(Test-Path $IniPath)) {
        Say-Err ("INI not found: {0}" -f $IniPath)
        return $false
    }

    # Schreib-Set vorab filtern: geschützte Keys gar nicht erst zulassen
    $writeSet = @{}
    foreach ($k in $NewValues.Keys) {
        if ($ProtectedKeys -and ($ProtectedKeys -contains $k)) { continue }
        $writeSet[$k] = [string]$NewValues[$k]
    }

    $nl   = "`r`n"
    $text = Get-Content -LiteralPath $IniPath -Raw -Encoding UTF8

    $rxHeader = [regex]'(?ms)^\s*\[\s*paths\s*\]\s*$'
    $m = $rxHeader.Matches($text)
    $hasPaths = $m.Count -gt 0

    if ($hasPaths) {
        # --- bestehenden [paths]-Block parsen ---
        $startIdx = $m[0].Index + $m[0].Length
        $after    = $text.Substring($startIdx)
        $m2       = [regex]::Match($after, '^\s*\[.+?\]\s*$', [System.Text.RegularExpressions.RegexOptions]::Multiline)
        $endIdx   = if ($m2.Success) { $startIdx + $m2.Index } else { $text.Length }

        $before   = $text.Substring(0, $startIdx)
        $block    = $text.Substring($startIdx, $endIdx - $startIdx)
        $afterAll = $text.Substring($endIdx)

        $existing = @{}
        foreach ($line in ($block -split "(`r`n|`n|`r)")) {
            if ($line -match '^\s*([^#;][^=]+?)\s*=\s*(.*)$') {
                $kk = $matches[1].Trim()
                $vv = $matches[2].Trim()
                $existing[$kk] = $vv
            }
        }

        # Merge OHNE geschützte Keys zu überschreiben
        foreach ($k in $writeSet.Keys) {
            if ($ProtectedKeys -and ($ProtectedKeys -contains $k)) { continue }  # doppelt sicher
            $existing[$k] = [string]$writeSet[$k]
        }

        $orderedKeys = ($existing.Keys | Sort-Object)

        $before   = $before.TrimEnd("`r","`n") + "`r`n"
        $newBlock = ""
        foreach ($k in $orderedKeys) {
            $val = $existing[$k]
            $newBlock += ("{0} = {1}`r`n" -f $k, $val)
        }

        if ($DryRun) {
            Say-Ok ("INI DryRun: {0} keys would be written." -f $orderedKeys.Count)
            foreach ($k in $orderedKeys) { Say-Info (" - {0}" -f $k) }
            return $true
        }

        try { Copy-Item -LiteralPath $IniPath -Destination ($IniPath + ".bak") -Force -ErrorAction Stop; Say-Info ("Backup created: {0}" -f ($IniPath + ".bak")) } catch {}

        $final = $before + $newBlock + $afterAll
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($IniPath, $final, $utf8NoBom)

        Say-Ok ("Update extensions_path.ini: {0} (Keys: {1})" -f $IniPath, $orderedKeys.Count)
        return $true
    }
    else {
        # Kein [paths]-Block vorhanden -> nur NICHT-geschützte Keys schreiben
        $orderedKeys = ($writeSet.Keys | Sort-Object)

        if ($DryRun) {
            Say-Ok "[paths] section would be created."
            foreach ($k in $orderedKeys) { Say-Info (" - {0}" -f $k) }
            return $true
        }

        try { Copy-Item -LiteralPath $IniPath -Destination ($IniPath + ".bak") -Force -ErrorAction Stop; Say-Info ("Backup created: {0}" -f ($IniPath + ".bak")) } catch {}

        $append = $nl + "[paths]" + $nl
        foreach ($k in $orderedKeys) {
            $append += ("{0} = {1}{2}" -f $k, $writeSet[$k], $nl)
        }

        $final = $text.TrimEnd() + $nl + $append
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($IniPath, $final, $utf8NoBom)

        Say-Ok ("Create [paths] in extensions_path.ini: {0} (Keys: {1})" -f $IniPath, $orderedKeys.Count)
        return $true
    }
}


if ($UpdateIni) {
    $iniPath = Get-ExtensionsIniPath -ExplicitIniPath $extensionsPath
    if ($iniPath) {
        Say-Section 'Update extensions_path.ini'
        Show-Item -Name 'INI' -Value $iniPath

        $allowGlobal = -not $usedVenv
        $upd = Build-IniUpdatesFromEnv `
            -PythonExe $pythonPath `
            -ToolResults $global:toolResults `
            -VenvOnly:$usedVenv `
            -AllowGlobalFallback:$allowGlobal `
            -IncludeEmptyForMissing:$false `
            -ExcludeKeys $ProtectedKeys 

        if ($upd.Count -eq 0) {
            Say-Warn 'No new paths found — check PATH and selected Python env.'
        } else {
            foreach ($kv in $upd.GetEnumerator()) {
                Show-Item -Name $kv.Key -Value $kv.Value
            }
            [void](Update-ExtensionsIniValues -IniPath $iniPath -NewValues $upd -DryRun:$IniDryRun -ProtectedKeys $ProtectedKeys)  # <-- Guard aktiv
        }

    } else {
        Say-Warn 'extensions_path.ini not found'
    }
}

# ============================ venv Info ================================
if ($usedVenv) {
    Say-Section "Isolated Environment Info"
    Write-Host ("venv python : {0}" -f $pythonPath)
    Write-Host ("venv scripts: {0}" -f (Get-PyScriptsDir -PythonExe $pythonPath))
}

# ============================ Launch AutoPy++ ==========================
if (!(Test-Path $srcDir)) { Say-Err 'Folder not found: {0}' -f $srcDir; exit 1 }
Say-Section ('Launching AutoPyPlusPlus with: {0}' -f $pythonPath)
Set-Location -Path $srcDir
& $pythonPath -m AutoPyPlusPlus
exit $LASTEXITCODE
