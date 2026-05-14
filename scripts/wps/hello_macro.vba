' WPS Word 测试宏 - Hello World
' 这是一个简单的测试宏示例

Sub HelloWorld()
    ' 显示欢迎消息
    MsgBox "Hello, WPS 脚本管理器！", vbInformation, "脚本管理器"

    ' 在文档中插入文本
    Selection.TypeText Text:="=================================" & vbCrLf
    Selection.TypeText Text:="这是通过脚本管理器部署的测试宏" & vbCrLf
    Selection.TypeText Text:="执行时间：" & Now() & vbCrLf
    Selection.TypeText Text:="=================================" & vbCrLf
End Sub

' 插入当前日期时间
Sub InsertDateTime()
    Dim dt As String
    dt = Format(Now(), "yyyy-mm-dd hh:nn:ss")
    Selection.TypeText Text:="[" & dt & "]"
End Sub
