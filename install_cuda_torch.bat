@echo off
REM ------------------------------------------------------------------
REM  One-click install of the NVIDIA (CUDA) build of PyTorch.
REM  Right click this file -> Run, or type:  .\install_cuda_torch.bat
REM  It asks for no typing and no copy-pasting of long URLs.
REM ------------------------------------------------------------------
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_cuda_torch.ps1"
echo.
pause
