; ============================================================================
; AI Hub - Main Entry Point
; ============================================================================
; A hybrid AutoHotkey + Python AI assistant for text processing and chat
;
; Features:
; - Text processing with customizable AI prompts
; - Chat interface for AI conversations
; - Prompt library management
; - Hotkey-driven workflow for quick access
; - Modular architecture for easy expansion
;
; Hotkeys:
; - Ctrl+Shift+H: Toggle main GUI
; - Ctrl+Shift+P: Show quick popup for selected text
; - Ctrl+Shift+Q: Quick clarify (process selected text)
;
; Version: 1.0
; ============================================================================

#Requires AutoHotkey v2.0
#SingleInstance Force

; Set working directory to script location
SetWorkingDir A_ScriptDir

; ============================================================================
; Load Dependencies
; ============================================================================

#Include utils.ahk
#Include api_bridge.ahk
#Include gui_tabs.ahk

; ============================================================================
; Global Variables
; ============================================================================

global QuickPopup := ""
global AppInitialized := false

; ============================================================================
; Initialization
; ============================================================================

Initialize() {
    global AppInitialized

    if AppInitialized
        return

    LogMessage("=" . StrRepeat("=", 60))
    LogMessage("AI Hub Starting - " . A_ScriptName)
    LogMessage("=" . StrRepeat("=", 60))

    ; Check if backend is running, if not start it
    if !IsBackendRunning() {
        LogMessage("Backend not running, attempting to start...")

        if !StartBackend() {
            ; Show error but don't exit - user can start manually
            MsgBox(
                "Failed to start Python backend automatically.`n`n"
                . "Please ensure:`n"
                . "1. Python 3.7+ is installed`n"
                . "2. Required packages are installed (run: pip install -r requirements.txt)`n"
                . "3. Backend script exists at: AIHub\Python\backend.py`n`n"
                . "You can try starting it manually from the Settings tab.",
                "AI Hub - Backend Startup Failed",
                "Icon! 0x30"
            )
        } else {
            LogMessage("Backend started successfully")
        }
    } else {
        LogMessage("Backend already running")
    }

    ; Create quick popup (but don't show it)
    global QuickPopup
    QuickPopup := CreateQuickPopup()

    AppInitialized := true
    LogMessage("AI Hub initialized successfully")

    ; Show welcome notification
    ShowNotification("AI Hub", "Press Ctrl+Shift+H to open AI Hub")
}

; ============================================================================
; Hotkeys
; ============================================================================

; Ctrl+Shift+H - Toggle Main GUI
^+h:: {
    global MainGui

    ; Initialize if needed
    if !AppInitialized
        Initialize()

    ; Toggle GUI
    if (MainGui = "" || !WinExist("ahk_id " . MainGui.Hwnd)) {
        ShowMainGui()
    } else if WinActive("ahk_id " . MainGui.Hwnd) {
        MainGui.Hide()
    } else {
        WinActivate("ahk_id " . MainGui.Hwnd)
    }
}

; Ctrl+Shift+P - Quick Popup
^+p:: {
    global QuickPopup

    ; Initialize if needed
    if !AppInitialized
        Initialize()

    ; Check if backend is running
    if !IsBackendRunning() {
        ShowError("Backend is not running.`nPlease start it from the Settings tab (Ctrl+Shift+H).")
        return
    }

    ; Show popup
    if (QuickPopup != "") {
        QuickPopup.Show()
        WinActivate("ahk_id " . QuickPopup.Hwnd)
    }
}

; Ctrl+Shift+Q - Quick Clarify (process selected text immediately)
^+q:: {
    ; Initialize if needed
    if !AppInitialized
        Initialize()

    ; Check if backend is running
    if !IsBackendRunning() {
        ShowError("Backend is not running.`nPlease start it from the Settings tab (Ctrl+Shift+H).")
        return
    }

    ; Capture selection
    Text := CaptureSelection()

    if IsEmpty(Text) {
        ShowError("No text selected. Please select some text and try again.")
        return
    }

    ; Process with clarify prompt
    ShowTooltip("Clarifying text...", 0)
    Result := RunPrompt("clarify", Text)
    ToolTip()

    if (Result != "") {
        ; Replace selection
        ReplaceSelection(Result)
        ShowNotification("AI Hub", "Text clarified successfully!")
    }
}

; Ctrl+Shift+F - Quick Friendly (make text friendly)
^+f:: {
    if !AppInitialized
        Initialize()

    if !IsBackendRunning() {
        ShowError("Backend is not running.")
        return
    }

    Text := CaptureSelection()
    if IsEmpty(Text) {
        ShowError("No text selected.")
        return
    }

    ShowTooltip("Making text friendly...", 0)
    Result := RunPrompt("friendly", Text)
    ToolTip()

    if (Result != "")
        ReplaceSelection(Result)
}

; Ctrl+Shift+G - Quick Grammar Fix
^+g:: {
    if !AppInitialized
        Initialize()

    if !IsBackendRunning() {
        ShowError("Backend is not running.")
        return
    }

    Text := CaptureSelection()
    if IsEmpty(Text) {
        ShowError("No text selected.")
        return
    }

    ShowTooltip("Fixing grammar...", 0)
    Result := RunPrompt("grammar", Text)
    ToolTip()

    if (Result != "")
        ReplaceSelection(Result)
}

; ============================================================================
; Tray Menu
; ============================================================================

; Create custom tray menu
A_TrayMenu.Delete()  ; Remove default items

A_TrayMenu.Add("AI Hub", (*) => ShowMainGui())
A_TrayMenu.Default := "AI Hub"

A_TrayMenu.Add("Quick Popup", (*) => (QuickPopup != "" ? QuickPopup.Show() : ""))
A_TrayMenu.Add()  ; Separator

A_TrayMenu.Add("Start Backend", (*) => StartBackend())
A_TrayMenu.Add("Check Backend", (*) => CheckBackendStatusTray())
A_TrayMenu.Add()  ; Separator

A_TrayMenu.Add("Hotkeys:", "")
A_TrayMenu.Disable("Hotkeys:")
A_TrayMenu.Add("  Ctrl+Shift+H - Main GUI", "")
A_TrayMenu.Disable("  Ctrl+Shift+H - Main GUI")
A_TrayMenu.Add("  Ctrl+Shift+P - Quick Popup", "")
A_TrayMenu.Disable("  Ctrl+Shift+P - Quick Popup")
A_TrayMenu.Add("  Ctrl+Shift+Q - Quick Clarify", "")
A_TrayMenu.Disable("  Ctrl+Shift+Q - Quick Clarify")
A_TrayMenu.Add()  ; Separator

A_TrayMenu.Add("Reload", (*) => Reload())
A_TrayMenu.Add("Exit", (*) => ExitApp())

; ============================================================================
; Tray Functions
; ============================================================================

CheckBackendStatusTray(*) {
    if IsBackendRunning() {
        MsgBox("Backend is running on http://127.0.0.1:8765", "AI Hub - Backend Status", "Icon!")
    } else {
        Result := MsgBox(
            "Backend is not running.`n`nWould you like to start it now?",
            "AI Hub - Backend Status",
            "YesNo Icon?"
        )
        if (Result = "Yes")
            StartBackend()
    }
}

; ============================================================================
; Startup
; ============================================================================

; Auto-initialize on script start
Initialize()

; Keep script running
Persistent()

; ============================================================================
; Cleanup on Exit
; ============================================================================

OnExit(CleanupOnExit)

CleanupOnExit(ExitReason, ExitCode) {
    LogMessage("AI Hub exiting - Reason: " . ExitReason)

    ; Optionally stop backend
    ; Uncomment the line below if you want to stop the backend when closing the script
    ; StopBackend()

    LogMessage("AI Hub cleanup complete")
}

; ============================================================================
; Helper Functions
; ============================================================================

; String repeat utility
StrRepeat(Str, Count) {
    Result := ""
    Loop Count
        Result .= Str
    return Result
}

; ============================================================================
; Welcome Message
; ============================================================================

; Show startup message in console (if running with /Debug or from editor)
if A_IsCompiled = 0 {
    OutputDebug("
    (
    ============================================================
    AI Hub v1.0 - AutoHotkey AI Assistant
    ============================================================

    Hotkeys:
      Ctrl+Shift+H  - Toggle Main GUI
      Ctrl+Shift+P  - Quick Popup Menu
      Ctrl+Shift+Q  - Quick Clarify
      Ctrl+Shift+F  - Quick Friendly Tone
      Ctrl+Shift+G  - Quick Grammar Fix

    The Python backend will start automatically.
    Right-click the tray icon for more options.

    ============================================================
    )")
}
