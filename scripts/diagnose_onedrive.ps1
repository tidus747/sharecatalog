# Registry-only diagnostic. Never resolve the input path or query a synced file.
[CmdletBinding()]
param(
    [string]$Path,
    [switch]$SummaryOnly
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

if (-not $Path) {
    if ($SummaryOnly) {
        throw 'Supply an absolute Windows path with -Path.'
    }
    $inputWindow = New-Object System.Windows.Forms.Form
    $inputWindow.Text = 'Paste a synced file or directory path (no file access)'
    $inputWindow.Size = New-Object System.Drawing.Size(850, 155)
    $inputWindow.StartPosition = 'CenterScreen'
    $inputText = New-Object System.Windows.Forms.TextBox
    $inputText.SetBounds(15, 15, 800, 25)
    $accept = New-Object System.Windows.Forms.Button
    $accept.Text = 'Inspect registry'
    $accept.SetBounds(15, 55, 160, 30)
    $accept.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $inputWindow.Controls.Add($inputText)
    $inputWindow.Controls.Add($accept)
    $inputWindow.AcceptButton = $accept
    try {
        if ($inputWindow.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
            return
        }
        $Path = $inputText.Text.Trim().Trim('"')
    }
    finally {
        $inputWindow.Dispose()
    }
}

if ($Path -notmatch '^(?:[A-Za-z]:[\\/]|\\\\[^\\]+\\[^\\]+\\)') {
    throw 'Paste an absolute Windows drive or UNC path.'
}
# GetFullPath is lexical. Do not use Resolve-Path, Get-Item, file pickers or Shell COM.
$inputPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
$matchesByPair = @{}
$registryStatus = 'Provider registry not present'
$registryRoot = 'HKCU:\Software\SyncEngines\Providers\OneDrive'
if (Test-Path -LiteralPath $registryRoot) {
    $registryStatus = 'Read successfully'
    try {
        foreach ($key in Get-ChildItem -LiteralPath $registryRoot) {
            $values = Get-ItemProperty -LiteralPath $key.PSPath
            if ([string]::IsNullOrWhiteSpace($values.MountPoint) -or
                [string]::IsNullOrWhiteSpace($values.UrlNamespace)) {
                continue
            }
            $localRoot = [IO.Path]::GetFullPath([string]$values.MountPoint).TrimEnd('\')
            if ($inputPath.Equals($localRoot, [StringComparison]::OrdinalIgnoreCase) -or
                $inputPath.StartsWith($localRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
                $url = ([string]$values.UrlNamespace).TrimEnd('/')
                $identity = $localRoot.ToLowerInvariant() + "`n" + $url
                $matchesByPair[$identity] = [PSCustomObject]@{LocalRoot = $localRoot; WebUrl = $url}
            }
        }
    }
    catch {
        # Fail closed: an incomplete read can hide a more specific library.
        $matchesByPair.Clear()
        $registryStatus = 'Provider registry read incomplete; configure a mapping manually'
    }
}
$candidates = @($matchesByPair.Values | Sort-Object -Property @{Expression = {$_.LocalRoot.Length}; Descending = $true})
$candidateLines = New-Object 'System.Collections.Generic.List[string]'
foreach ($candidate in $candidates) {
    $candidateLines.Add('Local root: ' + $candidate.LocalRoot)
    $candidateLines.Add('Web namespace: ' + $candidate.WebUrl)
    $candidateLines.Add('')
}

# Console output deliberately omits all private paths and URLs.
Write-Output 'File access: None (registry-only inspection)'
Write-Output ('Distinct local/web candidates: ' + $candidates.Count)
Write-Output ('Registry inspection: ' + $registryStatus)

if (-not $SummaryOnly) {
    $report = @(
        'ShareCatalog OneDrive diagnostic (registry only)',
        '',
        ('Input path (not accessed): ' + $inputPath),
        '',
        ('Distinct local/web candidates: ' + $candidates.Count),
        ('Registry inspection: ' + $registryStatus),
        '',
        ($candidateLines -join [Environment]::NewLine),
        'Candidates are ordered by specificity. Conflicting entries require manual configuration.',
        'Registry fields are implementation details, not verified library URLs.',
        'No synced file was accessed. No Shell properties or file picker were used.',
        'No registry values, clipboard contents, or sharing permissions were changed.',
        'Nothing was saved or sent. Keep the paths and URLs in this window private.'
    ) -join [Environment]::NewLine

    $window = New-Object System.Windows.Forms.Form
    $window.Text = 'ShareCatalog: OneDrive registry diagnostic'
    $window.Size = New-Object System.Drawing.Size(900, 550)
    $window.StartPosition = 'CenterScreen'
    $text = New-Object System.Windows.Forms.TextBox
    $text.Multiline = $true
    $text.ReadOnly = $true
    $text.ScrollBars = 'Both'
    $text.WordWrap = $false
    $text.Dock = 'Fill'
    $text.Text = $report
    $window.Controls.Add($text)
    try {
        [void]$window.ShowDialog()
    }
    finally {
        $window.Dispose()
    }
}
