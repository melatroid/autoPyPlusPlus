# Run-AutoPyPlusPlus.ps1

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

$pythonPath = 'C:\Program Files (x86)\Thonny\python.exe'
$srcDir     = 'C:\Users\melatroid\Desktop\autoPy++\AutoPyPlusPlus\src'

if (-not (Test-Path $pythonPath)) { Write-Error "Python not found: $pythonPath"; exit 1 }
if (-not (Test-Path $srcDir))     { Write-Error "Folder not found: $srcDir";   exit 1 }

Set-Location -Path $srcDir
& $pythonPath -m AutoPyPlusPlus
exit $LASTEXITCODE
