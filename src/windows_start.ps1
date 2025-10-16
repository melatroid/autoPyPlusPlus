# Run-AutoPyPlusPlus.ps1
# -----------------------------------------------------------------------------
# Optional venv:
# - Erst werden (mit 5s Timeout) vorhandene Python-Installationen angezeigt.
# - Taste [V] (oder [N]) = Neues, isoliertes Environment anlegen (pyenv-win/winget).
# - Keine Eingabe -> nach 5s wird der Default (bestehende Installation) gewählt.
# - Fehlende Build-/Tool-Pakete werden IMMER in das gewählte/erstellte Environment
#   installiert (nie in den Skript-Ordner).
# - Am Ende werden die Pfade ("where") der Tools (Modul/Exec) ausgegeben.
# -----------------------------------------------------------------------------

$art = @'
            /^\/^\                                   /^\/^\
         __|__|o |                                 _|_o|  o|
\/     /~     \_/ \                              /~     \_/ \
 \____|__________/  \                           |__________/ \
        \_______      \                         \_______      \
                `\     \                 \               \     \                   \
                  |     |                  \             |     |                     \
                 /      /                    \\          /     /                      \\
                /     /                       \\        /     /                        \ \
              /      /                         \ \      /     /                         \  \
             /     /                            \  \   /     /                           \  \
           /     /             _----_            \   \ /     /             _----_         \   \
          /     /           _-~      ~-_         |   |/     /           _-~      ~-_      |    |
         (      (        _-~    _--_    ~-_     _/   (      (        _-~    _--_    ~-_ _/     |
          \      ~-____-~    _-~    ~-_    ~-_-~    / \      ~-____-~    _-~    ~-_    ~-_-~   /
            ~-_           _-~          ~-_       _-~   ~-_           _-~          ~-_       _-~
               ~--______-~                ~-___-~         ~--______-~                ~-___-~
'@
Write-Host $art -ForegroundColor Blue

# ============================ Configuration ============================
#   EDIT THIS !!!!
$defaultPythonPath     = 'C:\Users\melatroid\AppData\Local\Programs\Python\Python310\python.exe'    # default python version that is used
$srcDir                = 'C:\Users\melatroid\Desktop\autoPy++\AutoPyPlusPlus\src'  # autopy++ src path

#========================================================
#   EDIT THIS NOT!!!!
$desiredPythonVersion  = '3.10.11'            # "3.10" oder "3.10.11"
$expectedMinor         = '3.10' 			  # Needet Version
$venvRoot              = "$env:LOCALAPPDATA\AutoPyPP\envs"											# default env folder
$venvName              = "autopypp-Env-$($desiredPythonVersion -replace '\.','_')"					# default env name
$allowInstallPython    = $true  #Install Python
$autoInstallMissing    = $true  #Install missing Extensions
$enforceToolPresence   = $false 
$enforceMinor          = $false # Force Incompatibel
# ============================ Helpers: Console =========================
function Read-LineWithTimeout {
    param([int]$Seconds = 5)
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

# ============================ Helpers: Python Install ==================
function Test-WingetAvailable { try { Get-Command winget -ErrorAction Stop | Out-Null; $true } catch { $false } }

function Ensure-PyenvWin {
    $root = Join-Path $env:USERPROFILE ".pyenv\pyenv-win"
    if (Test-Path $root) { return $true }
    Write-Host "Installing pyenv-win (per-user)..." -ForegroundColor Cyan
    try {
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://pyenv-win.github.io/pyenv-win/install.ps1'))
        $pyenvBin = Join-Path $env:USERPROFILE ".pyenv\pyenv-win\bin"
        $pyenvShm = Join-Path $env:USERPROFILE ".pyenv\pyenv-win\shims"
        $env:Path = "$pyenvBin;$pyenvShm;$env:Path"
        return $true
    } catch {
        Write-Host "pyenv-win installation failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
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
    Write-Host "Installing Python $Version via pyenv-win..." -ForegroundColor Cyan
    try { pyenv install -q $Version; return $true } catch { Write-Host "pyenv install failed: $($_.Exception.Message)" -ForegroundColor Red; return $false }
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
    if (-not $pkgId) { Write-Host "winget: no mapping for Python $Minor" -ForegroundColor Yellow; return $false }
    Write-Host "Installing Python $Minor via winget ($pkgId)..." -ForegroundColor Cyan
    try { winget install --id $pkgId --silent --accept-source-agreements --accept-package-agreements; return $true }
    catch { Write-Host "winget install failed." -ForegroundColor Red; return $false }
}

function Ensure-Python-Version {
    param([string]$Desired) # "3.10.11" oder "3.10"
    if ($Desired -match '^\d+\.\d+\.\d+$') {
        if (Install-Python-WithPyenv -Version $Desired) {
            $pp = Find-PyenvPythonPath -Version $Desired
            if ($pp) { return $pp }
        }
    } else {
        if (Install-Python-WithPyenv -Version $Desired) {
            # pyenv installiert neueste Patch; suche Pfad
            try {
                $vers = (pyenv versions) -join "`n"
                $m = [regex]::Matches($vers, '(\d+\.\d+\.\d+)')
                if ($m.Success) {
                    $patch = ($m.Value | Where-Object { $_ -like "$Desired.*" } | Sort-Object {[version]$_} -Descending | Select-Object -First 1)
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
        Write-Host "pip not found - bootstrapping via ensurepip..." -ForegroundColor Yellow
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
    Write-Host "Creating venv: $venvPath" -ForegroundColor Cyan
    & $BasePythonExe -m venv $venvPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) { Write-Host "Failed to create venv." -ForegroundColor Red; return $null }
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
    # auch pyenv-win-Installationen anzeigen
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

function Choose-Existing-Or-Venv {
    param([array]$candidates, [string]$defaultPath)
    if (-not $candidates -or $candidates.Count -eq 0) {
        Write-Host "No existing Pythons found. Press [Enter] to attempt venv creation..." -ForegroundColor Yellow
        return [pscustomobject]@{ Mode='venv'; PythonPath=$null; DesiredVersion=$null }
    }

    Write-Host ""
    Write-Host "=== Available Python installations ===" -ForegroundColor Cyan
    $i = 1
    foreach ($c in $candidates) {
        $tagDefault = if ($c.IsDefault) { " *" } else { "" }
        $bitsLabel  = if ($c.Bits) { " ($($c.Bits)-bit)" } else { "" }
        Write-Host ("[{0}] Python {1}{2}  -> {3}{4}" -f $i, $c.Version, $bitsLabel, $c.Path, $tagDefault)
        $i++
    }
    Write-Host "[V] Create new isolated environment (pyenv/winget + venv)"
    Write-Host "[X] Cancel`n"

    $defaultCandidatePath = if ($defaultPath -and (Test-Path $defaultPath)) { $defaultPath } else { $candidates[0].Path }

    Write-Host ("Press a number, paste a full path to python.exe,")
    Write-Host ("or press [V] to create a new isolated venv.")
    Write-Host ("Auto-select in 5s: {0}" -f $defaultCandidatePath) -ForegroundColor Yellow
    Write-Host -NoNewline "> "

    $choice = Read-LineWithTimeout -Seconds 5
    Write-Host ""

    if ([string]::IsNullOrWhiteSpace($choice)) {
        return [pscustomobject]@{ Mode='existing'; PythonPath=$defaultCandidatePath; DesiredVersion=$null }
    }

    if ($choice -match '^[Xx]$') { return $null }
	if ($choice -match '^[VvNn]$') {
		Write-Host ("Enter desired Python version (e.g. 3.10 or 3.10.11). Default in 10s: {0}" -f $desiredPythonVersion) -ForegroundColor Yellow
		Write-Host -NoNewline "> "
		$verChoice = Read-LineWithTimeout -Seconds 10
		Write-Host ""
		if ([string]::IsNullOrWhiteSpace($verChoice)) { $verChoice = $desiredPythonVersion }
		return [pscustomobject]@{ Mode='venv'; PythonPath=$null; DesiredVersion=$verChoice }
	}
    $idx = 0
    if ([int]::TryParse($choice, [ref]$idx)) {
        if ($idx -ge 1 -and $idx -le $candidates.Count) {
            return [pscustomobject]@{ Mode='existing'; PythonPath=$candidates[$idx-1].Path; DesiredVersion=$null }
        } else {
            Write-Warning "Invalid selection."; return $null
        }
    }

    $norm = $choice.Trim('"', "'"); $norm = $norm -replace '/', '\'
    if ($norm -match '(?i)python\.exe$' -and (Test-Path $norm)) {
        return [pscustomobject]@{ Mode='existing'; PythonPath=$norm; DesiredVersion=$null }
    }

    Write-Warning "Please enter a valid number, 'V' for venv, or an existing path to python.exe."
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

function Get-PyModuleVersion { param([string]$PythonExe,[string]$Module,[string]$Regex,[string]$AltModule)
    try { $raw=& $PythonExe -m $Module --version 2>$null; if($LASTEXITCODE -eq 0 -and $raw){$m=[regex]::Match($raw,$Regex); if($m.Success){return $m.Groups['v'].Value.Trim()}} } catch {}
    if($AltModule){ try { $raw=& $PythonExe -m $AltModule --version 2>$null; if($LASTEXITCODE -eq 0 -and $raw){$m=[regex]::Match($raw,$Regex); if($m.Success){return $m.Groups['v'].Value.Trim()}} } catch {} }
    try {$py=@"
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
"@; $out=& $PythonExe -c $py 2>$null; if($out -and $out.Trim().Length -gt 0){return $out.Trim()} } catch {}
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

function Resolve-ExecPath { param([string]$PythonExe,[string]$ExecName)
    try { $cmd = Get-Command $ExecName -ErrorAction SilentlyContinue } catch { $cmd=$null }
    if ($cmd) { return $cmd.Path }
    $scripts = Get-PyScriptsDir -PythonExe $PythonExe
    if ($scripts) {
        $c1 = Join-Path $scripts ($ExecName + '.exe'); if (Test-Path $c1) { return $c1 }
        $c2 = Join-Path $scripts ($ExecName); if (Test-Path $c2) { return $c2 }
    }
    return $null
}

$tools = @(
    @{ Name='PyArmor'; Dist='pyarmor'; Module='pyarmor'; AltModule='pyarmor.cli'; Pkg='pyarmor>=9.1.6'; Regex='(?i)(?<v>\d+(\.\d+){1,3})'; Exec='pyarmor' },
    @{ Name='Nuitka';  Dist='nuitka';  Module='nuitka';  AltModule=$null;          Pkg='nuitka';         Regex='(?i)(?<v>\d+(\.\d+){1,3})'; Exec='nuitka' },
    @{ Name='Cython';  Dist='Cython';  Module='Cython';  AltModule=$null;          Pkg='cython';         Regex='(?i)(?<v>\d+(\.\d+){1,3})'; Exec='cython' },
    @{ Name='Pytest';  Dist='pytest';  Module='pytest';  AltModule=$null;          Pkg='pytest';         Regex='(?i)pytest\s+(?<v>\d+(\.\d+){1,3})'; Exec='pytest' },
    @{ Name='Sphinx';  Dist='Sphinx';  Module='sphinx';  AltModule=$null;          Pkg='sphinx';         Regex='(?i)(sphinx\s+)?(?<v>\d+(\.\d+){1,3})'; Exec='sphinx-build' }
)

$global:toolResults = @()

function Show-ToolStatus {
    param([string]$Header, [string]$PythonExe)
    Write-Host ("`n=== {0} ===" -f $Header) -ForegroundColor Cyan
    $missing = @(); $results=@()
    foreach ($t in $tools) {
        $ver = Get-PyDistVersion -PythonExe $PythonExe -DistName $t.Dist
        if (-not $ver) { $ver = Get-PyModuleVersion -PythonExe $PythonExe -Module $t.Module -Regex $t.Regex -AltModule $t.AltModule }
        if ($ver) {
            Write-Host ("{0,-8}: found  v{1}" -f $t.Name, $ver)
            $modPath  = Get-PyModulePath -PythonExe $PythonExe -Module $t.Module
            $execPath = if ($t.Exec) { Resolve-ExecPath -PythonExe $PythonExe -ExecName $t.Exec } else { $null }
            $results += [pscustomobject]@{ Name=$t.Name; Version=$ver; ModulePath=$modPath; ExecPath=$execPath }
        } else {
            Write-Host ("{0,-8}: NOT FOUND" -f $t.Name) -ForegroundColor Yellow
            $missing += $t
        }
    }
    $global:toolResults = $results
    return ,$missing
}

# ============================ Auswahl: bestehend ODER venv =============
$candidates = Get-PythonCandidates -expectedMinor $expectedMinor
$selection  = Choose-Existing-Or-Venv -candidates $candidates -defaultPath $defaultPythonPath
if (-not $selection) { Write-Host "Cancelled." -ForegroundColor Yellow; exit 1 }

$pythonPath = $null
$usedVenv   = $false

if ($selection.Mode -eq 'existing') {
    $pythonPath = $selection.PythonPath
    Ensure-Pip -PythonExe $pythonPath
} elseif ($selection.Mode -eq 'venv') {
    $usedVenv = $true
    $want = $selection.DesiredVersion
    if ([string]::IsNullOrWhiteSpace($want)) { $want = $desiredPythonVersion }
    $basePy = $null

    # Prüfe, ob gewünschte Version bereits vorhanden ist
    $already = Get-PythonCandidates -expectedMinor ''
    $basePy = ($already | Where-Object {
        if ($want -match '^\d+\.\d+\.\d+$') { $_.Path -and (& $_.Path -c "import sys; print('.'.join(map(str,sys.version_info[:3])))") -eq $want }
        else { $_.Version -eq ($want -replace '^(\d+\.\d+).*','$1') }
    } | Select-Object -First 1).Path

    if (-not $basePy -and $allowInstallPython) {
        $basePy = Ensure-Python-Version -Desired $want
    }
    if (-not $basePy) {
        Write-Host "Could not find or install Python $want." -ForegroundColor Red
        exit 10
    }

    $venvName = "autopypp-$($want -replace '\.','_')"
    $pythonPath = New-IsolatedVenv -BasePythonExe $basePy -VenvRoot $venvRoot -VenvName $venvName
    if (-not $pythonPath) { exit 11 }
    Ensure-Pip -PythonExe $pythonPath
}

if (!(Test-Path $srcDir)) { Write-Error "Folder not found: $srcDir"; exit 1 }

# ============================ Diagnostics ==============================
Write-Host "`n=== Python/AutoPy++ Diagnostic ===" -ForegroundColor Cyan
& $pythonPath --version
$pyMajMin  = & $pythonPath -c "import sys; print('%d.%d' % (sys.version_info[0], sys.version_info[1]))"
$pyPatch   = & $pythonPath -c "import sys; print(sys.version_info[2])"
$pyverFull = & $pythonPath -c "import sys; print(sys.version.replace('\n',' '))"
Write-Host ("Selected Python: {0}.{1}  (full: {2})" -f $pyMajMin, $pyPatch, $pyverFull)

if ($expectedMinor -and ($pyMajMin -ne $expectedMinor)) {
    Write-Warning ("Preferred minor is {0}, but you selected {1}.{2}. Continuing..." -f $expectedMinor, $pyMajMin, $pyPatch)
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
Write-Host "`n=== PyArmor Compatibility Recommendation ===" -ForegroundColor Cyan
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
    Write-Host "Supported by PyArmor: NO" -ForegroundColor Red
    Write-Host ("Recommendation: {0}" -f $pyarmorRecommendation)
    Write-Host "Aborting due to missing PyArmor support." -ForegroundColor Red
    exit 2
} else {
    Write-Host "Supported by PyArmor: YES" -ForegroundColor Green
    Write-Host ("Recommendation: {0}" -f $pyarmorRecommendation)
}

Write-Host "Version matrix:"
Write-Host " - Python 3.7 - 3.11  -> PyArmor 8.x or 9.x"
Write-Host " - Python 3.12 - 3.13 -> PyArmor 9.x (>= 9.1.6 preferred)"
Write-Host " - Other versions     -> Not supported by PyArmor"

# ============================ Tools: install & where ===================
$missing = Show-ToolStatus -Header "Tool Presence (selected Python env)" -PythonExe $pythonPath
if ($missing.Count -gt 0 -and $autoInstallMissing) {
    Write-Host "`nInstalling missing tools into the selected Python environment..." -ForegroundColor Cyan
    foreach ($t in $missing) {
        try {
            Write-Host ("pip install {0}" -f $t.Pkg)
            & $pythonPath -m pip install --disable-pip-version-check $t.Pkg
        } catch {
            Write-Host ("Install failed for {0}" -f $t.Name) -ForegroundColor Red
        }
    }
    $missing = Show-ToolStatus -Header "Tool Presence (re-check)" -PythonExe $pythonPath
}

if ($missing.Count -gt 0) {
    $names = ($missing | ForEach-Object { $_.Name }) -join ', '
    Write-Host ("Missing: {0}" -f $names) -ForegroundColor Yellow
    if ($enforceToolPresence) {
        Write-Host "Aborting because required tools are missing." -ForegroundColor Red
        exit 3
    } else {
        Write-Host "Note: continuing despite missing tools (set `$enforceToolPresence = `$true to abort)." -ForegroundColor DarkYellow
    }
} else {
    Write-Host "All tools present." -ForegroundColor Green
}

# Ausgabe der Ablageorte ("where")
if ($global:toolResults.Count -gt 0) {
    Write-Host "`n=== Tool Locations (selected Python env) ===" -ForegroundColor Cyan
    foreach ($r in $global:toolResults) {
        Write-Host ("{0,-8}: v{1}" -f $r.Name, $r.Version)
        if ($r.ModulePath) { Write-Host ("  module: {0}" -f $r.ModulePath) }
        if ($r.ExecPath)   { Write-Host ("  exec  : {0}" -f $r.ExecPath) }
    }
}

if ($usedVenv) {
    Write-Host "`n=== Isolated Environment Info ===" -ForegroundColor Cyan
    Write-Host ("venv python : {0}" -f $pythonPath)
    Write-Host ("venv scripts: {0}" -f (Get-PyScriptsDir -PythonExe $pythonPath))
}

# ============================ Launch AutoPy++ ==========================
if (!(Test-Path $srcDir)) { Write-Error "Folder not found: $srcDir"; exit 1 }
Write-Host ("`n=== Launching AutoPyPlusPlus with: {0} ===" -f $pythonPath) -ForegroundColor Cyan
Set-Location -Path $srcDir
& $pythonPath -m AutoPyPlusPlus
exit $LASTEXITCODE
