$serviceName = "LabelManagementSystem"
$displayName = "Label Management System"
$binaryPath = "C:\Users\Bartender3\brady_label_automation\start_server.bat"

New-Service -Name $serviceName `
            -DisplayName $displayName `
            -BinaryPathName $binaryPath `
            -StartupType Automatic `
            -Description "Django server for Label Management System" 