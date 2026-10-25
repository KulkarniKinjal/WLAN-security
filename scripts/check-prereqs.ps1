# Optional PowerShell prerequisites checker, run on the Windows HOST
# (not inside Kali) before you begin the VM setup in docs/WINDOWS_SETUP.md.
# Safe to rerun; makes no changes.

Write-Host "== WLAN AttackLab Windows host prerequisites check ==" -ForegroundColor Cyan

$info = systeminfo | Select-String "Virtualization Enabled In Firmware"
if ($info -match "Yes") {
    Write-Host "[OK] Virtualization is enabled in firmware." -ForegroundColor Green
} else {
    Write-Host "[WARNING] Virtualization may be disabled. See docs/WINDOWS_SETUP.md step 2." -ForegroundColor Yellow
}

$vbox = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
if (Test-Path $vbox) {
    $version = & $vbox --version
    Write-Host "[OK] VirtualBox found: $version" -ForegroundColor Green
} else {
    Write-Host "[WARNING] VirtualBox not found at the default path. Install from https://www.virtualbox.org/wiki/Downloads" -ForegroundColor Yellow
}

$hyperv = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -ErrorAction SilentlyContinue
if ($hyperv -and $hyperv.State -eq "Enabled") {
    Write-Host "[WARNING] Hyper-V is enabled -- this can conflict with VirtualBox. See docs/WINDOWS_SETUP.md step 2." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Hyper-V does not appear to be enabled (or could not be checked without admin rights)." -ForegroundColor Green
}

Write-Host ""
Write-Host "This check does not install or change anything. Proceed to docs/WINDOWS_SETUP.md."
