package com.sitelens.ai

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.Build
import java.io.Closeable
import java.nio.charset.Charset
import java.util.UUID

private val clientConfigUuid: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")


data class BleDeviceItem(
    val address: String,
    val name: String,
    val rssi: Int,
)


data class BleBridgeState(
    val connectionStatus: String = "Bluetooth idle",
    val isScanning: Boolean = false,
    val isConnected: Boolean = false,
    val selectedAddress: String? = null,
    val deviceFilter: String = "Meta",
    val serviceUuid: String = "0000ffe0-0000-1000-8000-00805f9b34fb",
    val characteristicUuid: String = "0000ffe1-0000-1000-8000-00805f9b34fb",
    val discoveredDevices: List<BleDeviceItem> = emptyList(),
    val lastPacket: String? = null,
    val lastError: String? = null,
)


class BleGlassBridge(
    context: Context,
    private val onStateChanged: (BleBridgeState) -> Unit,
    private val onPacketReceived: (String) -> Unit,
) : Closeable {
    private val appContext = context.applicationContext
    private val bluetoothManager = appContext.getSystemService(BluetoothManager::class.java)
    private val adapter: BluetoothAdapter? = bluetoothManager?.adapter
    private val scanner = adapter?.bluetoothLeScanner

    private var state = BleBridgeState()
    private var gatt: BluetoothGatt? = null
    private var scanCallback: ScanCallback? = null

    init {
        emitState()
    }

    @Suppress("unused")
    fun currentState(): BleBridgeState = state

    fun updateConfiguration(
        deviceFilter: String? = null,
        serviceUuid: String? = null,
        characteristicUuid: String? = null,
    ) {
        updateState {
            copy(
                deviceFilter = deviceFilter ?: this.deviceFilter,
                serviceUuid = serviceUuid ?: this.serviceUuid,
                characteristicUuid = characteristicUuid ?: this.characteristicUuid,
            )
        }
    }

    @SuppressLint("MissingPermission")
    fun startScan() {
        val currentAdapter = adapter
        val currentScanner = scanner
        if (currentAdapter == null || currentScanner == null) {
            updateState {
                copy(
                    connectionStatus = "Bluetooth unavailable on this device",
                    lastError = "No Bluetooth adapter found",
                    isScanning = false,
                )
            }
            return
        }

        stopScan()
        updateState {
            copy(
                discoveredDevices = emptyList(),
                isScanning = true,
                connectionStatus = "Scanning for glasses...",
                lastError = null,
            )
        }

        scanCallback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                registerDevice(result.device, result.rssi)
            }

            override fun onBatchScanResults(results: MutableList<ScanResult>) {
                results.forEach { registerDevice(it.device, it.rssi) }
            }

            override fun onScanFailed(errorCode: Int) {
                updateState {
                    copy(
                        isScanning = false,
                        connectionStatus = "Scan failed",
                        lastError = "Bluetooth scan failed with code $errorCode",
                    )
                }
            }
        }

        currentScanner.startScan(null, ScanSettings.Builder().build(), scanCallback)
    }

    @SuppressLint("MissingPermission")
    fun stopScan() {
        val currentScanner = scanner
        val callback = scanCallback
        if (currentScanner != null && callback != null) {
            currentScanner.stopScan(callback)
        }
        scanCallback = null
        updateState {
            copy(
                isScanning = false,
                connectionStatus = if (isConnected) connectionStatus else "Bluetooth idle",
            )
        }
    }

    @SuppressLint("MissingPermission")
    fun connect(address: String) {
        val currentAdapter = adapter
        if (currentAdapter == null) {
            updateState {
                copy(
                    connectionStatus = "Bluetooth unavailable on this device",
                    lastError = "No Bluetooth adapter found",
                )
            }
            return
        }

        val device = runCatching { currentAdapter.getRemoteDevice(address) }.getOrNull()
        if (device == null) {
            updateState {
                copy(
                    connectionStatus = "Device not found",
                    lastError = "No Bluetooth device found for address $address",
                )
            }
            return
        }

        disconnectInternal(keepScanState = true)
        updateState {
            copy(
                connectionStatus = "Connecting to ${device.safeName}",
                selectedAddress = address,
                lastError = null,
            )
        }

        gatt = device.connectGatt(appContext, false, object : BluetoothGattCallback() {
            override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
                if (status != BluetoothGatt.GATT_SUCCESS) {
                    updateState {
                        copy(
                            connectionStatus = "GATT error: $status",
                            isConnected = false,
                            lastError = "Connection failed with status $status",
                        )
                    }
                    disconnectInternal(keepScanState = false)
                    return
                }

                when (newState) {
                    BluetoothProfile.STATE_CONNECTED -> {
                        updateState {
                            copy(
                                connectionStatus = "Connected to ${device.safeName}",
                                isConnected = true,
                                lastError = null,
                            )
                        }
                        gatt.discoverServices()
                    }

                    BluetoothProfile.STATE_DISCONNECTED -> {
                        updateState {
                            copy(
                                connectionStatus = "Bluetooth disconnected",
                                isConnected = false,
                            )
                        }
                        disconnectInternal(keepScanState = false)
                    }
                }
            }

            override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
                if (status != BluetoothGatt.GATT_SUCCESS) {
                    updateState {
                        copy(
                            connectionStatus = "Service discovery failed",
                            lastError = "Unable to discover glasses services (status $status)",
                        )
                    }
                    return
                }

                val service = runCatching { gatt.getService(UUID.fromString(state.serviceUuid)) }.getOrNull()
                val characteristic = service?.getCharacteristic(UUID.fromString(state.characteristicUuid))
                if (service == null || characteristic == null) {
                    updateState {
                        copy(
                            connectionStatus = "Glasses characteristic missing",
                            lastError = "Service or characteristic not found",
                        )
                    }
                    return
                }

                gatt.setCharacteristicNotification(characteristic, true)
                characteristic.getDescriptor(clientConfigUuid)?.let { descriptor ->
                    val value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        gatt.writeDescriptor(descriptor, value)
                    } else {
                        @Suppress("DEPRECATION")
                        descriptor.value = value
                        @Suppress("DEPRECATION")
                        gatt.writeDescriptor(descriptor)
                    }
                }

                updateState {
                    copy(
                        connectionStatus = "Telemetry streaming from glasses",
                        isConnected = true,
                        lastError = null,
                    )
                }
            }

            @Deprecated("Use the version with value parameter")
            override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
                @Suppress("DEPRECATION")
                emitPacket(characteristic.value)
            }

            override fun onCharacteristicChanged(
                gatt: BluetoothGatt,
                characteristic: BluetoothGattCharacteristic,
                value: ByteArray,
            ) {
                emitPacket(value)
            }
        })
    }

    @SuppressLint("MissingPermission")
    fun sendToGlasses(data: String) {
        val currentGatt = gatt ?: return
        val service = currentGatt.getService(UUID.fromString(state.serviceUuid))
        val characteristic = service?.getCharacteristic(UUID.fromString(state.characteristicUuid)) ?: return
        
        val bytes = data.toByteArray(Charset.forName("UTF-8"))
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            currentGatt.writeCharacteristic(characteristic, bytes, BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)
        } else {
            @Suppress("DEPRECATION")
            characteristic.value = bytes
            @Suppress("DEPRECATION")
            currentGatt.writeCharacteristic(characteristic)
        }
    }

    @SuppressLint("MissingPermission")
    fun disconnect() {
        disconnectInternal(keepScanState = false)
        updateState {
            copy(
                isConnected = false,
                selectedAddress = null,
                connectionStatus = "Bluetooth idle",
            )
        }
    }

    private fun registerDevice(device: BluetoothDevice, rssi: Int) {
        val currentFilter = state.deviceFilter.trim().lowercase()
        val deviceName = device.safeName
        if (currentFilter.isNotBlank() && !deviceName.lowercase().contains(currentFilter)) {
            return
        }

        val nextDevices = (state.discoveredDevices + BleDeviceItem(device.address, deviceName, rssi))
            .distinctBy { it.address }
            .sortedByDescending { it.rssi }
        updateState {
            copy(
                discoveredDevices = nextDevices,
                connectionStatus = if (isScanning) "Scanning: ${nextDevices.size} device(s) found" else connectionStatus,
            )
        }
    }

    private fun emitPacket(bytes: ByteArray?) {
        val text = bytes?.let { String(it, Charset.forName("UTF-8")) }?.trim().orEmpty()
        if (text.isBlank()) {
            return
        }
        onPacketReceived(text)
        updateState {
            copy(
                lastPacket = text,
                connectionStatus = "Glasses telemetry received",
            )
        }
    }

    private fun disconnectInternal(keepScanState: Boolean) {
        scanCallback?.let { callback ->
            scanner?.stopScan(callback)
        }
        scanCallback = null
        gatt?.disconnect()
        gatt?.close()
        gatt = null
        updateState {
            copy(
                isScanning = if (keepScanState) isScanning else false,
                isConnected = false,
            )
        }
    }

    private fun updateState(transform: BleBridgeState.() -> BleBridgeState) {
        state = state.transform()
        emitState()
    }

    private fun emitState() {
        onStateChanged(state)
    }

    override fun close() {
        disconnectInternal(keepScanState = false)
    }
}

private val BluetoothDevice.safeName: String
    @SuppressLint("MissingPermission")
    get() = name?.takeIf { it.isNotBlank() } ?: address
