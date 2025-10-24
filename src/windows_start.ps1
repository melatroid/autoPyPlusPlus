param(
    [string]$PythonExe = 'C:\Users\melatroid\AppData\Local\Programs\Python\Python310\python.exe',
    [string]$SrcDir    = 'C:\Users\melatroid\Desktop\autoPy++\AutoPyPlusPlus\src'
)

$UI = @{
  HeaderBg='DarkBlue'; HeaderFg='White'
  Border='Cyan'; Text='Gray'; Muted='DarkGray'
  Ok='Green'; Warn='Yellow'; Err='Red'; Info='DarkCyan'
}

function Out-Rule([string]$ch='-', [int]$width=0){
  if($width -le 0){ try{$width=[Math]::Max(40,[Console]::WindowWidth-2)}catch{$width=78} }
  Write-Host ($ch * $width) -ForegroundColor $UI.Border
}
function Out-Title([string]$text){
  Out-Rule '='
  Write-Host (" " + $text) -ForegroundColor $UI.HeaderFg -BackgroundColor $UI.HeaderBg
  Out-Rule '='
}
function Out-Panel([string]$Title,[string[]]$Lines=@(),[int]$Width=0){
  if($Width -le 0){ try{$Width=[Math]::Max(40,[Console]::WindowWidth-2)}catch{$Width=78} }
  $inner=$Width-4; $top="+{0}+" -f ('-'*($Width-2))
  Write-Host $top -ForegroundColor $UI.Border
  if($Title){
    $t=if($Title.Length -gt $inner){$Title.Substring(0,$inner)}else{$Title}
    $pad=' ' * ($inner - $t.Length)
    Write-Host ("| " + $t + $pad + " |")
    Write-Host $top -ForegroundColor $UI.Border
  }
  foreach($ln in $Lines){
    $line="$ln"
    while($line.Length -gt $inner){
      $chunk=$line.Substring(0,$inner); Write-Host ("| " + $chunk + " |"); $line=$line.Substring($inner)
    }
    $pad=' ' * ($inner - $line.Length); Write-Host ("| " + $line + $pad + " |")
  }
  Write-Host $top -ForegroundColor $UI.Border
}
function Say-Section([string]$Text){ Out-Title $Text }
function Say-Step   ([string]$Text){ Write-Host ("[STEP] " + $Text) -ForegroundColor $UI.Border }
function Say-Info   ([string]$Text){ Write-Host ("[INFO] " + $Text) -ForegroundColor $UI.Info }
function Say-Ok     ([string]$Text){ Write-Host ("[OK]   " + $Text) -ForegroundColor $UI.Ok }
function Say-Warn   ([string]$Text){ Write-Host ("[WARN] " + $Text) -ForegroundColor $UI.Warn }
function Say-Err    ([string]$Text){ Write-Host ("[ERR]  " + $Text) -ForegroundColor $UI.Err }
function Show-Item  ([string]$Name,[string]$Value){ Write-Host (" - {0}: " -f $Name) -NoNewline; Write-Host $Value -ForegroundColor $UI.Muted }

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

Say-Section "AutoPy++ Direct Launch"
Show-Item "Python"  $PythonExe
Show-Item "Source"  $SrcDir

Say-Step "Switching to working directory..."
Set-Location -Path $SrcDir

Say-Step "Launching AutoPyPlusPlus..."
& $PythonExe -m AutoPyPlusPlus @args
$code = $LASTEXITCODE

Say-Section "Done"
Write-Host ("Exit code: {0}" -f $code) -ForegroundColor $UI.Muted
exit $code
