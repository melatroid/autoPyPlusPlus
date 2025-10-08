

# windows_update.ps1
$ErrorActionPreference = 'Stop'

# Settings
$DEFAULT_REMOTE = "https://github.com/melatroid/autoPyPlusPlus.git"

$global:BackupMode = 1

# --- ASCII art header ---
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


# Resolve repo root relative to this script (../ from /src)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $here '..') -ErrorAction SilentlyContinue
if (-not $repoRoot) {
  Write-Host '[Error] Repo root not found (expected .. from /src)' -ForegroundColor Red
  exit 1
}
Set-Location $repoRoot

function Ensure-Git {
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host '[Error] Git not found. Install: winget install --id Git.Git -e' -ForegroundColor Red
    exit 1
  }
}

function Is-GitRepo {
  try { (git rev-parse --is-inside-work-tree 2>$null).Trim() -eq 'true' } catch { $false }
}

function Detect-DefaultBranch {
  $h = (& git symbolic-ref --short refs/remotes/origin/HEAD 2>$null)
  if ($h) { return $h.Split('/')[-1] }
  $l = (git remote show origin | Select-String -Pattern 'HEAD branch:' -ErrorAction SilentlyContinue)
  if ($l) { return $l.ToString().Split(':')[-1].Trim() }
  return 'main'
}

function Ensure-Repo-And-Remote {
  Ensure-Git
  if (-not (Is-GitRepo)) {
    Write-Host '[Error] This folder is not a Git repository. Run ''Create'' first.' -ForegroundColor Red
    return $false
  }
  if (-not (& git remote get-url origin 2>$null)) {
    Write-Host '[Error] No ''origin'' remote configured. Run ''Create'' first.' -ForegroundColor Red
    return $false
  }
  return $true
}

# --- Backup helpers ---
function Ensure-BackupsDir {
  param([string]$Root)
  $dir = Join-Path $Root 'backups'
  if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir | Out-Null
  }
  return $dir
}

function New-RepoBackup {
  <#
    Erstellt ein Backup des Repos (ohne .git & ohne backups).
    Respektiert $global:BackupMode:
      0 = kein Backup
      1 = Ordner-Backup
      2 = ZIP-Backup (Ordner wird nach dem Zip gelöscht)
    Return: Pfad zum Backup (Ordner oder ZIP) oder $null, wenn Modus=0
  #>
  param(
    [string]$Root,
    [switch]$VerboseLog
  )

  switch ($global:BackupMode) {
    0 {
      Write-Host '[Backup] Mode OFF – kein Backup erstellt.' -ForegroundColor DarkGray
      return $null
    }
    default {
      $backupsRoot = Ensure-BackupsDir -Root $Root
      $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
      $dest = Join-Path $backupsRoot $stamp

      Write-Host "Creating backup at: $dest"
      New-Item -ItemType Directory -Path $dest | Out-Null

      # Robocopy spiegelt alles außer .git und backups (damit keine Rekursion).
      # /MIR: Mirror, /XJ: Ausschließen von Verzeichnis-Junctions
      # /R:1 /W:1: wenig Wiederholungen/Wartezeit, /NFL /NDL /NP: weniger Lärm
      $flags = @('/MIR','/XD','.git','backups','/XJ','/R:1','/W:1','/NFL','/NDL','/NP')
      if ($VerboseLog) { $flags = @('/MIR','/XD','.git','backups','/XJ','/R:1','/W:1') }

      $null = & robocopy $Root $dest @flags
      $exitCode = $LASTEXITCODE

      # Robocopy Rückgabecodes: 0..7 = Erfolg/kleine Abweichungen
      if ($exitCode -le 7) {
        if ($global:BackupMode -eq 1) {
          Write-Host "Backup created successfully at: $dest" -ForegroundColor Green
          return $dest
        } else {
          # ZIP-Backup
          $zipPath = "$dest.zip"
          Write-Host "Compressing backup to: $zipPath"
          Compress-Archive -Path (Join-Path $dest '*') -DestinationPath $zipPath -CompressionLevel Optimal
          # Ordner nach erfolgreichem Zip löschen
          Remove-Item -Recurse -Force $dest
          Write-Host "ZIP backup ready: $zipPath" -ForegroundColor Green
          return $zipPath
        }
      } else {
        Write-Host "[Warning] Backup may have failed (robocopy code $exitCode). Update aborted." -ForegroundColor Yellow
        throw "Backup failed with robocopy exit code $exitCode"
      }
    }
  }
}

function Get-BackupModeLabel {
  switch ($global:BackupMode) {
    0 { return 'OFF' }
    1 { return 'FOLDER' }
    2 { return 'ZIP' }
    default { return 'UNKNOWN' }
  }
}

# --- Create ---
function Op-Create {
  Write-Host '== CREATE (initialize & attach to GitHub) =='
  Ensure-Git

  if (-not (Is-GitRepo)) {
    Write-Host 'Initializing repository...'
    git init | Out-Null
  } else {
    Write-Host 'Repository detected.'
  }

  $existing = (& git remote get-url origin 2>$null)
  if ($existing) {
    Write-Host "Remote 'origin' already set: $existing"
  } else {
    Write-Host "Setting remote 'origin' to $DEFAULT_REMOTE"
    git remote add origin $DEFAULT_REMOTE
  }

  Write-Host 'Fetching from origin...'
  git fetch origin --prune

  $head = Detect-DefaultBranch
  Write-Host "Default branch: $head"
  Write-Host "Checking out '$head' and aligning to origin/$head (overwrites local files)..."
  git checkout -B $head
  git reset --hard ("origin/" + $head)

  Write-Host 'Updating submodules (if any)...'
  git submodule update --init --recursive

  Write-Host 'CREATE finished.'
}

# --- Updates (3 Varianten) ---

# [1] Safe: Fast-Forward only
function Op-Update-FFOnly {
  if (-not (Ensure-Repo-And-Remote)) { return }
  # Backup vor Update gemäß Modus
  New-RepoBackup -Root $repoRoot | Out-Null

  Write-Host '== UPDATE (pull latest, fast-forward only) =='
  Write-Host '[1/4] Fetch --all --prune'
  git fetch --all --prune
  $head = Detect-DefaultBranch
  Write-Host "[2/4] Checkout '$head'"
  git checkout $head
  Write-Host '[3/4] Pull --ff-only'
  git pull --ff-only
  Write-Host '[4/4] Submodules update --init --recursive'
  git submodule update --init --recursive
  Write-Host 'UPDATE (FF-only) finished.'
}

# [2] Hard-Reset: exakt wie Remote
function Op-Update-HardReset {
  if (-not (Ensure-Repo-And-Remote)) { return }
  # Backup vor Update gemäß Modus
  New-RepoBackup -Root $repoRoot | Out-Null

  Write-Host '== UPDATE (HARD RESET to origin/<default>) =='
  Write-Host '[1/3] Fetch --all --prune --tags --prune-tags'
  git fetch --all --prune --tags --prune-tags
  $head = Detect-DefaultBranch
  Write-Host "[2/3] Checkout '$head'"
  git checkout -B $head
  Write-Host "[3/3] Reset --hard origin/$head  (local changes will be LOST!)" -ForegroundColor Yellow
  git reset --hard ("origin/" + $head)
  Write-Host '[Submodules] update --init --recursive --force'
  git submodule sync --recursive
  git submodule update --init --recursive --force
  Write-Host 'UPDATE (Hard-Reset) finished.'
}

# [3] Rebase: lokale Commits oben drauf behalten
function Op-Update-Rebase {
  if (-not (Ensure-Repo-And-Remote)) { return }
  # Backup vor Update gemäß Modus
  New-RepoBackup -Root $repoRoot | Out-Null

  Write-Host '== UPDATE (pull --rebase) =='
  Write-Host '[1/4] Fetch --all --prune'
  git fetch --all --prune
  $head = Detect-DefaultBranch
  Write-Host "[2/4] Checkout '$head'"
  git checkout $head
  Write-Host '[3/4] Pull --rebase'
  git pull --rebase
  Write-Host '[4/4] Submodules update --init --recursive'
  git submodule update --init --recursive
  Write-Host 'UPDATE (Rebase) finished.'
}

# --- Menu helpers ---
function Toggle-BackupMode {
  Write-Host "Current backup mode: $(Get-BackupModeLabel)" -ForegroundColor Cyan
  Write-Host '[1] OFF'
  Write-Host '[2] FOLDER'
  Write-Host '[3] ZIP'
  $sel = Read-Host 'Select backup mode'
  switch ($sel) {
    '1' { $global:BackupMode = 0 }
    '2' { $global:BackupMode = 1 }
    '3' { $global:BackupMode = 2 }
    default { Write-Host 'No change.' }
  }
  Write-Host "Backup mode is now: $(Get-BackupModeLabel)" -ForegroundColor Green
  Read-Host 'Press ENTER to continue' | Out-Null
}

# --- Menu loop ---
while ($true) {
  Clear-Host
  Write-Host '##################################################################################################' -ForegroundColor Blue
  Write-Host '##################################################################################################' -ForegroundColor Cyan
  Write-Host '##################################################################################################' -ForegroundColor Blue
  Write-Host $art -ForegroundColor Yellow

  $backupLabel = Get-BackupModeLabel
  Write-Host '##################################################################################################' -ForegroundColor Blue
  Write-Host '################################## AutoPy++ - Update Menu ########################################' -ForegroundColor Cyan
  Write-Host '##################################################################################################' -ForegroundColor Blue
  Write-Host "Repo: $repoRoot" -ForegroundColor DarkGray
  Write-Host "Backup Mode: $backupLabel" -ForegroundColor DarkYellow
  Write-Host '-----------------------------------------------'
  Write-Host '[1] Update (Safe: Fast-Forward only)'
  Write-Host '[2] Update (Hard-Reset to origin/<default>)'
  Write-Host '[3] Update (Rebase local commits)'
  Write-Host '[4] Backup Mode (OFF/FOLDER/ZIP)'
  Write-Host '[9] Create (initialize & attach to GitHub)'
  Write-Host '[0] Exit'
  Write-Host '-----------------------------------------------'
  $choice = Read-Host 'Select'

  switch ($choice) {
    '1' { Op-Update-FFOnly;     Read-Host 'Press ENTER to continue' | Out-Null }
    '2' { Op-Update-HardReset;  Read-Host 'Press ENTER to continue' | Out-Null }
    '3' { Op-Update-Rebase;     Read-Host 'Press ENTER to continue' | Out-Null }
    '4' { Toggle-BackupMode }
    '9' { Op-Create;            Read-Host 'Press ENTER to continue' | Out-Null }
    '0' { break }
    default { Write-Host 'Invalid choice.'; Start-Sleep -Milliseconds 900 }
  }
}

Write-Host 'Bye!'
