; ============================================================================
; gui_tabs.ahk - Modular GUI Tab Creation and Management
; ============================================================================

; Global GUI state
global MainGui := ""
global CurrentPrompts := Map()

; ============================================================================
; Main GUI Creation
; ============================================================================

CreateMainGui() {
    global MainGui

    ; Create main window
    MainGui := Gui("+Resize", "AI Hub")
    MainGui.OnEvent("Close", (*) => MainGui.Hide())
    MainGui.OnEvent("Escape", (*) => MainGui.Hide())

    ; Create tab control
    Tab := MainGui.Add("Tab3", "x10 y10 w760 h550", ["Quick Actions", "Chat", "Prompts", "Settings"])

    ; Create each tab
    Tab.UseTab(1)
    CreateQuickActionsTab(MainGui)

    Tab.UseTab(2)
    CreateChatTab(MainGui)

    Tab.UseTab(3)
    CreatePromptsTab(MainGui)

    Tab.UseTab(4)
    CreateSettingsTab(MainGui)

    Tab.UseTab()  ; End tab usage

    ; Status bar at bottom
    MainGui.Add("Text", "x10 y570 w760 h25 vStatusBar", "Ready")

    return MainGui
}

; ============================================================================
; Quick Actions Tab
; ============================================================================

CreateQuickActionsTab(GuiObj) {
    ; Instructions
    GuiObj.Add("Text", "x20 y40 w720",
        "Select text anywhere and press a hotkey to process it with AI.`n" .
        "The processed text will replace your selection.")

    ; Enabled prompts group
    GuiObj.Add("GroupBox", "x20 y80 w720 h200", "Enabled Prompts")

    ; List of enabled prompts
    LV := GuiObj.Add("ListView", "x30 y100 w700 h150 vEnabledPromptsList",
        ["Hotkey", "Prompt Name", "Description"])
    LV.ModifyCol(1, 100)
    LV.ModifyCol(2, 200)
    LV.ModifyCol(3, 380)

    ; Manual input group
    GuiObj.Add("GroupBox", "x20 y290 w720 h240", "Manual Text Input")

    ; Input area
    GuiObj.Add("Text", "x30 y310 w100", "Input Text:")
    Edit := GuiObj.Add("Edit", "x30 y330 w700 h100 vQuickInputText WantReturn")

    ; Prompt selector
    GuiObj.Add("Text", "x30 y440 w100", "Select Prompt:")
    DDL := GuiObj.Add("DropDownList", "x130 y437 w300 vQuickPromptSelect")

    ; Process button
    Btn := GuiObj.Add("Button", "x440 y435 w120 h25", "Process Text")
    Btn.OnEvent("Click", ProcessQuickAction)

    ; Copy result button
    GuiObj.Add("Button", "x570 y435 w120 h25", "Copy Result")
        .OnEvent("Click", (*) => CopyToClipboard(GuiObj["QuickInputText"].Value))

    ; Refresh prompts button
    GuiObj.Add("Button", "x30 y490 w120 h25", "Refresh Prompts")
        .OnEvent("Click", (*) => RefreshEnabledPrompts())
}

; Processes text with selected prompt in Quick Actions tab
ProcessQuickAction(*) {
    global MainGui

    InputText := MainGui["QuickInputText"].Value
    PromptSelection := MainGui["QuickPromptSelect"].Text

    if IsEmpty(InputText) {
        ShowError("Please enter some text to process.")
        return
    }

    if IsEmpty(PromptSelection) {
        ShowError("Please select a prompt.")
        return
    }

    ; Extract prompt ID from selection (format: "Name (id)")
    if RegExMatch(PromptSelection, "\(([^)]+)\)$", &Match)
        PromptId := Match[1]
    else {
        ShowError("Invalid prompt selection.")
        return
    }

    ; Update status
    MainGui["StatusBar"].Value := "Processing..."

    ; Run prompt
    Result := RunPrompt(PromptId, InputText)

    if (Result != "") {
        MainGui["QuickInputText"].Value := Result
        MainGui["StatusBar"].Value := "Processing complete!"
        ShowNotification("AI Hub", "Text processed successfully!")
    } else {
        MainGui["StatusBar"].Value := "Processing failed."
    }
}

; ============================================================================
; Chat Tab
; ============================================================================

CreateChatTab(GuiObj) {
    ; Chat history display
    GuiObj.Add("Text", "x20 y40 w720", "Chat with AI Assistant:")

    ChatEdit := GuiObj.Add("Edit", "x20 y60 w720 h380 vChatHistory ReadOnly WantReturn")
    ChatEdit.Value := "AI Hub Chat - Ready to assist you!`n" . StrRepeat("=", 60) . "`n`n"

    ; Input area
    GuiObj.Add("Text", "x20 y450 w720", "Your Message:")
    GuiObj.Add("Edit", "x20 y470 w720 h50 vChatInput WantReturn")

    ; Buttons
    GuiObj.Add("Button", "x20 y530 w120 h25", "Send (Ctrl+Enter)")
        .OnEvent("Click", SendChatMessageHandler)

    GuiObj.Add("Button", "x150 y530 w120 h25", "Clear History")
        .OnEvent("Click", ClearChatHistoryHandler)

    GuiObj.Add("Button", "x280 y530 w120 h25", "Copy Chat")
        .OnEvent("Click", (*) => CopyToClipboard(MainGui["ChatHistory"].Value))
}

; Sends a chat message
SendChatMessageHandler(*) {
    global MainGui

    Message := Trim(MainGui["ChatInput"].Value)

    if IsEmpty(Message) {
        ShowError("Please enter a message.")
        return
    }

    ; Update UI
    MainGui["StatusBar"].Value := "Sending message..."

    ; Add user message to display
    ChatHistory := MainGui["ChatHistory"].Value
    ChatHistory .= "You: " . Message . "`n`n"
    MainGui["ChatHistory"].Value := ChatHistory

    ; Clear input
    MainGui["ChatInput"].Value := ""

    ; Send to backend
    Reply := SendChatMessage(Message)

    if (Reply != "") {
        ; Add AI reply to display
        ChatHistory .= "AI: " . Reply . "`n`n"
        MainGui["ChatHistory"].Value := ChatHistory

        ; Scroll to bottom
        SendMessage(0x115, 7, 0, MainGui["ChatHistory"])

        MainGui["StatusBar"].Value := "Message sent!"
    } else {
        MainGui["StatusBar"].Value := "Failed to send message."
    }
}

; Clears chat history
ClearChatHistoryHandler(*) {
    global MainGui

    if !ConfirmAction("Are you sure you want to clear the chat history?")
        return

    ; Clear backend history
    if ClearChatHistory() {
        ; Reset UI
        MainGui["ChatHistory"].Value := "Chat history cleared.`n`n"
        MainGui["StatusBar"].Value := "Chat history cleared."
        ShowNotification("AI Hub", "Chat history cleared successfully!")
    }
}

; ============================================================================
; Prompts Tab
; ============================================================================

CreatePromptsTab(GuiObj) {
    ; Instructions
    GuiObj.Add("Text", "x20 y40 w720",
        "Manage your AI prompts. Enable/disable prompts or edit their templates.")

    ; Prompts list
    LV := GuiObj.Add("ListView", "x20 y65 w720 h350 vPromptsList",
        ["ID", "Name", "Enabled", "Description"])
    LV.ModifyCol(1, 120)
    LV.ModifyCol(2, 150)
    LV.ModifyCol(3, 70)
    LV.ModifyCol(4, 350)
    LV.OnEvent("DoubleClick", EditPromptHandler)

    ; Buttons
    GuiObj.Add("Button", "x20 y425 w120 h25", "Refresh Prompts")
        .OnEvent("Click", (*) => LoadPromptsToList())

    GuiObj.Add("Button", "x150 y425 w120 h25", "Edit Prompt")
        .OnEvent("Click", EditPromptHandler)

    GuiObj.Add("Button", "x280 y425 w120 h25", "Toggle Enabled")
        .OnEvent("Click", TogglePromptHandler)

    ; Prompt details
    GuiObj.Add("Text", "x20 y460 w720", "Prompt Template Preview:")
    GuiObj.Add("Edit", "x20 y480 w720 h60 vPromptPreview ReadOnly")
}

; Loads prompts into the list view
LoadPromptsToList() {
    global MainGui, CurrentPrompts

    ; Get prompts from backend
    CurrentPrompts := GetPrompts()

    ; Clear list
    LV := MainGui["PromptsList"]
    LV.Delete()

    ; Populate list
    for PromptId, PromptData in CurrentPrompts {
        Name := PromptData.Has("name") ? PromptData["name"] : PromptId
        Enabled := PromptData.Has("enabled") && PromptData["enabled"] ? "Yes" : "No"
        Desc := PromptData.Has("description") ? PromptData["description"] : ""

        LV.Add("", PromptId, Name, Enabled, Desc)
    }

    MainGui["StatusBar"].Value := "Prompts refreshed. Total: " . CurrentPrompts.Count
}

; Edits a prompt
EditPromptHandler(*) {
    global MainGui, CurrentPrompts

    ; Get selected row
    RowNum := MainGui["PromptsList"].GetNext()
    if (RowNum = 0) {
        ShowError("Please select a prompt to edit.")
        return
    }

    ; Get prompt ID
    PromptId := MainGui["PromptsList"].GetText(RowNum, 1)

    if !CurrentPrompts.Has(PromptId) {
        ShowError("Prompt not found.")
        return
    }

    ; Show prompt template in preview
    PromptData := CurrentPrompts[PromptId]
    Template := PromptData.Has("template") ? PromptData["template"] : ""
    MainGui["PromptPreview"].Value := Template

    ShowNotification("Prompt Editor", "Editing: " . PromptData["name"] . "`nTemplate shown in preview below.")
}

; Toggles prompt enabled state
TogglePromptHandler(*) {
    global MainGui, CurrentPrompts

    ; Get selected row
    RowNum := MainGui["PromptsList"].GetNext()
    if (RowNum = 0) {
        ShowError("Please select a prompt to toggle.")
        return
    }

    ; Get prompt ID
    PromptId := MainGui["PromptsList"].GetText(RowNum, 1)

    if !CurrentPrompts.Has(PromptId) {
        ShowError("Prompt not found.")
        return
    }

    ; Toggle enabled state
    PromptData := CurrentPrompts[PromptId]
    CurrentEnabled := PromptData.Has("enabled") ? PromptData["enabled"] : false
    PromptData["enabled"] := !CurrentEnabled

    ; Update backend
    if UpdatePrompt(PromptId, PromptData) {
        ; Refresh list
        LoadPromptsToList()
        ShowNotification("AI Hub", "Prompt " . (CurrentEnabled ? "disabled" : "enabled"))
    }
}

; ============================================================================
; Settings Tab
; ============================================================================

CreateSettingsTab(GuiObj) {
    ; Backend status
    GuiObj.Add("GroupBox", "x20 y40 w720 h100", "Backend Status")

    GuiObj.Add("Text", "x30 y60 w150", "Backend Server:")
    GuiObj.Add("Text", "x180 y60 w300 vBackendStatus", "Checking...")

    GuiObj.Add("Button", "x30 y85 w120 h25", "Start Backend")
        .OnEvent("Click", (*) => StartBackendHandler())

    GuiObj.Add("Button", "x160 y85 w120 h25", "Check Status")
        .OnEvent("Click", (*) => UpdateBackendStatus())

    ; API Configuration
    GuiObj.Add("GroupBox", "x20 y150 w720 h120", "API Configuration")

    GuiObj.Add("Text", "x30 y170 w150", "AI Provider:")
    GuiObj.Add("DropDownList", "x180 y167 w200 vAIProvider", ["OpenAI", "Local LLM (Coming Soon)"])

    GuiObj.Add("Text", "x30 y200 w150", "Model:")
    GuiObj.Add("Edit", "x180 y197 w300 vModelName", "gpt-4o-mini")

    GuiObj.Add("Text", "x30 y230 w150", "API Key File:")
    GuiObj.Add("Text", "x180 y230 w400", "Place your API key in: AIHub\Python\apikey.txt")

    ; About
    GuiObj.Add("GroupBox", "x20 y280 w720 h120", "About AI Hub")

    AboutText := "AI Hub v1.0`n`n"
        . "An AutoHotkey + Python AI assistant for text processing and chat.`n"
        . "Designed for modular expansion and local AI integration.`n`n"
        . "Hotkeys: Ctrl+Shift+H (Toggle GUI) | Ctrl+Shift+P (Quick Popup)"

    GuiObj.Add("Text", "x30 y300 w680", AboutText)

    ; Update status on load
    SetTimer(UpdateBackendStatus, -500)
}

; Starts backend with UI feedback
StartBackendHandler() {
    global MainGui

    MainGui["StatusBar"].Value := "Starting backend..."

    if StartBackend() {
        UpdateBackendStatus()
    } else {
        MainGui["StatusBar"].Value := "Failed to start backend."
    }
}

; Updates backend status display
UpdateBackendStatus() {
    global MainGui

    if IsBackendRunning() {
        MainGui["BackendStatus"].Value := "✓ Running on http://127.0.0.1:8765"
        MainGui["BackendStatus"].Opt("+cGreen")
        MainGui["StatusBar"].Value := "Backend is running."
    } else {
        MainGui["BackendStatus"].Value := "✗ Not Running"
        MainGui["BackendStatus"].Opt("+cRed")
        MainGui["StatusBar"].Value := "Backend is not running. Click 'Start Backend' to launch it."
    }
}

; ============================================================================
; Quick Popup Window
; ============================================================================

CreateQuickPopup() {
    PopupGui := Gui("+AlwaysOnTop +ToolWindow", "AI Hub - Quick Actions")

    PopupGui.Add("Text", "x10 y10 w380", "Select an action for the selected text:")

    ; List enabled prompts as buttons
    Y := 40
    PopupGui.Add("Button", "x10 y" . Y . " w380 h30", "Clarify Text")
        .OnEvent("Click", (*) => QuickPromptAction("clarify", PopupGui))

    Y += 35
    PopupGui.Add("Button", "x10 y" . Y . " w380 h30", "Make Friendly")
        .OnEvent("Click", (*) => QuickPromptAction("friendly", PopupGui))

    Y += 35
    PopupGui.Add("Button", "x10 y" . Y . " w380 h30", "Summarize")
        .OnEvent("Click", (*) => QuickPromptAction("summarize", PopupGui))

    Y += 35
    PopupGui.Add("Button", "x10 y" . Y . " w380 h30", "Fix Grammar")
        .OnEvent("Click", (*) => QuickPromptAction("grammar", PopupGui))

    Y += 40
    PopupGui.Add("Button", "x10 y" . Y . " w180 h25", "Cancel")
        .OnEvent("Click", (*) => PopupGui.Hide())

    PopupGui.Add("Button", "x200 y" . Y . " w190 h25", "Open Main GUI")
        .OnEvent("Click", (*) => (PopupGui.Hide(), ShowMainGui()))

    return PopupGui
}

; Executes a quick prompt action
QuickPromptAction(PromptId, PopupGui) {
    PopupGui.Hide()

    ; Capture selected text
    Text := CaptureSelection()

    if IsEmpty(Text) {
        ShowError("No text selected. Please select some text and try again.")
        return
    }

    ; Process with AI
    ShowTooltip("Processing with AI...", 0)
    Result := RunPrompt(PromptId, Text)
    ToolTip()

    if (Result != "") {
        ; Replace selection with result
        ReplaceSelection(Result)
        ShowNotification("AI Hub", "Text processed successfully!")
    }
}

; ============================================================================
; Helper Functions
; ============================================================================

; Shows the main GUI
ShowMainGui() {
    global MainGui

    if (MainGui = "") {
        MainGui := CreateMainGui()
        CenterWindow(MainGui)
    }

    ; Refresh data
    LoadPromptsToList()
    RefreshEnabledPrompts()
    UpdateBackendStatus()

    MainGui.Show()
}

; Refreshes enabled prompts in Quick Actions tab
RefreshEnabledPrompts() {
    global MainGui, CurrentPrompts

    ; Get prompts
    CurrentPrompts := GetPrompts()

    ; Clear enabled prompts list
    LV := MainGui["EnabledPromptsList"]
    LV.Delete()

    ; Clear dropdown
    DDL := MainGui["QuickPromptSelect"]
    DDL.Delete()

    ; Add enabled prompts
    HotkeyNum := 1
    for PromptId, PromptData in CurrentPrompts {
        if PromptData.Has("enabled") && PromptData["enabled"] {
            Name := PromptData.Has("name") ? PromptData["name"] : PromptId
            Desc := PromptData.Has("description") ? PromptData["description"] : ""
            Hotkey := "Ctrl+Shift+" . HotkeyNum

            LV.Add("", Hotkey, Name, Desc)
            DDL.Add([Name . " (" . PromptId . ")"])

            HotkeyNum++
        }
    }
}
