package com.sitelens.ai

import android.Manifest
import android.content.Context
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ExitToApp
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.google.gson.annotations.SerializedName
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import okio.ByteString
import java.io.Closeable
import java.io.IOException
import kotlin.math.roundToInt
import com.sitelens.ai.R
import com.sitelens.ai.BuildConfig
import androidx.compose.ui.res.painterResource
import androidx.camera.view.PreviewView

// --- Data Models ---

data class SessionCreateRequest(
    @SerializedName("user_id") val userId: String?,
    @SerializedName("worker_name") val workerName: String,
    @SerializedName("site_name") val siteName: String,
    val language: String,
    @SerializedName("glasses_id") val glassesId: String?,
)

data class SessionResponse(
    val id: String,
    @SerializedName("worker_name") val workerName: String,
    @SerializedName("site_name") val siteName: String,
    val language: String,
    @SerializedName("glasses_id") val glassesId: String?,
    val status: String,
    @SerializedName("is_live") val isLive: Boolean,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("updated_at") val updatedAt: String,
)

data class GlassesEventRequest(
    @SerializedName("event_type") val eventType: String,
    val source: String = "meta-glasses",
    @SerializedName("camera_observation") val cameraObservation: String? = null,
    @SerializedName("audio_transcript") val audioTranscript: String? = null,
    @SerializedName("hazard_flags") val hazardFlags: List<String> = emptyList(),
    val metadata: Map<String, Any> = emptyMap(),
)

data class GlassesSocketEventRequest(
    @SerializedName("event_type") val eventType: String,
    val source: String = "meta-glasses",
    @SerializedName("camera_observation") val cameraObservation: String? = null,
    @SerializedName("audio_transcript") val audioTranscript: String? = null,
    @SerializedName("hazard_flags") val hazardFlags: List<String> = emptyList(),
    val metadata: Map<String, Any> = emptyMap(),
)

data class GlassesEventResponse(
    val id: Int,
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("event_type") val eventType: String,
    val source: String,
    @SerializedName("camera_observation") val cameraObservation: String?,
    @SerializedName("audio_transcript") val audioTranscript: String?,
    @SerializedName("hazard_flags") val hazardFlags: List<String>,
    val metadata: Map<String, Any>,
    @SerializedName("created_at") val createdAt: String,
)

data class SiteReportResponse(
    val id: Int,
    @SerializedName("session_id") val sessionId: String,
    val title: String,
    val summary: String,
    val severity: String,
    @SerializedName("recommended_actions") val recommendedActions: List<String>,
    val metrics: Map<String, Any>,
    @SerializedName("is_latest") val isLatest: Boolean,
    @SerializedName("created_at") val createdAt: String,
)

data class SocketAckResponse(
    val status: String,
    @SerializedName("session_id") val sessionId: String,
    val event: GlassesEventResponse? = null,
    val report: SiteReportResponse? = null,
    @SerializedName("assistant_message") val assistantMessage: String? = null,
)

enum class SessionType {
    PHONE, GLASSES, NONE
}

sealed class Screen {
    object Login : Screen()
    object Home : Screen()
    object ActiveSession : Screen()
}

data class User(
    val id: String,
    val username: String,
    @SerializedName("full_name") val fullName: String? = null,
    @SerializedName("emp_id") val employeeId: String? = null,
    val role: String? = null
)

data class Site(
    val id: Int,
    @SerializedName("site_name") val name: String? = null,
    val description: String? = null
)

data class Task(
    val id: Int,
    val title: String? = null,
    val description: String? = null,
    val status: String? = null
)

data class LanguageOption(
    val code: String,
    val name: String,
    val nativeName: String,
    val flag: String
)

val SUPPORTED_LANGUAGES = listOf(
    LanguageOption("en", "English", "English", "🌐"),
    LanguageOption("ta", "Tamil", "தமிழ்", "🇮🇳"),
    LanguageOption("te", "Telugu", "తెలుగు", "🇮🇳"),
    LanguageOption("ml", "Malayalam", "മലയാളം", "🇮🇳"),
    LanguageOption("kn", "Kannada", "கன்னட / ಕನ್ನಡ", "🇮🇳"),
    LanguageOption("mr", "Marathi", "मराठी", "🇮🇳"),
    LanguageOption("hi", "Hindi", "हिन्दी", "🇮🇳"),
    LanguageOption("bn", "Bengali", "বাংলা", "🇮🇳"),
    LanguageOption("gu", "Gujarati", "ગુજરાતી", "🇮🇳"),
    LanguageOption("pa", "Punjabi", "ਪੰਜਾਬੀ", "🇮🇳"),
    LanguageOption("or", "Odia", "ଓଡ଼ିଆ", "🇮🇳"),
    LanguageOption("es", "Spanish", "Español", "🇪🇸"),
    LanguageOption("fr", "French", "Français", "🇫🇷"),
    LanguageOption("de", "German", "Deutsch", "🇩🇪"),
    LanguageOption("ja", "Japanese", "日本語", "🇯🇵"),
    LanguageOption("zh", "Chinese", "中文", "🇨🇳"),
    LanguageOption("ar", "Arabic", "العربية", "🇸🇦"),
    LanguageOption("pt", "Portuguese", "Português", "🇵🇹"),
    LanguageOption("it", "Italian", "Italiano", "🇮🇹"),
    LanguageOption("ru", "Russian", "Русский", "🇷🇺"),
    LanguageOption("ko", "Korean", "한국어", "🇰🇷")
)

data class BridgeUiState(
    val backendUrl: String = BuildConfig.DEFAULT_BACKEND_URL,
    val currentScreen: Screen = Screen.Login,
    val currentUser: User? = null,
    val availableSites: List<Site> = emptyList(),
    val currentTasks: List<Task> = emptyList(),
    val selectedSite: Site? = null,
    val workerName: String = "Worker A",
    val siteName: String = "North Tower",
    val language: String = "en",
    val glassesId: String = "meta-glasses-01",
    val cameraObservation: String = "Forklift entering the loading bay",
    val voiceTranscript: String = "Need support at zone four",
    val sessionId: String? = null,
    val connectionStatus: String = "Disconnected",
    val assistantMessage: String = "Ready to start a site session.",
    val latestSeverity: String? = null,
    val latestReportAt: String? = null,
    val recentEvents: List<String> = emptyList(),
    val bleState: BleBridgeState = BleBridgeState(),
    val isStreaming: Boolean = false,
    val isDemoStreaming: Boolean = false,
    val isBusy: Boolean = false,
    val isCameraPaused: Boolean = false,
    val isMicPaused: Boolean = false,
    val isSessionPaused: Boolean = false,
    val selectedTab: Int = 0,
    val errorMessage: String? = null,
    val sessionType: SessionType = SessionType.NONE,
    val showSessionTypeDialog: Boolean = false,
    val showGlassesSetupDialog: Boolean = false,
    val isInPiPMode: Boolean = false,
    val isListening: Boolean = false,
    val showSummaryDialog: Boolean = false,
    val sessionSummary: String? = null,
)

// --- API Client ---

class SiteLensApiClient(
    private val backendUrl: String,
    private val client: OkHttpClient,
) {
    private val gson: Gson = GsonBuilder().create()
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    suspend fun startSession(request: SessionCreateRequest): SessionResponse = withContext(Dispatchers.IO) {
        executePost("/api/sessions/start", request, SessionResponse::class.java)
    }

    suspend fun sendEvent(sessionId: String, request: GlassesEventRequest): GlassesEventResponse = withContext(Dispatchers.IO) {
        executePost("/api/sessions/$sessionId/events", request, GlassesEventResponse::class.java)
    }

    suspend fun generateReport(sessionId: String): SiteReportResponse = withContext(Dispatchers.IO) {
        executePost("/api/sessions/$sessionId/reports/generate", null, SiteReportResponse::class.java)
    }

    suspend fun uploadFrame(sessionId: String, jpegBytes: ByteArray): GlassesEventResponse = withContext(Dispatchers.IO) {
        val requestBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart(
                "image",
                "frame.jpg",
                jpegBytes.toRequestBody("image/jpeg".toMediaType())
            )
            .addFormDataPart("prompt", "Analyze site frame for safety hazards")
            .build()

        val request = Request.Builder()
            .url(backendUrl.trimEnd('/') + "/api/sessions/$sessionId/upload-frame")
            .post(requestBody)
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("HTTP ${response.code}: ${response.message}")
            val responseBody = response.body?.string().orEmpty()
            return@withContext gson.fromJson(responseBody, GlassesEventResponse::class.java)
        }
    }

    suspend fun stopSession(sessionId: String): SessionResponse = withContext(Dispatchers.IO) {
        executePost("/api/sessions/$sessionId/stop", null, SessionResponse::class.java)
    }

    fun openSocket(
        sessionId: String,
        onText: (String) -> Unit,
        onStatus: (String) -> Unit,
        onError: (String) -> Unit,
    ): WebSocket {
        val request = Request.Builder()
            .url(webSocketUrl(sessionId))
            .build()

        return client.newWebSocket(
            request,
            object : WebSocketListener() {
                override fun onOpen(webSocket: WebSocket, response: Response) {
                    onStatus("Connected to glasses stream")
                }
                override fun onMessage(webSocket: WebSocket, text: String) {
                    onText(text)
                }
                override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                    onText(bytes.utf8())
                }
                override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                    onError(t.message ?: "Socket failure")
                }
                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                    onStatus("Stream closed: $reason")
                }
            },
        )
    }

    private fun webSocketUrl(sessionId: String): String {
        val normalized = backendUrl.trimEnd('/')
        return when {
            normalized.startsWith("https://") -> normalized.replaceFirst("https://", "wss://") + "/ws/glasses/$sessionId"
            normalized.startsWith("http://") -> normalized.replaceFirst("http://", "ws://") + "/ws/glasses/$sessionId"
            else -> "ws://$normalized/ws/glasses/$sessionId"
        }
    }

    private fun <T> executePost(path: String, body: Any?, responseType: Class<T>): T {
        val requestBody = body?.let {
            gson.toJson(it).toRequestBody(jsonMediaType)
        } ?: "".toRequestBody(null)

        val request = Request.Builder()
            .url(backendUrl.trimEnd('/') + path)
            .post(requestBody)
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("HTTP ${response.code}: ${response.message}")
            val responseBody = response.body?.string().orEmpty()
            return gson.fromJson(responseBody, responseType)
        }
    }
}

// --- Controller ---

class BridgeController(initialBackendUrl: String, context: Context) : Closeable {
    private val prefs = context.getSharedPreferences("sitelens_prefs", Context.MODE_PRIVATE)
    private val exceptionHandler = CoroutineExceptionHandler { _, throwable ->
        android.util.Log.e("BridgeController", "Uncaught exception", throwable)
        updateState { copy(errorMessage = "Internal error: ${throwable.message}") }
    }
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate + exceptionHandler)
    private val gson = GsonBuilder().create()
    private val _state = MutableStateFlow(
        BridgeUiState(
            backendUrl = prefs.getString("backend_url", initialBackendUrl) ?: initialBackendUrl,
            language = prefs.getString("selected_language", "en") ?: "en"
        )
    )
    val state: StateFlow<BridgeUiState> = _state.asStateFlow()
    private var socket: WebSocket? = null
    private var demoJob: Job? = null
    private var lastSpokenMessage: String? = null
    
    // Throttling for UI logs
    private val pendingLogs = mutableListOf<String>()
    private var logThrottleJob: Job? = null
    
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
        .writeTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
        .build()

    private val bleBridge = BleGlassBridge(
        context = context,
        onStateChanged = { bleState -> updateState { copy(bleState = bleState) } },
    ) { packet -> ingestBlePacket(packet) }
    private val voiceAssistant = VoiceAssistantManager(context)
    private val voiceRecognizer = VoiceRecognitionManager(
        context = context,
        onResult = { text -> handleVoiceInput(text) },
        onStateChange = { listening -> updateState { copy(isListening = listening) } },
        onError = { error -> updateState { copy(errorMessage = error) } }
    )

    private fun handleVoiceInput(rawText: String) {
        val trimmed = rawText.trim()
        if (trimmed.isBlank()) return

        val lower = trimmed.lowercase()
        val wakeWords = listOf(
            "slen", "s len", "s-len", "selen", "es len", "sleen", "hey slen", "ok slen", "hi slen", "hello slen",
            "meta", "m-eta", "hey meta", "ok meta", "hi meta", "hello meta"
        )

        var foundWakeWord = false
        var cleanedText = trimmed

        for (ww in wakeWords) {
            if (lower.contains(ww)) {
                foundWakeWord = true
                val idx = lower.indexOf(ww)
                cleanedText = trimmed.substring(idx + ww.length).trimStart(' ', ',', ':', '-', '.')
                break
            }
        }

        if (foundWakeWord) {
            if (cleanedText.isBlank()) {
                val listeningMsg = getListeningPromptForLanguage(state.value.language)
                updateState { copy(voiceTranscript = "SLen / Meta", assistantMessage = listeningMsg) }
                voiceAssistant.speak(listeningMsg)
            } else {
                updateState { copy(voiceTranscript = cleanedText) }
                sendVoiceNote()
            }
        } else {
            updateState { copy(voiceTranscript = trimmed) }
            sendVoiceNote()
        }
    }

    private fun getListeningPromptForLanguage(lang: String): String {
        return when (lang.split("-")[0].lowercase()) {
            "ta" -> "ஆம், SLen உங்களுக்காகக் கேட்கிறது."
            "te" -> "అవును, SLen వింటోంది."
            "ml" -> "അതെ, SLen കേൾക്കുന്നു."
            "kn" -> "ಹೌದು, SLen ಕೇಳುತ್ತಿದೆ."
            "mr" -> "होय, SLen ऐकत आहे."
            "hi" -> "हाँ, SLen आपकी बात सुन रहा है।"
            "es" -> "¡Sí, SLen te escucha!"
            "fr" -> "Oui, SLen vous écoute !"
            "de" -> "Ja, SLen hört zu!"
            "ja" -> "はい、SLenが聞いています。"
            "zh" -> "是的，SLen正在倾听。"
            else -> "Yes, SLen is listening!"
        }
    }
    private val smartPhoneManager = SmartPhoneManager(context) { jpegBytes ->
        if (state.value.isCameraPaused || state.value.isSessionPaused) return@SmartPhoneManager
        val sessionId = state.value.sessionId ?: return@SmartPhoneManager
        scope.launch {
            runCatching {
                SiteLensApiClient(state.value.backendUrl, httpClient).uploadFrame(sessionId, jpegBytes)
            }.onSuccess { event ->
                updateState { copy(recentEvents = (recentEvents + "Saved image frame to backend").takeLast(15)) }
            }.onFailure { error ->
                android.util.Log.w("BridgeController", "Image frame upload failed: ${error.message}")
            }
        }
    }

    private fun updateState(transform: BridgeUiState.() -> BridgeUiState) {
        _state.update { current -> current.transform() }
    }

    init {
        val initialLang = prefs.getString("selected_language", "en") ?: "en"
        voiceAssistant.setLanguage(initialLang)
        voiceRecognizer.setLanguage(initialLang)
    }

    fun login(username: String, password: String) {
        scope.launch {
            updateState { copy(isBusy = true, errorMessage = null) }
            runCatching {
                withContext(Dispatchers.IO) {
                    val request = Request.Builder()
                        .url(state.value.backendUrl.trimEnd('/') + "/api/auth/login")
                        .post(gson.toJson(mapOf("username" to username, "password" to password)).toRequestBody("application/json".toMediaType()))
                        .build()
                    httpClient.newCall(request).execute().use { 
                        if (!it.isSuccessful) throw IOException("Invalid credentials")
                        gson.fromJson(it.body?.string(), User::class.java)
                    }
                }
            }.onSuccess { user ->
                updateState { copy(currentUser = user, currentScreen = Screen.Home, isBusy = false) }
                fetchSitesAndTasks()
            }.onFailure { error ->
                updateState { copy(errorMessage = error.message, isBusy = false) }
            }
        }
    }

    private fun fetchSitesAndTasks() {
        scope.launch {
            val user = state.value.currentUser ?: return@launch
            runCatching {
                val sites = withContext(Dispatchers.IO) {
                    val request = Request.Builder().url(state.value.backendUrl.trimEnd('/') + "/api/sites").get().build()
                    httpClient.newCall(request).execute().use {
                        val type = object : com.google.gson.reflect.TypeToken<List<Site>>() {}.type
                        gson.fromJson<List<Site>>(it.body?.string(), type)
                    }
                }
                val tasks = withContext(Dispatchers.IO) {
                    val request = Request.Builder().url(state.value.backendUrl.trimEnd('/') + "/api/tasks/${user.id}").get().build()
                    httpClient.newCall(request).execute().use {
                        val type = object : com.google.gson.reflect.TypeToken<List<Task>>() {}.type
                        gson.fromJson<List<Task>>(it.body?.string(), type)
                    }
                }
                Pair(sites, tasks)
            }.onSuccess { (sites, tasks) ->
                updateState { copy(availableSites = sites, currentTasks = tasks) }
            }
        }
    }

    fun selectSite(site: Site) = updateState { copy(selectedSite = site, siteName = site.name ?: "", errorMessage = null) }
    fun updateBackendUrl(url: String) {
        prefs.edit().putString("backend_url", url).apply()
        updateState { copy(backendUrl = url) }
    }
    fun updateLanguage(lang: String) {
        prefs.edit().putString("selected_language", lang).apply()
        updateState { copy(language = lang) }
        voiceAssistant.setLanguage(lang)
        voiceRecognizer.setLanguage(lang)
    }
    fun logout() = updateState { copy(currentUser = null, currentScreen = Screen.Login, selectedTab = 0, errorMessage = null) }
    fun selectTab(index: Int) = updateState { copy(selectedTab = index) }
    fun toggleCamera(paused: Boolean) = updateState { copy(isCameraPaused = paused) }
    fun startVoiceInput() {
        updateState { copy(errorMessage = null) }
        if (state.value.isListening) voiceRecognizer.stopListening()
        else voiceRecognizer.startListening(continuous = true)
    }
    fun toggleSession(paused: Boolean) {
        updateState { copy(isSessionPaused = paused) }
        if (paused) {
            voiceRecognizer.stopListening()
        } else {
            voiceRecognizer.startListening(continuous = true)
        }
    }
    fun updatePiPMode(enabled: Boolean) = updateState { copy(isInPiPMode = enabled) }
    fun toggleSessionTypeDialog(show: Boolean) = updateState { copy(showSessionTypeDialog = show) }
    fun toggleGlassesSetupDialog(show: Boolean) = updateState { 
        if (!show) bleBridge.stopScan()
        copy(showGlassesSetupDialog = show) 
    }
    fun onCameraSurfaceReady(provider: androidx.camera.core.Preview.SurfaceProvider, lifecycleOwner: LifecycleOwner) {
        smartPhoneManager.startCamera(lifecycleOwner, provider)
    }

    fun runAIAssistantTest() {
        scope.launch {
            updateState { copy(recentEvents = (recentEvents + "Starting AI Assistant Test Sequence...").takeLast(10)) }
            sendTelemetry("camera_frame", "Hazard: Oil spill detected.", null, metadata = mapOf("test" to "hazard"))
            delay(4000L)
            sendTelemetry("voice_note", null, "I am setting up safety cones.", metadata = mapOf("test" to "action"))
        }
    }

    fun startSession(type: SessionType, lifecycleOwner: LifecycleOwner? = null) {
        scope.launch {
            val snapshot = state.value
            updateState { copy(isBusy = true, errorMessage = null, sessionType = type, showSessionTypeDialog = false) }
            runCatching {
                SiteLensApiClient(snapshot.backendUrl, httpClient).startSession(
                    SessionCreateRequest(
                        userId = snapshot.currentUser?.id,
                        workerName = snapshot.currentUser?.fullName ?: snapshot.workerName,
                        siteName = snapshot.selectedSite?.name ?: snapshot.siteName,
                        language = snapshot.language,
                        glassesId = snapshot.glassesId.ifBlank { null },
                    )
                )
            }.onSuccess { session ->
                lastSpokenMessage = null
                updateState { copy(sessionId = session.id, currentScreen = Screen.ActiveSession, isBusy = false) }
                connectLiveFeed()
                if (type == SessionType.PHONE && lifecycleOwner != null) {
                    voiceAssistant.speak("Session started. Camera and microphone active.")
                    smartPhoneManager.startCamera(lifecycleOwner)
                    voiceRecognizer.startListening(continuous = true)
                }
            }.onFailure { error ->
                updateState { copy(errorMessage = "Session start failed: ${error.message}", isBusy = false) }
            }
        }
    }

    fun stopSession() {
        terminateSession()
    }

    fun terminateSession() {
        scope.launch {
            val snapshot = state.value
            val sessionId = snapshot.sessionId
            
            // Stop hardware sensors
            smartPhoneManager.stopCamera()
            voiceRecognizer.stopListening()
            
            if (sessionId == null) {
                updateState { copy(currentScreen = Screen.Home, connectionStatus = "Disconnected") }
                return@launch
            }
            updateState { copy(isBusy = true, errorMessage = null, connectionStatus = "Ending Session...") }
            
            // Generate final report before stopping
            runCatching {
                SiteLensApiClient(snapshot.backendUrl, httpClient).generateReport(sessionId)
            }.onSuccess { report ->
                updateState { 
                    copy(
                        sessionSummary = "Session ID: $sessionId\n\n${report.summary}",
                        showSummaryDialog = true,
                        isBusy = false,
                        connectionStatus = "Session Completed"
                    )
                }
                // Now stop the session on server
                runCatching { SiteLensApiClient(snapshot.backendUrl, httpClient).stopSession(sessionId) }
                disconnectLiveFeed(keepSession = true)
            }.onFailure { error ->
                android.util.Log.e("BridgeController", "Final report failed", error)
                // Even if report fails, try to stop session
                runCatching { SiteLensApiClient(snapshot.backendUrl, httpClient).stopSession(sessionId) }
                disconnectLiveFeed()
                updateState { copy(isBusy = false, sessionId = null, connectionStatus = "Disconnected") }
            }
        }
    }

    fun dismissSummaryDialog() {
        updateState { copy(showSummaryDialog = false, sessionId = null, currentScreen = Screen.Home) }
    }

    fun generateReport() {
        scope.launch {
            val snapshot = state.value
            val sessionId = snapshot.sessionId ?: return@launch
            updateState { copy(isBusy = true, errorMessage = null) }
            runCatching {
                SiteLensApiClient(snapshot.backendUrl, httpClient).generateReport(sessionId)
            }.onSuccess { report ->
                updateState {
                    copy(
                        latestSeverity = report.severity,
                        assistantMessage = "Report generated: ${report.summary}",
                        isBusy = false
                    )
                }
            }.onFailure { error ->
                updateState { copy(errorMessage = "Report failed: ${error.message}", isBusy = false) }
            }
        }
    }

    fun connectLiveFeed() {
        scope.launch {
            val snapshot = state.value
            val sessionId = snapshot.sessionId ?: return@launch
            android.util.Log.d("BridgeController", "Connecting to stream at ${snapshot.backendUrl}")
            socket = SiteLensApiClient(snapshot.backendUrl, httpClient).openSocket(
                sessionId = sessionId,
                onText = { message -> scope.launch { handleSocketMessage(message) } },
                onStatus = { status -> 
                    val isStreaming = !status.lowercase().contains("closed") && !status.lowercase().contains("error")
                    updateState { copy(connectionStatus = status, isStreaming = isStreaming, errorMessage = null) } 
                },
                onError = { error -> 
                    android.util.Log.e("BridgeController", "Stream error: $error")
                    updateState { copy(connectionStatus = "Stream error", errorMessage = error, isStreaming = false) } 
                }
            )
        }
    }

    fun reconnectLiveFeed() {
        disconnectLiveFeed(keepSession = true)
        connectLiveFeed()
    }

    fun disconnectLiveFeed(keepSession: Boolean = false) {
        socket?.close(1000, "Disconnect")
        socket = null
        stopDemoStream()
        updateState { copy(isStreaming = false, currentScreen = if (!keepSession) Screen.Home else currentScreen) }
    }

    private fun handleSocketMessage(message: String) {
        val ack = runCatching { gson.fromJson(message, SocketAckResponse::class.java) }.getOrNull()
        if (ack != null) {
            ack.assistantMessage?.let { msg ->
                if (msg.isNotBlank() && msg != lastSpokenMessage) {
                    lastSpokenMessage = msg
                    if (state.value.sessionType == SessionType.GLASSES) {
                        bleBridge.sendToGlasses(msg)
                    } else {
                        voiceAssistant.speak(msg)
                    }
                }
                updateState { copy(assistantMessage = msg) }
            }
            updateState {
                val newLog = ack.assistantMessage?.let { "AI: $it" } ?: ack.event?.let { "Ack ${it.eventType}" } ?: "Update received"
                copy(
                    latestSeverity = ack.report?.severity ?: latestSeverity,
                    recentEvents = (recentEvents + newLog).takeLast(10)
                )
            }
        }
    }

    private fun sendTelemetry(eventType: String, cameraObservation: String?, audioTranscript: String?, source: String = "mobile", metadata: Map<String, Any> = emptyMap()) {
        if (state.value.isSessionPaused && eventType == "camera_frame") return
        
        scope.launch {
            val snapshot = state.value
            val sessionId = snapshot.sessionId ?: return@launch
            
            // Immediate UI feedback for voice notes
            if (eventType == "voice_note") {
                updateState { copy(recentEvents = (recentEvents + "Capturing voice...").takeLast(15)) }
            }

            val socketRequest = GlassesSocketEventRequest(
                eventType = eventType, source = source,
                cameraObservation = cameraObservation, audioTranscript = audioTranscript,
                metadata = metadata
            )
            
            runCatching {
                if (socket != null) {
                    val json = gson.toJson(socketRequest)
                    val sent = socket?.send(json) ?: false
                    if (!sent) throw IOException("Socket write failed")
                } else {
                    SiteLensApiClient(snapshot.backendUrl, httpClient).sendEvent(sessionId, GlassesEventRequest(eventType, source, cameraObservation, audioTranscript, emptyList(), metadata))
                }
            }.onSuccess {
                updateState { copy(recentEvents = (recentEvents + "Sent $eventType").takeLast(15)) }
            }.onFailure { error ->
                android.util.Log.w("BridgeController", "Telemetry socket failed ($eventType): ${error.message}")
                
                // Fallback to HTTP if socket fails
                runCatching {
                    SiteLensApiClient(snapshot.backendUrl, httpClient).sendEvent(sessionId, GlassesEventRequest(eventType, source, cameraObservation, audioTranscript, emptyList(), metadata))
                }.onSuccess {
                    updateState { copy(recentEvents = (recentEvents + "Sent $eventType (HTTP)").takeLast(15)) }
                }.onFailure { fallbackError ->
                    android.util.Log.e("BridgeController", "Telemetry fallback failed ($eventType): ${fallbackError.message}")
                    updateState { copy(recentEvents = (recentEvents + "Dropped $eventType").takeLast(15)) }
                    if (eventType != "camera_frame") {
                        updateState { copy(errorMessage = "Network note: ${fallbackError.message}") }
                    }
                }
            }
        }
    }

    private fun ingestBlePacket(packet: String) {
        throttleLog("BLE: $packet")
        if (state.value.sessionId.isNullOrBlank()) return

        when {
            packet.startsWith("EYES:", ignoreCase = true) -> {
                val obs = packet.substringAfter("EYES:").trim()
                sendTelemetry("camera_frame", obs, null, source = "glasses")
            }
            packet.startsWith("MIC:", ignoreCase = true) -> {
                val transcript = packet.substringAfter("MIC:").trim()
                sendTelemetry("voice_note", null, transcript, source = "glasses")
            }
            else -> {
                sendTelemetry("status_update", packet, null, source = "ble")
            }
        }
    }

    private fun throttleLog(message: String) {
        synchronized(pendingLogs) {
            pendingLogs.add(message)
        }
        if (logThrottleJob == null || logThrottleJob?.isCompleted == true) {
            logThrottleJob = scope.launch {
                delay(500L) // Update UI at most every 500ms
                val batch = synchronized(pendingLogs) {
                    val items = pendingLogs.toList()
                    pendingLogs.clear()
                    items
                }
                if (batch.isNotEmpty()) {
                    updateState {
                        copy(recentEvents = (recentEvents + batch).takeLast(15))
                    }
                }
            }
        }
    }

    fun sendVoiceNote() = sendTelemetry("voice_note", null, state.value.voiceTranscript)
    fun sendHazardAlert() = sendTelemetry("hazard_alert", state.value.cameraObservation, state.value.voiceTranscript)
    fun updateGlassesId(value: String) = updateState { copy(glassesId = value) }
    fun updateBleDeviceFilter(v: String) = bleBridge.updateConfiguration(deviceFilter = v)
    fun updateBleServiceUuid(v: String) = bleBridge.updateConfiguration(serviceUuid = v)
    fun updateBleCharacteristicUuid(v: String) = bleBridge.updateConfiguration(characteristicUuid = v)
    fun startBleScan() = bleBridge.startScan()
    fun stopBleScan() = bleBridge.stopScan()
    fun connectBleDevice(a: String) = bleBridge.connect(a)
    private fun stopDemoStream() { demoJob?.cancel(); demoJob = null }
    override fun close() { disconnectLiveFeed(); bleBridge.close(); voiceAssistant.shutdown(); voiceRecognizer.destroy(); smartPhoneManager.stopCamera(); scope.cancel() }
}

// --- Main Activity ---

class MainActivity : ComponentActivity() {
    private var controller: BridgeController? = null

    override fun onUserLeaveHint() {
        super.onUserLeaveHint()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && controller?.state?.value?.sessionType == SessionType.PHONE) {
            enterPictureInPictureMode(android.app.PictureInPictureParams.Builder().setAspectRatio(android.util.Rational(9, 16)).build())
        }
    }

    override fun onPictureInPictureModeChanged(isInPiP: Boolean, newConfig: android.content.res.Configuration) {
        super.onPictureInPictureModeChanged(isInPiP, newConfig)
        controller?.updatePiPMode(isInPiP)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val blackGoldColorScheme = darkColorScheme(
            primary = Color(0xFFFFD700), onPrimary = Color(0xFF0F172A),
            primaryContainer = Color(0xFF334155), background = Color(0xFF020617),
            surface = Color(0xFF1E293B), onSurface = Color.White
        )

        setContent {
            MaterialTheme(colorScheme = blackGoldColorScheme) {
                GradientBackground {
                    val currentController = remember { BridgeController(BuildConfig.DEFAULT_BACKEND_URL, this@MainActivity.applicationContext) }
                    controller = currentController
                    val state by currentController.state.collectAsStateWithLifecycle()
                    val lo = androidx.lifecycle.compose.LocalLifecycleOwner.current
                    val permLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
                        if (result.values.all { it }) currentController.startSession(SessionType.PHONE, lo)
                    }

                    DisposableEffect(Unit) { onDispose { currentController.close() } }

                    SiteLensScreen(
                        state = state,
                        onLogin = currentController::login,
                        onLogout = currentController::logout,
                        onSiteSelected = currentController::selectSite,
                        onStartSession = { type -> 
                            if (type == SessionType.PHONE) permLauncher.launch(requiredPermissions()) 
                            else {
                                currentController.toggleSessionTypeDialog(false)
                                currentController.toggleGlassesSetupDialog(true)
                            }
                        },
                        onToggleSessionTypeDialog = currentController::toggleSessionTypeDialog,
                        onToggleGlassesSetupDialog = currentController::toggleGlassesSetupDialog,
                        onStopSession = { currentController.terminateSession() },
                        onSendHazardAlert = currentController::sendHazardAlert,
                        onGenerateReport = currentController::generateReport,
                        onRunAITest = currentController::runAIAssistantTest,
                        onCameraSurfaceReady = currentController::onCameraSurfaceReady,
                        onToggleCamera = currentController::toggleCamera,
                        onToggleMic = currentController::startVoiceInput,
                        onToggleSession = currentController::toggleSession,
                        onTabSelected = currentController::selectTab,
                        onBackendUrlChange = currentController::updateBackendUrl,
                        onLanguageChange = currentController::updateLanguage,
                        onUpdateGlassesId = currentController::updateGlassesId,
                        onStartBleScan = currentController::startBleScan,
                        onStopBleScan = currentController::stopBleScan,
                        onConnectBleDevice = currentController::connectBleDevice,
                        onReconnect = currentController::reconnectLiveFeed,
                        onDismissSummary = currentController::dismissSummaryDialog
                    )
                }
            }
        }
    }
}

// --- UI Components ---

@Composable
private fun SiteLensScreen(
    state: BridgeUiState,
    onLogin: (String, String) -> Unit, onLogout: () -> Unit, onSiteSelected: (Site) -> Unit,
    onStartSession: (SessionType) -> Unit, 
    onToggleSessionTypeDialog: (Boolean) -> Unit,
    onToggleGlassesSetupDialog: (Boolean) -> Unit,
    onStopSession: () -> Unit, 
    onSendHazardAlert: () -> Unit, onGenerateReport: () -> Unit, onRunAITest: () -> Unit,
    onCameraSurfaceReady: (androidx.camera.core.Preview.SurfaceProvider, androidx.lifecycle.LifecycleOwner) -> Unit,
    onToggleCamera: (Boolean) -> Unit, onToggleMic: () -> Unit, onToggleSession: (Boolean) -> Unit,
    onTabSelected: (Int) -> Unit, onBackendUrlChange: (String) -> Unit, onLanguageChange: (String) -> Unit,
    onUpdateGlassesId: (String) -> Unit, onStartBleScan: () -> Unit, onStopBleScan: () -> Unit, onConnectBleDevice: (String) -> Unit,
    onReconnect: () -> Unit,
    onDismissSummary: () -> Unit,
) {
    if (state.isInPiPMode) { PiPContent(state.assistantMessage); return }

    when (state.currentScreen) {
        is Screen.Login -> LoginScreen(state.isBusy, state.errorMessage, state.backendUrl, onBackendUrlChange, onLogin)
        is Screen.Home -> HomeScreen(state, onLogout, onSiteSelected, { onToggleSessionTypeDialog(true) }, onTabSelected, onBackendUrlChange, onLanguageChange)
        is Screen.ActiveSession -> ActiveSessionScreen(state, onStopSession, onCameraSurfaceReady, onRunAITest, onGenerateReport, onSendHazardAlert, onToggleCamera, onToggleMic, onToggleSession, onReconnect = onReconnect)
    }

    if (state.showSessionTypeDialog) {
        SessionSelectionDialog({ onToggleSessionTypeDialog(false) }, onStartSession)
    }

    if (state.showGlassesSetupDialog) {
        GlassesSetupDialog(
            state = state,
            onDismiss = { onToggleGlassesSetupDialog(false) },
            onUpdateGlassesId = onUpdateGlassesId,
            onStartScan = onStartBleScan,
            onStopScan = onStopBleScan,
            onConnect = onConnectBleDevice,
            onStartSession = { onStartSession(SessionType.GLASSES) }
        )
    }

    if (state.showSummaryDialog) {
        SummaryDialog(state.sessionSummary ?: "No summary available", onDismissSummary)
    }
}

@Composable
private fun SummaryDialog(summary: String, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Session Summary", fontWeight = FontWeight.Bold) },
        text = { 
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Here is the AI generated summary of your session:", style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.6f))
                Text(summary, color = Color.White)
            }
        },
        confirmButton = { Button(onDismiss) { Text("Dismiss") } },
        containerColor = Color(0xFF1E293B),
        shape = RoundedCornerShape(24.dp)
    )
}

@Composable
private fun LoginScreen(isBusy: Boolean, error: String?, backendUrl: String, onUrlChange: (String) -> Unit, onLogin: (String, String) -> Unit) {
    var u by remember { mutableStateOf("") }; var p by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    
    Column(modifier = Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
        Image(painter = painterResource(id = R.drawable.logo_full), contentDescription = "SiteLens AI Logo", modifier = Modifier.fillMaxWidth().height(160.dp).padding(bottom = 32.dp))
        Text("Your Intelligence partner on site", style = MaterialTheme.typography.bodyMedium, color = Color.White.copy(alpha = 0.6f))
        Spacer(Modifier.height(48.dp))
        GlassCard(Modifier.fillMaxWidth()) {
            Text("Sign In", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Color.White)
            Spacer(Modifier.height(16.dp))
            OutlinedTextField(backendUrl, onUrlChange, label = { Text("Backend URL") }, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp))
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(u, { u = it }, label = { Text("Username") }, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp))
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(
                value = p, 
                onValueChange = { p = it }, 
                label = { Text("Password") }, 
                modifier = Modifier.fillMaxWidth(), 
                visualTransformation = if (passwordVisible) androidx.compose.ui.text.input.VisualTransformation.None else androidx.compose.ui.text.input.PasswordVisualTransformation(),
                trailingIcon = {
                    val image = if (passwordVisible) Icons.Filled.Visibility else Icons.Filled.VisibilityOff
                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                        Icon(imageVector = image, contentDescription = if (passwordVisible) "Hide password" else "Show password", tint = Color.White.copy(alpha = 0.6f))
                    }
                },
                shape = RoundedCornerShape(12.dp)
            )
            Spacer(Modifier.height(24.dp))
            Button({ onLogin(u, p) }, Modifier.fillMaxWidth().height(56.dp), enabled = !isBusy && u.isNotBlank() && p.isNotBlank(), shape = RoundedCornerShape(16.dp)) {
                if (isBusy) CircularProgressIndicator(Modifier.size(24.dp), Color.Black) else Text("Login", fontWeight = FontWeight.Bold)
            }
            error?.let { Spacer(Modifier.height(16.dp)); Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall) }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HomeScreen(state: BridgeUiState, onLogout: () -> Unit, onSiteSelected: (Site) -> Unit, onStart: () -> Unit, onTab: (Int) -> Unit, onUrlChange: (String) -> Unit, onLanguageChange: (String) -> Unit) {
    Scaffold(containerColor = Color.Transparent, 
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Image(painterResource(R.drawable.logo_favicon), null, Modifier.size(48.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("SiteLens AI", fontWeight = FontWeight.Bold, color = Color.White)
                    }
                },
                navigationIcon = {
                    IconButton(onLogout) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                    }
                },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(containerColor = Color.Transparent)
            )
        },
        bottomBar = {
        NavigationBar(containerColor = Color(0xFF0F172A).copy(alpha = 0.8f)) {
            NavigationBarItem(state.selectedTab == 0, { onTab(0) }, { Icon(Icons.Default.Home, null) }, label = { Text("Home") })
            NavigationBarItem(state.selectedTab == 1, { onTab(1) }, { Icon(Icons.Default.Person, null) }, label = { Text("Profile") })
            NavigationBarItem(state.selectedTab == 2, { onTab(2) }, { Icon(Icons.Default.Settings, null) }, label = { Text("Settings") })
        }
    }) { padding ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(padding),
            contentPadding = PaddingValues(24.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            if (state.selectedTab != 1) {
                item {
                    Row(Modifier.fillMaxWidth(), Arrangement.SpaceBetween, Alignment.CenterVertically) {
                        Column { Text("Hi ${state.currentUser?.fullName ?: "Worker"}", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold, color = Color.White); Text("Ready for your shift?", color = Color.White.copy(0.6f)) }
                        IconButton(onLogout, Modifier.background(Color.White.copy(alpha = 0.1f), RoundedCornerShape(12.dp))) { Icon(Icons.AutoMirrored.Filled.ExitToApp, null, tint = Color.White) }
                    }
                }
            }

            if (state.errorMessage != null && state.selectedTab == 0) {
                item {
                    Card(colors = CardDefaults.cardColors(MaterialTheme.colorScheme.errorContainer)) {
                        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Error, null, tint = MaterialTheme.colorScheme.error)
                            Spacer(Modifier.width(12.dp))
                            Text(state.errorMessage, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onErrorContainer)
                        }
                    }
                }
            }

            if (state.selectedTab == 0) {
                item {
                    GlassCard(Modifier.fillMaxWidth()) {
                        Text("Active Site", fontWeight = FontWeight.Bold, color = Color.White)
                        Spacer(modifier = Modifier.height(16.dp))
                        var ex by remember { mutableStateOf(false) }
                        ExposedDropdownMenuBox(ex, { ex = !ex }) {
                            OutlinedTextField(state.selectedSite?.name ?: "Select a site", {}, Modifier.fillMaxWidth().menuAnchor(), readOnly = true, shape = RoundedCornerShape(16.dp), trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(ex) })
                            ExposedDropdownMenu(ex, { ex = false }) {
                                state.availableSites.forEach { site -> DropdownMenuItem(text = { Text(site.name ?: "Unknown Site") }, onClick = { onSiteSelected(site); ex = false }) }
                            }
                        }
                        Spacer(modifier = Modifier.height(24.dp))
                        Button(onStart, Modifier.fillMaxWidth().height(56.dp), enabled = !state.isBusy && state.selectedSite != null, shape = RoundedCornerShape(16.dp)) {
                            if (state.isBusy) CircularProgressIndicator(Modifier.size(24.dp), Color.Black) else Text("Start Session", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }

            if (state.selectedTab == 1) {
                item {
                    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                        Text("Employee Profile", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Color.White)
                        GlassCard(Modifier.fillMaxWidth()) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Box(Modifier.size(64.dp).background(MaterialTheme.colorScheme.primary.copy(alpha = 0.1f), RoundedCornerShape(32.dp)), contentAlignment = Alignment.Center) {
                                    Text(state.currentUser?.fullName?.take(1) ?: "W", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.headlineSmall)
                                }
                                Spacer(Modifier.width(16.dp))
                                Column {
                                    Text(state.currentUser?.fullName ?: "Unknown Worker", fontWeight = FontWeight.Bold, color = Color.White)
                                    Text("Employee ID: ${state.currentUser?.employeeId ?: "N/A"}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary)
                                    Text("Role: ${state.currentUser?.role ?: "Field Staff"}", style = MaterialTheme.typography.labelSmall, color = Color.White.copy(0.4f))
                                }
                            }
                        }
                        
                        Text("Sites Working In", fontWeight = FontWeight.Bold, color = Color.White)
                        if (state.availableSites.isEmpty()) {
                            GlassCard { Text("No active site assignments.", color = Color.White.copy(alpha = 0.4f)) }
                        } else {
                            state.availableSites.forEach { site ->
                                GlassCard { Text(site.name ?: "Unnamed Site", color = Color.White) }
                            }
                        }

                        Text("Work Summaries", fontWeight = FontWeight.Bold, color = Color.White)
                        GlassCard(Modifier.fillMaxWidth()) {
                            Text("Recent session insights will appear here after your shifts.", style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.6f))
                        }
                    }
                }
            }

            if (state.selectedTab == 2) {
                item {
                    GlassCard(Modifier.fillMaxWidth()) {
                        Text("System & AI Language", fontWeight = FontWeight.Bold, color = Color.White)
                        Spacer(Modifier.height(4.dp))
                        Text("Select language for voice interaction, AI analysis & assistant responses.", style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.6f))
                        Spacer(Modifier.height(16.dp))
                        var langExpanded by remember { mutableStateOf(false) }
                        val selectedLangObj = SUPPORTED_LANGUAGES.find { it.code.equals(state.language, ignoreCase = true) } ?: SUPPORTED_LANGUAGES[0]

                        ExposedDropdownMenuBox(langExpanded, { langExpanded = !langExpanded }) {
                            OutlinedTextField(
                                value = "${selectedLangObj.flag}  ${selectedLangObj.name} (${selectedLangObj.nativeName})",
                                onValueChange = {},
                                modifier = Modifier.fillMaxWidth().menuAnchor(),
                                readOnly = true,
                                label = { Text("AI Preferred Language") },
                                shape = RoundedCornerShape(12.dp),
                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(langExpanded) }
                            )
                            ExposedDropdownMenu(langExpanded, { langExpanded = false }) {
                                SUPPORTED_LANGUAGES.forEach { lang ->
                                    DropdownMenuItem(
                                        text = {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                Text(lang.flag, style = MaterialTheme.typography.bodyLarge)
                                                Spacer(Modifier.width(12.dp))
                                                Column {
                                                    Text(lang.name, fontWeight = FontWeight.SemiBold, color = Color.White)
                                                    Text(lang.nativeName, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.6f))
                                                }
                                            }
                                        },
                                        onClick = {
                                            onLanguageChange(lang.code)
                                            langExpanded = false
                                        }
                                    )
                                }
                            }
                        }
                    }
                }
                item {
                    GlassCard(Modifier.fillMaxWidth()) {
                        Text("Backend Server", fontWeight = FontWeight.Bold, color = Color.White)
                        Spacer(Modifier.height(16.dp))
                        OutlinedTextField(state.backendUrl, onUrlChange, label = { Text("Backend URL") }, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp))
                        Spacer(Modifier.height(8.dp))
                        Text("Example: http://192.168.1.10:8000", style = MaterialTheme.typography.labelSmall, color = Color.White.copy(0.4f))
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ActiveSessionScreen(state: BridgeUiState, onDisc: () -> Unit, onSurf: (androidx.camera.core.Preview.SurfaceProvider, LifecycleOwner) -> Unit, onTest: () -> Unit, onRep: () -> Unit, onHaz: () -> Unit, onTogCam: (Boolean) -> Unit, onTogMic: () -> Unit, onTogSes: (Boolean) -> Unit, onReconnect: () -> Unit) {
    Scaffold(containerColor = Color.Transparent, topBar = {
        TopAppBar(
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Image(painterResource(R.drawable.logo_favicon), null, Modifier.size(48.dp))
                    Spacer(Modifier.width(8.dp))
                    Column {
                        Text(state.selectedSite?.name ?: "Session", fontWeight = FontWeight.Bold, color = Color.White)
                        Text(state.connectionStatus, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                    }
                }
            },
            navigationIcon = {
                IconButton(onDisc) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                }
            },
            actions = {
                IconButton({ onTogSes(!state.isSessionPaused) }) { Icon(if (state.isSessionPaused) Icons.Default.PlayArrow else Icons.Default.Pause, null, tint = Color.White) }
                IconButton(onDisc) { Icon(Icons.Default.Stop, null, tint = Color.Red) }
            }, colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent))
    }) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(24.dp),
                verticalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                item { GlassCard { Row(Modifier.fillMaxWidth(), Arrangement.SpaceEvenly) {
                    ControlToggle(if (state.isCameraPaused) Icons.Default.VideocamOff else Icons.Default.Videocam, !state.isCameraPaused, "Video") { onTogCam(!state.isCameraPaused) }
                    ControlToggle(if (state.isListening) Icons.Default.GraphicEq else Icons.Default.Mic, state.isListening, if (state.isListening) "Listening..." else "Tap to Speak") { onTogMic() }
                } } }
                if (state.errorMessage != null) {
                    item {
                        GlassCard(border = BorderStroke(1.dp, Color.Red.copy(alpha = 0.5f))) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.ErrorOutline, null, tint = Color.Red, modifier = Modifier.size(20.dp))
                                Spacer(Modifier.width(8.dp))
                                Text(state.errorMessage, color = Color.Red, style = MaterialTheme.typography.bodySmall, modifier = Modifier.weight(1f))
                                if (state.connectionStatus == "Stream error") {
                                    TextButton(onReconnect) { Text("Reconnect", color = MaterialTheme.colorScheme.primary) }
                                }
                            }
                        }
                    }
                }
                item { ReportCard(state.assistantMessage, state.latestSeverity, state.latestReportAt, state.sessionId) }
                item { TelemetryCard(onHaz, onRep, onTest, state.isBusy) }
                item { EventLogCard(state.recentEvents) }
            }
            if (state.sessionType == SessionType.PHONE && state.sessionId != null && !state.isInPiPMode) {
                val lo = androidx.lifecycle.compose.LocalLifecycleOwner.current; var off by remember { mutableStateOf(Offset.Zero) }
                FloatingCameraPreview(
                    onSurf = { p -> onSurf(p, lo) },
                    isRecording = state.isStreaming && !state.isSessionPaused,
                    isPaused = state.isSessionPaused || state.isCameraPaused,
                    modifier = Modifier.align(Alignment.BottomEnd).offset { IntOffset(off.x.roundToInt(), off.y.roundToInt()) }.padding(16.dp).width(140.dp).height(200.dp).pointerInput(Unit) { detectDragGestures { c, d -> c.consume(); off += d } }
                )
            }
        }
    }
}

@Composable
private fun ControlToggle(icon: ImageVector, active: Boolean, label: String, onClick: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.clickable { onClick() }.padding(8.dp)) {
        Box(Modifier.size(56.dp).background(if (active) MaterialTheme.colorScheme.primary.copy(alpha = 0.2f) else Color.White.copy(alpha = 0.05f), RoundedCornerShape(16.dp)), contentAlignment = Alignment.Center) {
            Icon(icon, null, tint = if (active) MaterialTheme.colorScheme.primary else Color.White.copy(alpha = 0.4f))
        }
        Text(label, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.6f))
    }
}

@Composable private fun PiPContent(msg: String) { Column(Modifier.fillMaxSize().padding(8.dp), Arrangement.Center, Alignment.CenterHorizontally) { Text("AI Assistant", style = MaterialTheme.typography.labelSmall, color = Color(0xFFFFD700)); Text(msg, style = MaterialTheme.typography.bodySmall, color = Color.White) } }

@Composable
private fun FloatingCameraPreview(
    onSurf: (androidx.camera.core.Preview.SurfaceProvider) -> Unit,
    isRecording: Boolean = true,
    isPaused: Boolean = false,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "rec_blink")
    val alpha by if (isRecording && !isPaused) {
        infiniteTransition.animateFloat(
            initialValue = 1.0f,
            targetValue = 0.2f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = 600, easing = LinearEasing),
                repeatMode = RepeatMode.Reverse
            ),
            label = "rec_alpha"
        )
    } else {
        remember { mutableStateOf(1.0f) }
    }

    Card(modifier, elevation = CardDefaults.cardElevation(8.dp), shape = RoundedCornerShape(12.dp), colors = CardDefaults.cardColors(Color.Black)) {
        Box(Modifier.fillMaxSize()) {
            CameraPreview(onSurf, Modifier.fillMaxSize())
            Row(
                Modifier
                    .padding(8.dp)
                    .background(Color.Black.copy(alpha = 0.6f), RoundedCornerShape(8.dp))
                    .padding(horizontal = 6.dp, vertical = 4.dp)
                    .align(Alignment.TopStart),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Canvas(Modifier.size(10.dp)) {
                    drawCircle(color = if (isPaused) Color.Yellow else Color.Red, alpha = alpha)
                }
                Text(
                    text = if (isPaused) "PAUSED" else "REC",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Composable private fun CameraPreview(onSurf: (androidx.camera.core.Preview.SurfaceProvider) -> Unit, modifier: Modifier = Modifier) { AndroidView({ context -> PreviewView(context).apply { implementationMode = PreviewView.ImplementationMode.COMPATIBLE; onSurf(this.surfaceProvider) } }, modifier) }
@Composable private fun EventLogCard(events: List<String>) { GlassCard(Modifier.fillMaxWidth()) { Text("Recent activity", fontWeight = FontWeight.Bold, color = Color.White); events.forEach { e -> Text("• $e", style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.7f)) } } }
@Composable private fun ReportCard(msg: String, sev: String?, at: String?, sid: String?) { GlassCard(Modifier.fillMaxWidth()) { Text("Assistant Guidance", fontWeight = FontWeight.Bold, color = Color.White); Text(msg, color = Color.White); Text("Severity: ${sev ?: "low"}", style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.5f)) } }
@Composable private fun TelemetryCard(onHaz: () -> Unit, genRep: () -> Unit, test: () -> Unit, busy: Boolean) {
    GlassCard(Modifier.fillMaxWidth()) {
        Text("AI Assistant Actions", fontWeight = FontWeight.Bold, color = Color.White)
        Spacer(Modifier.height(16.dp))
        Button(onHaz, Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error), shape = RoundedCornerShape(12.dp)) {
            Icon(Icons.Default.Warning, null, Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
            Text("Force Hazard Alert")
        }
        Spacer(Modifier.height(12.dp))
        Button(genRep, Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary), enabled = !busy, shape = RoundedCornerShape(12.dp)) {
            if (busy) CircularProgressIndicator(Modifier.size(20.dp), Color.White)
            else {
                Icon(Icons.Default.Assessment, null, Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("Generate AI Report")
            }
        }
        Spacer(Modifier.height(12.dp))
        OutlinedButton(test, Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp)) { Text("Run Assistant Test Sequence") }
    }
}

@Composable private fun SessionSelectionDialog(onDismiss: () -> Unit, onSelect: (SessionType) -> Unit) { AlertDialog(onDismissRequest = onDismiss, title = { Text("Start Session") }, text = { Text("Choose mode:") }, confirmButton = { TextButton({ onSelect(SessionType.GLASSES) }) { Text("Glasses") } }, dismissButton = { TextButton({ onSelect(SessionType.PHONE) }) { Text("Phone") } }) }

@Composable
private fun GlassesSetupDialog(
    state: BridgeUiState,
    onDismiss: () -> Unit,
    onUpdateGlassesId: (String) -> Unit,
    onStartScan: () -> Unit,
    onStopScan: () -> Unit,
    onConnect: (String) -> Unit,
    onStartSession: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Glasses Setup", fontWeight = FontWeight.Bold) },
        text = {
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                OutlinedTextField(
                    value = state.glassesId,
                    onValueChange = onUpdateGlassesId,
                    label = { Text("Manual Glass ID") },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp)
                )
                
                HorizontalDivider(color = Color.White.copy(alpha = 0.1f))
                
                Text("Nearby Devices (Bluetooth)", style = MaterialTheme.typography.titleSmall, color = Color.White)
                
                if (state.bleState.isScanning) {
                    CircularProgressIndicator(Modifier.size(24.dp).align(Alignment.CenterHorizontally))
                    Text("Scanning...", style = MaterialTheme.typography.labelSmall, modifier = Modifier.align(Alignment.CenterHorizontally))
                    Button(onStopScan, Modifier.fillMaxWidth()) { Text("Stop Scan") }
                } else {
                    Button(onStartScan, Modifier.fillMaxWidth()) { Text("Find Nearby Devices") }
                }
                
                LazyColumn(Modifier.heightIn(max = 200.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(state.bleState.discoveredDevices.size) { index ->
                        val device = state.bleState.discoveredDevices[index]
                        val isSelected = state.bleState.selectedAddress == device.address
                        Card(
                            onClick = { onConnect(device.address) },
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(
                                containerColor = if (isSelected) MaterialTheme.colorScheme.primaryContainer else Color.White.copy(alpha = 0.05f)
                            )
                        ) {
                            Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(device.name, fontWeight = FontWeight.Bold, color = Color.White)
                                    Text(device.address, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.5f))
                                }
                                if (isSelected && state.bleState.isConnected) {
                                    Icon(Icons.Default.BluetoothConnected, null, tint = MaterialTheme.colorScheme.primary)
                                } else if (isSelected) {
                                    CircularProgressIndicator(Modifier.size(16.dp))
                                }
                            }
                        }
                    }
                }
                
                state.bleState.lastError?.let {
                    Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelSmall)
                }
                
                Text(state.bleState.connectionStatus, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
            }
        },
        confirmButton = {
            Button(onStartSession, enabled = state.glassesId.isNotBlank() || state.bleState.isConnected) {
                Text("Start Session")
            }
        },
        dismissButton = {
            TextButton(onDismiss) { Text("Cancel") }
        }
    )
}
@Composable private fun GradientBackground(content: @Composable () -> Unit) { Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color(0xFF0F172A), Color(0xFF020617))))) { content() } }
@Composable private fun GlassCard(modifier: Modifier = Modifier, border: BorderStroke? = null, content: @Composable ColumnScope.() -> Unit) { Card(modifier.graphicsLayer(alpha = 0.95f), shape = RoundedCornerShape(24.dp), colors = CardDefaults.cardColors(Color(0xFF1E293B).copy(alpha = 0.7f)), border = border ?: BorderStroke(1.dp, Color.White.copy(alpha = 0.1f))) { Column(Modifier.padding(16.dp), content = content) } }

private fun requiredPermissions() = mutableListOf(Manifest.permission.CAMERA, Manifest.permission.RECORD_AUDIO).apply { if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) { add(Manifest.permission.BLUETOOTH_SCAN); add(Manifest.permission.BLUETOOTH_CONNECT) } else { add(Manifest.permission.ACCESS_FINE_LOCATION) } }.toTypedArray()
