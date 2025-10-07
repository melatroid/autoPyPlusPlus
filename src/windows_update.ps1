# windows_update.ps1
$ErrorActionPreference = 'Stop'

# Settings
$DEFAULT_REMOTE = "https://github.com/melatroid/autoPyPlusPlus.git"

# --- ASCII art header ---
$art = @'
           /^\/^\                                   /^\/^\
         _|__|  O|                                _|_O|  O|
\/     /~     \_/ \                              /~     \_/ \
 \____|__________/  \                           |__________/ \
        \_______      \                         \_______      \
                `\     \                 \         `     \     \                 \
                  |     |                  \             |     |                   \
                 /      /                    \           /      /                    \
                /     /                       \\        /     /                       \ \
              /      /                         \ \      /     /                         \  \
             /     /                            \  \   /     /                            \  \
           /     /             _----_            \   \ /     /             _----_         \   \
          /     /           _-~      ~-_         |   |/     /           _-~      ~-_      |    |
         (      (        _-~    _--_    ~-_     _/   (      (        _-~    _--_    ~-_ _/     |
          \      ~-____-~    _-~    ~-_    ~-_-~    / \      ~-____-~    _-~    ~-_    ~-_-~   /
            ~-_           _-~          ~-_       _-~   ~-_           _-~          ~-_       _-~
               ~--______-~                ~-___-~         ~--______-~                ~-___-~
'@

# Resolve repo root relative to this script (../ from /src)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $here "..") -ErrorAction SilentlyContinue
if (-not $repoRoot) {
  Write-Host "[Error] Repo root not found (expected .. from /src)" -ForegroundColor Red
  exit 1
}
Set-Location $repoRoot

function Ensure-Git {
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] Git not found. Install: winget install --id Git.Git -e" -ForegroundColor Red
    exit 1
  }
}

function Is-GitRepo {
  try { (git rev-parse --is-inside-work-tree 2>$null).Trim() -eq 'true' } catch { $false }
}

function Detect-DefaultBranch {
  $h = (& git symbolic-ref --short refs/remotes/origin/HEAD 2>$null)
  if ($h) { return $h.Split('/')[-1] }
  $l = (git remote show origin | Select-String -Pattern "HEAD branch:" -ErrorAction SilentlyContinue)
  if ($l) { return $l.ToString().Split(":")[-1].Trim() }
  return 'main'
}

function Ensure-Repo-And-Remote {
  Ensure-Git
  if (-not (Is-GitRepo)) {
    Write-Host "[Error] This folder is not a Git repository. Run 'Create' first." -ForegroundColor Red
    return $false
  }
  if (-not (& git remote get-url origin 2>$null)) {
    Write-Host "[Error] No 'origin' remote configured. Run 'Create' first." -ForegroundColor Red
    return $false
  }
  return $true
}

# --- Create ---
function Op-Create {
  Write-Host "== CREATE (initialize `& attach to GitHub) =="
  Ensure-Git

  if (-not (Is-GitRepo)) {
    Write-Host "Initializing repository..."
    git init | Out-Null
  } else {
    Write-Host "Repository detected."
  }

  $existing = (& git remote get-url origin 2>$null)
  if ($existing) {
    Write-Host "Remote 'origin' already set: $existing"
  } else {
    Write-Host "Setting remote 'origin' to $DEFAULT_REMOTE"
    git remote add origin $DEFAULT_REMOTE
  }

  Write-Host "Fetching from origin..."
  git fetch origin --prune

  $head = Detect-DefaultBranch
  Write-Host "Default branch: $head"
  Write-Host "Checking out '$head' and aligning to origin/$head (overwrites local files)..."
  git checkout -B $head
  git reset --hard ("origin/" + $head)

  Write-Host "Updating submodules (if any)..."
  git submodule update --init --recursive

  Write-Host "CREATE finished."
}

# --- Updates (3 Varianten) ---

# [1] Safe: Fast-Forward only
function Op-Update-FFOnly {
  if (-not (Ensure-Repo-And-Remote)) { return }
  Write-Host "== UPDATE (pull latest, fast-forward only) =="
  Write-Host "[1/4] Fetch --all --prune"
  git fetch --all --prune
  $head = Detect-DefaultBranch
  Write-Host "[2/4] Checkout '$head'"
  git checkout $head
  Write-Host "[3/4] Pull --ff-only"
  git pull --ff-only
  Write-Host "[4/4] Submodules update --init --recursive"
  git submodule update --init --recursive
  Write-Host "UPDATE (FF-only) finished."
}

# [2] Hard-Reset: exakt wie Remote
function Op-Update-HardReset {
  if (-not (Ensure-Repo-And-Remote)) { return }
  Write-Host "== UPDATE (HARD RESET to origin/<default>) =="
  Write-Host "[1/3] Fetch --all --prune --tags --prune-tags"
  git fetch --all --prune --tags --prune-tags
  $head = Detect-DefaultBranch
  Write-Host "[2/3] Checkout '$head'"
  git checkout -B $head
  Write-Host "[3/3] Reset --hard origin/$head  (local changes will be LOST!)" -ForegroundColor Yellow
  git reset --hard ("origin/" + $head)
  Write-Host "[Submodules] update --init --recursive --force"
  git submodule sync --recursive
  git submodule update --init --recursive --force
  Write-Host "UPDATE (Hard-Reset) finished."
}

# [3] Rebase: lokale Commits oben drauf behalten
function Op-Update-Rebase {
  if (-not (Ensure-Repo-And-Remote)) { return }
  Write-Host "== UPDATE (pull --rebase) =="
  Write-Host "[1/4] Fetch --all --prune"
  git fetch --all --prune
  $head = Detect-DefaultBranch
  Write-Host "[2/4] Checkout '$head'"
  git checkout $head
  Write-Host "[3/4] Pull --rebase"
  git pull --rebase
  Write-Host "[4/4] Submodules update --init --recursive"
  git submodule update --init --recursive
  Write-Host "UPDATE (Rebase) finished."
}

# --- Menu loop ---
while ($true) {
  Clear-Host

  # show ASCII art at top of the menu
  Write-Host $art

  Write-Host "autoPy++ - Update Menu" -ForegroundColor Cyan
  Write-Host "Repo: $repoRoot" -ForegroundColor DarkGray
  Write-Host "-----------------------------------------------"
  Write-Host "[1] Update (Safe: Fast-Forward only)"
  Write-Host "[2] Update (Hard-Reset to origin/<default>)"
  Write-Host "[3] Update (Rebase local commits)"
  Write-Host "[9] Create (initialize & attach to GitHub)"
  Write-Host "[0] Exit"
  Write-Host "-----------------------------------------------"
  $choice = Read-Host "Select"

  switch ($choice) {
    '1' { Op-Update-FFOnly;     Read-Host "Press ENTER to continue" | Out-Null }
    '2' { Op-Update-HardReset;  Read-Host "Press ENTER to continue" | Out-Null }
    '3' { Op-Update-Rebase;     Read-Host "Press ENTER to continue" | Out-Null }
    '9' { Op-Create;            Read-Host "Press ENTER to continue" | Out-Null }
    '0' { break }
    default { Write-Host "Invalid choice."; Start-Sleep -Milliseconds 900 }
  }
}

Write-Host "Bye!"
