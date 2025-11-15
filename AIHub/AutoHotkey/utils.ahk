; ============================================================================
; utils.ahk - Utility functions for AI Hub
; ============================================================================

; ============================================================================
; Text Capture and Clipboard Operations
; ============================================================================

; Captures the currently selected text by copying to clipboard
CaptureSelection() {
    ; Store original clipboard content
    ClipboardBackup := ClipboardAll()
    A_Clipboard := ""  ; Clear clipboard

    ; Send Ctrl+C to copy
    Send "^c"

    ; Wait for clipboard to contain data (timeout: 1 second)
    if !ClipWait(1) {
        ; Restore clipboard if nothing was copied
        A_Clipboard := ClipboardBackup
        return ""
    }

    ; Get the copied text
    CapturedText := A_Clipboard

    ; Restore original clipboard
    A_Clipboard := ClipboardBackup
    ClipboardBackup := ""

    return CapturedText
}

; Replaces currently selected text with new text
ReplaceSelection(NewText) {
    ; Store original clipboard
    ClipboardBackup := ClipboardAll()

    ; Put new text on clipboard
    A_Clipboard := NewText

    ; Wait for clipboard to be ready
    ClipWait(1)

    ; Paste the new text (replaces selection)
    Send "^v"

    ; Brief delay to ensure paste completes
    Sleep 100

    ; Restore original clipboard
    A_Clipboard := ClipboardBackup
    ClipboardBackup := ""
}

; Copies text to clipboard
CopyToClipboard(Text) {
    A_Clipboard := Text
    ClipWait(1)
}

; ============================================================================
; JSON Utilities
; ============================================================================

; Escapes a string for use in JSON
; Handles: quotes, backslashes, newlines, tabs, carriage returns
EscapeJson(Str) {
    ; Replace backslash first (must be first!)
    Str := StrReplace(Str, "\", "\\")

    ; Replace double quotes
    Str := StrReplace(Str, '"', '\"')

    ; Replace newlines
    Str := StrReplace(Str, "`n", "\n")

    ; Replace tabs
    Str := StrReplace(Str, "`t", "\t")

    ; Replace carriage returns
    Str := StrReplace(Str, "`r", "\r")

    return Str
}

; Parses JSON string to object (requires JSON.ahk or built-in JSON support)
ParseJson(JsonStr) {
    try {
        return JSON.parse(JsonStr)
    } catch {
        ; Fallback: return empty object if parsing fails
        return Map()
    }
}

; ============================================================================
; String Utilities
; ============================================================================

; Truncates a string to a maximum length and adds ellipsis if needed
TruncateString(Str, MaxLen := 100) {
    if (StrLen(Str) <= MaxLen)
        return Str
    else
        return SubStr(Str, 1, MaxLen - 3) . "..."
}

; Removes leading and trailing whitespace
Trim(Str) {
    return RegExReplace(Str, "^\s+|\s+$", "")
}

; ============================================================================
; File Operations
; ============================================================================

; Reads entire file content
ReadFile(FilePath) {
    try {
        return FileRead(FilePath)
    } catch {
        return ""
    }
}

; Writes content to file
WriteFile(FilePath, Content) {
    try {
        FileDelete(FilePath)
        FileAppend(Content, FilePath)
        return true
    } catch {
        return false
    }
}

; Checks if file exists
FileExists(FilePath) {
    return FileExist(FilePath) != ""
}

; ============================================================================
; GUI Utilities
; ============================================================================

; Centers a GUI window on screen
CenterWindow(GuiObj) {
    GuiObj.GetPos(&X, &Y, &W, &H)
    MonitorGetWorkArea(, &Left, &Top, &Right, &Bottom)

    NewX := (Right - Left - W) // 2 + Left
    NewY := (Bottom - Top - H) // 2 + Top

    GuiObj.Move(NewX, NewY)
}

; Shows a tooltip at the cursor position that auto-hides
ShowTooltip(Text, Duration := 2000) {
    ToolTip Text
    SetTimer () => ToolTip(), -Duration
}

; Shows a notification (uses tooltip for now, can be enhanced)
ShowNotification(Title, Message, Duration := 3000) {
    NotificationText := Title . "`n" . Message
    ShowTooltip(NotificationText, Duration)
}

; ============================================================================
; Process Management
; ============================================================================

; Checks if a process is running
IsProcessRunning(ProcessName) {
    return ProcessExist(ProcessName)
}

; Checks if a port is in use (Windows-specific netstat check)
IsPortInUse(Port) {
    try {
        ; Run netstat to check if port is listening
        Output := ComObjCreate("WScript.Shell").Exec("netstat -an").StdOut.ReadAll()
        return InStr(Output, ":" . Port . " ")
    } catch {
        return false
    }
}

; ============================================================================
; Configuration Management
; ============================================================================

; Loads settings from INI file
LoadSettings(IniFile, Section := "Settings") {
    Settings := Map()

    if !FileExists(IniFile)
        return Settings

    try {
        ; Read all keys from the section
        Keys := IniRead(IniFile, Section)

        ; Parse each line (format: key=value)
        Loop Parse, Keys, "`n", "`r" {
            if (A_LoopField = "")
                continue

            Parts := StrSplit(A_LoopField, "=", , 2)
            if (Parts.Length >= 2)
                Settings[Trim(Parts[1])] := Trim(Parts[2])
        }
    }

    return Settings
}

; Saves a setting to INI file
SaveSetting(IniFile, Section, Key, Value) {
    try {
        IniWrite(Value, IniFile, Section, Key)
        return true
    } catch {
        return false
    }
}

; ============================================================================
; Logging
; ============================================================================

; Simple logging function
LogMessage(Message, LogFile := "aihub_ahk.log") {
    Timestamp := FormatTime(, "yyyy-MM-dd HH:mm:ss")
    LogEntry := Timestamp . " - " . Message . "`n"

    try {
        FileAppend(LogEntry, LogFile)
    }
}

; ============================================================================
; Validation
; ============================================================================

; Checks if a string is empty or only whitespace
IsEmpty(Str) {
    return (Str = "" || RegExMatch(Str, "^\s*$"))
}

; Validates that a URL is properly formed
IsValidUrl(Url) {
    return RegExMatch(Url, "^https?://")
}

; ============================================================================
; Date/Time Utilities
; ============================================================================

; Gets current timestamp in ISO format
GetTimestamp() {
    return FormatTime(, "yyyy-MM-dd HH:mm:ss")
}

; ============================================================================
; Error Handling
; ============================================================================

; Displays an error message box
ShowError(ErrorMsg, Title := "AI Hub Error") {
    MsgBox(ErrorMsg, Title, "Icon! 0x10")  ; 0x10 = Error icon
}

; Displays a success message
ShowSuccess(Message, Title := "AI Hub") {
    MsgBox(Message, Title, "Icon! 0x40")  ; 0x40 = Info icon
}

; Displays a confirmation dialog (Yes/No)
ConfirmAction(Message, Title := "AI Hub") {
    Result := MsgBox(Message, Title, "YesNo Icon? 0x20")  ; 0x20 = Question icon
    return (Result = "Yes")
}
