rule Aegis_Suspicious_Ransomware_Recovery_Inhibition : ransomware behavior
{
    meta:
        author = "Aegis PE Intelligence"
        description = "Multiple static command fragments associated with deleting recovery material"
        severity = "high"
        confidence = "medium"
        aegis_verdict = "suspicious"
        reference = "https://attack.mitre.org/techniques/T1490/"

    strings:
        $vssadmin = "vssadmin" ascii wide nocase
        $delete_shadows = "delete shadows" ascii wide nocase
        $shadowcopy_delete = "shadowcopy delete" ascii wide nocase
        $wbadmin_catalog = "wbadmin delete catalog" ascii wide nocase
        $recovery_disabled = "recoveryenabled no" ascii wide nocase

    condition:
        uint16(0) == 0x5a4d and 2 of them
}

rule Aegis_Informational_UPX_Packing : packed
{
    meta:
        author = "Aegis PE Intelligence"
        description = "Common UPX section markers; packing alone is not malicious"
        severity = "informational"
        confidence = "medium"

    strings:
        $upx0 = "UPX0" ascii
        $upx1 = "UPX1" ascii
        $upx2 = "UPX2" ascii

    condition:
        uint16(0) == 0x5a4d and 2 of them
}
