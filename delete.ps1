$payload = 'PASTE_BASE64_HERE'
$bytes   = [Convert]::FromBase64String($payload)
$code    = [Text.Encoding]::Unicode.GetString($bytes)
Invoke-Expression $code
