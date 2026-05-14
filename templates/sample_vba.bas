
' WPS Script Manager 示例 VBA 宏
' 将此代码导入种子文件后保存，然后使用 extract_vba.py 提取 vbaProject.bin

Sub ScriptManager_Main()
    ' 主入口函数
    Call HelloWPS_Main
End Sub

Sub HelloWPS_Main()
    ' 示例宏：Hello WPS
    MsgBox "Hello from WPS Script Manager!", vbInformation, "WPS 脚本管理器"
End Sub

Sub InsertCurrentDate_Main()
    ' 示例宏：插入当前日期
    ActiveCell.Value = Date
End Sub
