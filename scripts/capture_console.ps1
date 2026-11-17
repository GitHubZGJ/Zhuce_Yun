param(
    [string]$Label = "ZhuceTest",
    [string]$Command = "..\.venv\Scripts\python.exe -m pytest -q",
    [string]$OutFile = "D:\idealCProject\HomeWork\evidence\tests\term_pytest.png",
    [int]$WaitSeconds = 18,
    [int]$Cols = 120,
    [int]$Lines = 30
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public class Win32Cap {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder sb, int count);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr after, int X, int Y, int cx, int cy, uint flags);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    public static List<KeyValuePair<IntPtr, string>> Windows() {
        var list = new List<KeyValuePair<IntPtr, string>>();
        EnumWindows((h, l) => {
            if (IsWindowVisible(h)) {
                var sb = new StringBuilder(512);
                GetWindowText(h, sb, 512);
                list.Add(new KeyValuePair<IntPtr, string>(h, sb.ToString()));
            }
            return true;
        }, IntPtr.Zero);
        return list;
    }
}
"@

$inner = "cmd.exe /k title $Label && mode con: cols=$Cols lines=$Lines && cd /d D:\idealCProject\HomeWork\backend && $Command"
$proc = Start-Process conhost.exe -ArgumentList $inner -PassThru
Start-Sleep -Seconds $WaitSeconds

$hwnd = [IntPtr]::Zero
foreach ($kv in [Win32Cap]::Windows()) {
    if ($kv.Value -like "$Label*") { $hwnd = $kv.Key; break }
}
if ($hwnd -eq [IntPtr]::Zero) { throw "console window not found by title $Label" }

[Win32Cap]::ShowWindow($hwnd, 9) | Out-Null
$rect0 = New-Object Win32Cap+RECT
[Win32Cap]::GetWindowRect($hwnd, [ref]$rect0) | Out-Null
$w0 = $rect0.Right - $rect0.Left
$h0 = $rect0.Bottom - $rect0.Top
[Win32Cap]::SetWindowPos($hwnd, [IntPtr](-1), 0, 0, $w0, $h0, 0x0040) | Out-Null
[Win32Cap]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 900

$rect = New-Object Win32Cap+RECT
[Win32Cap]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
$w = $rect.Right - $rect.Left
$h = $rect.Bottom - $rect.Top
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, (New-Object System.Drawing.Size $w, $h))
$g.Dispose()
$dir = Split-Path $OutFile -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$bmp.Save($OutFile, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "SAVED $OutFile ${w}x${h}"

Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
