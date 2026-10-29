# install_cuda_torch.ps1
# ------------------------------------------------------------------
# Puts matching NVIDIA (CUDA) builds of PyTorch and Torchvision into this project's .venv
# so that PICTURES are drawn on your GPU instead of the CPU.
#
# How to use:   .\install_cuda_torch.bat      (or right click -> Run with PowerShell)
#
# It tries the CUDA 12.8 / 12.6 / 12.4 channels in order and keeps the
# first one that really works (it checks both imports and CUDA availability).
# If no CUDA build can be installed, it puts the regular builds back,
# so your project is never left broken.
# ------------------------------------------------------------------

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host ""
    Write-Host "Could not find the virtual environment at:" -ForegroundColor Red
    Write-Host "  $python" -ForegroundColor Red
    Write-Host ""
    Write-Host "Create it first (VS Code: Python: Create Environment -> Venv)," -ForegroundColor Yellow
    Write-Host "or run:  python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  Installing the NVIDIA builds of PyTorch and Torchvision" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan

# --- 1. remove current builds so pip cannot say "already satisfied" ----
Write-Host ""
Write-Host "Step 1: removing current torch and torchvision..." -ForegroundColor Cyan
& $python -m pip uninstall -y torch torchvision

# --- 2. try the CUDA channels, newest first ----------------------------
$channels = @("cu128", "cu126", "cu124")

foreach ($cu in $channels) {
    Write-Host ""
    Write-Host "--------------------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "  Step 2: trying the $cu build (about 2.5 GB)..." -ForegroundColor Cyan
    Write-Host "--------------------------------------------------------------" -ForegroundColor DarkCyan

    $index = "https://download.pytorch.org/whl/" + $cu
    & $python -m pip install torch torchvision --index-url $index --upgrade

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  -> $cu could not be installed, trying the next one" -ForegroundColor Yellow
        continue
    }

    # --- 3. does it REALLY use the GPU? --------------------------------
    $test = & $python -c "import torch, torchvision; print(torch.cuda.is_available())"
    if ($LASTEXITCODE -eq 0 -and $test -eq "True") {
        Write-Host ""
        Write-Host "==============================================================" -ForegroundColor Green
        Write-Host "  DONE - PyTorch now uses your NVIDIA GPU" -ForegroundColor Green
        Write-Host "==============================================================" -ForegroundColor Green
        & $python -c "import torch, torchvision; print('torch version      :', torch.__version__); print('torchvision version:', torchvision.__version__); print('built with CUDA    :', torch.version.cuda); print('GPU name           :', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"
        exit 0
    }

    Write-Host "  -> $cu installed, but the GPU is still not used. Trying the next one." -ForegroundColor Yellow
}

# --- 4. nothing worked: put the regular torch builds back ---------------
Write-Host ""
Write-Host "No CUDA build could be installed." -ForegroundColor Yellow
Write-Host "Putting the regular torch builds back so nothing is broken..." -ForegroundColor Yellow
& $python -m pip install torch torchvision --upgrade

Write-Host ""
Write-Host "Your project still works, but pictures will be drawn on the CPU." -ForegroundColor Yellow
Write-Host "You can run this script again later when you have a better connection." -ForegroundColor Yellow
exit 1
