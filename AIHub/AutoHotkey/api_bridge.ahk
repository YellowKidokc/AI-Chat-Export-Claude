; ============================================================================
; api_bridge.ahk - HTTP Communication Bridge with Python Backend
; ============================================================================

; Global configuration
global API_BASE_URL := "http://127.0.0.1:8765"
global API_TIMEOUT := 30000  ; 30 seconds
global BACKEND_PROCESS := ""

; ============================================================================
; Backend Process Management
; ============================================================================

; Starts the Python backend server
StartBackend() {
    global BACKEND_PROCESS

    ; Check if already running
    if IsBackendRunning() {
        LogMessage("Backend already running")
        return true
    }

    ; Get paths
    ScriptDir := A_ScriptDir
    PythonDir := ScriptDir . "\..\Python"
    BackendScript := PythonDir . "\backend.py"

    ; Check if Python script exists
    if !FileExists(BackendScript) {
        ShowError("Backend script not found at:`n" . BackendScript)
        return false
    }

    ; Try to find Python executable
    PythonExe := FindPythonExecutable()
    if (PythonExe = "") {
        ShowError("Python not found. Please install Python 3.7+ and ensure it's in your PATH.")
        return false
    }

    ; Start the backend process
    try {
        LogMessage("Starting Python backend: " . BackendScript)

        ; Use pythonw.exe if available (no console window)
        PythonDir := SubStr(PythonExe, 1, InStr(PythonExe, "\",, -1))
        PythonWExe := PythonDir . "pythonw.exe"

        if FileExists(PythonWExe)
            PythonExe := PythonWExe

        ; Run the backend
        Run('"' . PythonExe . '" "' . BackendScript . '"', PythonDir, "Hide", &PID)
        BACKEND_PROCESS := PID

        ; Wait for backend to be ready (up to 10 seconds)
        Loop 20 {
            Sleep 500
            if IsBackendRunning() {
                LogMessage("Backend started successfully (PID: " . PID . ")")
                ShowNotification("AI Hub", "Backend started successfully")
                return true
            }
        }

        ShowError("Backend started but failed to respond. Check aihub.log for errors.")
        return false

    } catch as err {
        ShowError("Failed to start backend:`n" . err.Message)
        return false
    }
}

; Stops the Python backend server
StopBackend() {
    global BACKEND_PROCESS

    if (BACKEND_PROCESS != "") {
        try {
            ProcessClose(BACKEND_PROCESS)
            LogMessage("Backend process stopped")
            BACKEND_PROCESS := ""
        }
    }
}

; Checks if backend is running by testing the health endpoint
IsBackendRunning() {
    try {
        Response := SendRequest("GET", "/health")
        return (Response != "")
    } catch {
        return false
    }
}

; Finds Python executable in common locations
FindPythonExecutable() {
    ; Try common Python commands
    PythonCommands := ["python", "python3", "py"]

    for Index, Cmd in PythonCommands {
        try {
            ; Test if command exists by checking version
            Output := ComObjCreate("WScript.Shell").Exec(Cmd . " --version").StdOut.ReadAll()
            if InStr(Output, "Python") {
                ; Get full path
                FullPath := ComObjCreate("WScript.Shell").Exec("where " . Cmd).StdOut.ReadLine()
                if (FullPath != "")
                    return Trim(FullPath)
            }
        }
    }

    return ""
}

; ============================================================================
; HTTP Request Functions
; ============================================================================

; Sends an HTTP request to the backend
SendRequest(Method, Endpoint, JsonData := "") {
    global API_BASE_URL, API_TIMEOUT

    Url := API_BASE_URL . Endpoint

    try {
        ; Create HTTP request object
        http := ComObject("WinHttp.WinHttpRequest.5.1")

        ; Open connection
        http.Open(Method, Url, false)

        ; Set timeout
        http.SetTimeouts(5000, 5000, API_TIMEOUT, API_TIMEOUT)

        ; Set headers for JSON
        if (JsonData != "") {
            http.SetRequestHeader("Content-Type", "application/json")
        }

        ; Send request
        if (Method = "POST" && JsonData != "")
            http.Send(JsonData)
        else
            http.Send()

        ; Get response
        ResponseText := http.ResponseText
        StatusCode := http.Status

        ; Check status code
        if (StatusCode >= 200 && StatusCode < 300) {
            return ResponseText
        } else {
            LogMessage("HTTP Error " . StatusCode . ": " . ResponseText)
            throw Error("HTTP " . StatusCode . ": " . ResponseText)
        }

    } catch as err {
        LogMessage("Request failed: " . err.Message)
        throw err
    }
}

; Sends a POST request with JSON data
SendJsonRequest(Endpoint, JsonData) {
    return SendRequest("POST", Endpoint, JsonData)
}

; ============================================================================
; AI Hub API Functions
; ============================================================================

; Runs a prompt on text
RunPrompt(PromptId, Text) {
    ; Build JSON payload
    JsonPayload := '{"action":"run_prompt","prompt_id":"' . PromptId . '","text":"' . EscapeJson(Text) . '"}'

    try {
        ; Send request
        LogMessage("Running prompt: " . PromptId)
        Response := SendJsonRequest("/process", JsonPayload)

        ; Parse response
        ResponseObj := ParseJson(Response)

        if ResponseObj.Has("result")
            return ResponseObj["result"]
        else if ResponseObj.Has("error")
            throw Error(ResponseObj["error"])
        else
            throw Error("Invalid response from backend")

    } catch as err {
        ShowError("Failed to run prompt:`n" . err.Message)
        return ""
    }
}

; Sends a chat message
SendChatMessage(Message) {
    ; Build JSON payload
    JsonPayload := '{"action":"chat","message":"' . EscapeJson(Message) . '"}'

    try {
        ; Send request
        LogMessage("Sending chat message")
        Response := SendJsonRequest("/process", JsonPayload)

        ; Parse response
        ResponseObj := ParseJson(Response)

        if ResponseObj.Has("reply")
            return ResponseObj["reply"]
        else if ResponseObj.Has("error")
            throw Error(ResponseObj["error"])
        else
            throw Error("Invalid response from backend")

    } catch as err {
        ShowError("Failed to send chat message:`n" . err.Message)
        return ""
    }
}

; Gets all prompts from backend
GetPrompts() {
    JsonPayload := '{"action":"get_prompts"}'

    try {
        Response := SendJsonRequest("/process", JsonPayload)
        ResponseObj := ParseJson(Response)

        if ResponseObj.Has("prompts")
            return ResponseObj["prompts"]
        else
            return Map()

    } catch as err {
        LogMessage("Failed to get prompts: " . err.Message)
        return Map()
    }
}

; Updates a prompt
UpdatePrompt(PromptId, PromptData) {
    ; Build JSON - need to serialize PromptData map properly
    PromptJson := SerializePromptData(PromptData)
    JsonPayload := '{"action":"update_prompt","prompt_id":"' . PromptId . '","prompt_data":' . PromptJson . '}'

    try {
        Response := SendJsonRequest("/process", JsonPayload)
        ResponseObj := ParseJson(Response)

        if ResponseObj.Has("status")
            return (ResponseObj["status"] = "success")
        else
            return false

    } catch as err {
        ShowError("Failed to update prompt:`n" . err.Message)
        return false
    }
}

; Clears chat history
ClearChatHistory() {
    JsonPayload := '{"action":"clear_history"}'

    try {
        Response := SendJsonRequest("/process", JsonPayload)
        return true
    } catch {
        return false
    }
}

; ============================================================================
; Helper Functions
; ============================================================================

; Serializes prompt data map to JSON string
SerializePromptData(PromptData) {
    Json := "{"

    ; Add fields
    if PromptData.Has("name")
        Json .= '"name":"' . EscapeJson(PromptData["name"]) . '",'

    if PromptData.Has("template")
        Json .= '"template":"' . EscapeJson(PromptData["template"]) . '",'

    if PromptData.Has("enabled")
        Json .= '"enabled":' . (PromptData["enabled"] ? "true" : "false") . ','

    if PromptData.Has("description")
        Json .= '"description":"' . EscapeJson(PromptData["description"]) . '",'

    ; Remove trailing comma
    Json := RTrim(Json, ",")
    Json .= "}"

    return Json
}

; Checks backend health and returns status
CheckBackendHealth() {
    try {
        Response := SendRequest("GET", "/health")
        return ParseJson(Response)
    } catch {
        return Map()
    }
}
