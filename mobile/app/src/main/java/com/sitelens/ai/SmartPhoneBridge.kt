package com.sitelens.ai

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.graphics.Rect
import android.graphics.YuvImage
import android.graphics.ImageFormat
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.util.Base64
import android.util.Log
import android.util.Size
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class SmartPhoneManager(
    private val context: Context,
    private val onFrameCaptured: (ByteArray) -> Unit,
) {
    private var cameraExecutor: ExecutorService = Executors.newSingleThreadExecutor()
    private var imageAnalysis: ImageAnalysis? = null
    private var preview: Preview? = null
    private var lastFrameTime = 0L

    fun startCamera(lifecycleOwner: LifecycleOwner, surfaceProvider: Preview.SurfaceProvider? = null) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)

        cameraProviderFuture.addListener(
            {
                val cameraProvider: ProcessCameraProvider = cameraProviderFuture.get()

                imageAnalysis = ImageAnalysis.Builder()
                    .setTargetResolution(Size(640, 480))
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()

                imageAnalysis?.setAnalyzer(cameraExecutor) { imageProxy ->
                    val currentTime = System.currentTimeMillis()
                    if ((currentTime - lastFrameTime) > 3000) { // Every 3 seconds
                        lastFrameTime = currentTime
                        try {
                            processImage(imageProxy)
                        } catch (e: Exception) {
                            Log.e("SmartPhoneManager", "Error processing image", e)
                            imageProxy.close()
                        }
                    } else {
                        imageProxy.close()
                    }
                }

                val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

                val useCases = mutableListOf<androidx.camera.core.UseCase>(imageAnalysis!!)

                if (surfaceProvider != null) {
                    preview = Preview.Builder()
                        .setTargetResolution(Size(640, 480))
                        .build().also {
                            it.setSurfaceProvider(surfaceProvider)
                        }
                    useCases.add(preview!!)
                }

                try {
                    cameraProvider.unbindAll()
                    cameraProvider.bindToLifecycle(
                        lifecycleOwner, cameraSelector, *useCases.toTypedArray(),
                    )
                } catch (exc: Exception) {
                    Log.e("SmartPhoneManager", "Use case binding failed", exc)
                }

            },
            ContextCompat.getMainExecutor(context),
        )
    }

    private fun processImage(imageProxy: ImageProxy) {
        try {
            val bitmap = imageProxy.toBitmap()
            val outputStream = ByteArrayOutputStream()
            val scaled = if (bitmap.width > 640) {
                val aspect = bitmap.height.toFloat() / bitmap.width.toFloat()
                Bitmap.createScaledBitmap(bitmap, 640, (640 * aspect).toInt(), true)
            } else bitmap
            scaled.compress(Bitmap.CompressFormat.JPEG, 60, outputStream)
            val jpegBytes = outputStream.toByteArray()
            onFrameCaptured(jpegBytes)
        } catch (e: Exception) {
            Log.e("SmartPhoneManager", "Error processing image", e)
        } finally {
            imageProxy.close()
        }
    }

    private fun bitmapToBase64(bitmap: Bitmap): String {
        val outputStream = ByteArrayOutputStream()
        val scaled = if (bitmap.width > 480) {
            val aspect = bitmap.height.toFloat() / bitmap.width.toFloat()
            Bitmap.createScaledBitmap(bitmap, 480, (480 * aspect).toInt(), true)
        } else bitmap
        scaled.compress(Bitmap.CompressFormat.JPEG, 40, outputStream)
        val byteArray = outputStream.toByteArray()
        return Base64.encodeToString(byteArray, Base64.NO_WRAP)
    }

    fun stopCamera() {
        cameraExecutor.shutdown()
    }
}

fun getLanguageTag(tag: String): String {
    val clean = tag.trim().lowercase()
    return when (clean) {
        "ta", "ta-in", "tamil" -> "ta-IN"
        "te", "te-in", "telugu" -> "te-IN"
        "ml", "ml-in", "malayalam" -> "ml-IN"
        "kn", "kn-in", "kannada" -> "kn-IN"
        "mr", "mr-in", "marathi" -> "mr-IN"
        "hi", "hi-in", "hindi" -> "hi-IN"
        "bn", "bn-in", "bengali" -> "bn-IN"
        "gu", "gu-in", "gujarati" -> "gu-IN"
        "pa", "pa-in", "punjabi" -> "pa-IN"
        "or", "or-in", "odia" -> "or-IN"
        "es", "es-es", "spanish" -> "es-ES"
        "fr", "fr-fr", "french" -> "fr-FR"
        "de", "de-de", "german" -> "de-DE"
        "ja", "ja-jp", "japanese" -> "ja-JP"
        "zh", "zh-cn", "chinese" -> "zh-CN"
        "ar", "ar-sa", "arabic" -> "ar-SA"
        "pt", "pt-br", "portuguese" -> "pt-BR"
        "it", "it-it", "italian" -> "it-IT"
        "ru", "ru-ru", "russian" -> "ru-RU"
        "ko", "ko-kr", "korean" -> "ko-KR"
        "en", "en-us", "english" -> "en-US"
        else -> tag.replace('_', '-')
    }
}

fun getLocaleForLanguageTag(tag: String): Locale {
    val bcp = getLanguageTag(tag)
    val parts = bcp.split("-")
    return if (parts.size >= 2) {
        Locale(parts[0], parts[1])
    } else if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
        Locale.forLanguageTag(bcp)
    } else {
        Locale(bcp)
    }
}

class VoiceAssistantManager(context: Context) : TextToSpeech.OnInitListener {
    private var tts: TextToSpeech? = TextToSpeech(context, this)
    private var isReady = false
    private var currentLanguageTag: String = "en"
    private var pendingSpeech: String? = null

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isReady = true
            setLanguage(currentLanguageTag)
            pendingSpeech?.let {
                speak(it)
                pendingSpeech = null
            }
        } else {
            Log.e("TTS", "Initialization failed status=$status")
        }
    }

    fun setLanguage(languageTag: String) {
        currentLanguageTag = languageTag
        if (isReady) {
            val locale = getLocaleForLanguageTag(languageTag)
            val result = tts?.setLanguage(locale)
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                Log.w("TTS", "Language $languageTag ($locale) missing or unsupported, falling back to US")
                tts?.setLanguage(Locale.US)
            }
        }
    }

    fun speak(text: String) {
        if (text.isNotBlank()) {
            if (isReady) {
                try {
                    val params = Bundle()
                    params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f)
                    tts?.speak(text, TextToSpeech.QUEUE_FLUSH, params, "utterance_${System.currentTimeMillis()}")
                } catch (e: Exception) {
                    Log.e("TTS", "Speak failed", e)
                }
            } else {
                pendingSpeech = text
            }
        }
    }

    fun shutdown() {
        tts?.stop()
        tts?.shutdown()
    }
}

class VoiceRecognitionManager(
    private val context: Context,
    private val onResult: (String) -> Unit,
    private val onStateChange: (Boolean) -> Unit,
    private val onError: (String) -> Unit
) {
    private var speechRecognizer: SpeechRecognizer? = null
    private var isContinuous: Boolean = false
    private var currentLanguageTag: String = "en"
    private val mainHandler = android.os.Handler(android.os.Looper.getMainLooper())

    private fun createRecognizerIntent(): Intent {
        val bcpTag = getLanguageTag(currentLanguageTag)
        return Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, bcpTag)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, bcpTag)
            putExtra("android.speech.extra.EXTRA_ADDITIONAL_LANGUAGES", arrayOf(bcpTag))
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
        }
    }

    fun setLanguage(languageTag: String) {
        currentLanguageTag = languageTag
        Log.d("VoiceRec", "Language updated to $languageTag (${getLanguageTag(languageTag)})")
    }

    private fun ensureRecognizerCreated(): SpeechRecognizer {
        if (speechRecognizer != null) {
            try { speechRecognizer?.destroy() } catch (e: Exception) { Log.w("VoiceRec", "Destroy failed", e) }
        }
        return SpeechRecognizer.createSpeechRecognizer(context).apply {
            setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) { 
                    Log.d("VoiceRec", "Ready for speech (lang=$currentLanguageTag, tag=${getLanguageTag(currentLanguageTag)})")
                    onStateChange(true) 
                }
                override fun onBeginningOfSpeech() {
                    Log.d("VoiceRec", "Beginning of speech")
                }
                override fun onRmsChanged(rmsdB: Float) {}
                override fun onBufferReceived(buffer: ByteArray?) {}
                override fun onEndOfSpeech() { 
                    Log.d("VoiceRec", "End of speech")
                }
                override fun onError(error: Int) { 
                    val message = when (error) {
                        SpeechRecognizer.ERROR_NO_MATCH -> "No speech detected."
                        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Speech timeout."
                        SpeechRecognizer.ERROR_NETWORK -> "Network error. Check connection."
                        SpeechRecognizer.ERROR_AUDIO -> "Audio recording error."
                        SpeechRecognizer.ERROR_CLIENT -> "Speech engine busy or reset."
                        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission required."
                        SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout."
                        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Speech engine busy."
                        SpeechRecognizer.ERROR_SERVER -> "Speech server error."
                        else -> "Speech recognition code ($error)."
                    }
                    Log.d("VoiceRec", "Speech engine code: $error - $message")
                    
                    val isTransient = error == SpeechRecognizer.ERROR_NO_MATCH ||
                                      error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT ||
                                      error == SpeechRecognizer.ERROR_CLIENT ||
                                      error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY
                    if (!isTransient) {
                        onError(message)
                    }
                    onStateChange(false)
                    if (isContinuous) {
                        mainHandler.postDelayed({ restartListeningInternal() }, 1200L)
                    }
                }
                override fun onResults(results: Bundle?) {
                    val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    if (!matches.isNullOrEmpty()) {
                        Log.d("VoiceRec", "Result: ${matches[0]}")
                        onResult(matches[0])
                    } else {
                        Log.d("VoiceRec", "Empty speech results bundle")
                    }
                    onStateChange(false)
                    if (isContinuous) {
                        mainHandler.postDelayed({ restartListeningInternal() }, 600L)
                    }
                }
                override fun onPartialResults(partialResults: Bundle?) {}
                override fun onEvent(eventType: Int, params: Bundle?) {}
            })
        }
    }

    private fun restartListeningInternal() {
        if (!isContinuous) return
        try {
            speechRecognizer = ensureRecognizerCreated()
            speechRecognizer?.startListening(createRecognizerIntent())
        } catch (e: Exception) {
            Log.e("VoiceRec", "Restart listening failed", e)
        }
    }

    fun startListening(continuous: Boolean = false) {
        isContinuous = continuous
        if (androidx.core.content.PermissionChecker.checkSelfPermission(context, android.Manifest.permission.RECORD_AUDIO) != androidx.core.content.PermissionChecker.PERMISSION_GRANTED) {
            onError("Microphone permission not granted")
            return
        }
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            Log.e("VoiceRec", "Speech recognition not available")
            onError("Speech recognition not available on this device")
            return
        }
        
        // Vibration feedback
        val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? android.os.Vibrator
        vibrator?.let {
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                it.vibrate(android.os.VibrationEffect.createOneShot(50, android.os.VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                it.vibrate(50)
            }
        }

        try {
            speechRecognizer = ensureRecognizerCreated()
            val intent = createRecognizerIntent()
            Log.d("VoiceRec", "Starting listening (continuous=$continuous, lang=$currentLanguageTag, tag=${getLanguageTag(currentLanguageTag)})...")
            speechRecognizer?.startListening(intent)
        } catch (e: Exception) {
            Log.e("VoiceRec", "Start listening failed", e)
            onError("Voice listening start failed: ${e.message}")
        }
    }

    fun stopListening() {
        isContinuous = false
        mainHandler.removeCallbacksAndMessages(null)
        Log.d("VoiceRec", "Stopping listening...")
        try {
            speechRecognizer?.stopListening()
        } catch (e: Exception) {
            Log.w("VoiceRec", "Stop listening error", e)
        }
        onStateChange(false)
    }

    fun destroy() {
        isContinuous = false
        mainHandler.removeCallbacksAndMessages(null)
        try {
            speechRecognizer?.destroy()
        } catch (e: Exception) {}
        speechRecognizer = null
    }
}
