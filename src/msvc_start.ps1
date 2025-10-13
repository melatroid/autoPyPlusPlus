# Run-AutoPyPlusPlus-Msvc.ps1

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

$vcvars     = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
$pythonPath = 'C:\Program Files (x86)\Thonny\python.exe'
$srcDir     = 'C:\Users\melatroid\Desktop\autoPy++\AutoPyPlusPlus\src'

if (-not (Test-Path $vcvars))     { Write-Error "vcvars64.bat nicht gefunden: $vcvars"; exit 1 }
if (-not (Test-Path $pythonPath)) { Write-Error "Python nicht gefunden: $pythonPath";    exit 1 }
if (-not (Test-Path $srcDir))     { Write-Error "Ordner nicht gefunden: $srcDir";        exit 1 }

$cmd = "call `"$vcvars`" && cd /d `"$srcDir`" && `"$pythonPath`" -m AutoPyPlusPlus && pause"
cmd.exe /c $cmd
