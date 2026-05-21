package com.orbanforest.alaba.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.orbanforest.alaba.data.api.dto.DeviceDto
import com.orbanforest.alaba.data.auth.AlabaError
import com.orbanforest.alaba.data.auth.AuthEvent
import com.orbanforest.alaba.data.auth.AuthEventBus
import com.orbanforest.alaba.data.auth.TokenStore
import com.orbanforest.alaba.data.device.DevicesRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DevicesUiState(
    val devices: List<DeviceDto> = emptyList(),
    val cap: Int = 2,
    val activeCount: Int = 0,
    val cooldownUnlockAt: String? = null,
    val loading: Boolean = true,
    val error: String? = null,
    val confirmDeactivateId: String? = null,
)

@HiltViewModel
class DevicesViewModel @Inject constructor(
    private val devicesRepository: DevicesRepository,
    private val authEventBus: AuthEventBus,
    private val tokenStore: TokenStore,
) : ViewModel() {
    private val _state = MutableStateFlow(DevicesUiState())
    val state: StateFlow<DevicesUiState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            val r = devicesRepository.list()
            r.fold(
                onSuccess = { body ->
                    _state.value = DevicesUiState(
                        devices = body.devices,
                        cap = body.cap,
                        activeCount = body.activeCount,
                        cooldownUnlockAt = body.cooldownUnlockAt,
                        loading = false,
                    )
                },
                onFailure = { t ->
                    _state.value = _state.value.copy(loading = false, error = t.message ?: "Error")
                },
            )
        }
    }

    fun askConfirmDeactivate(deviceId: String) {
        _state.value = _state.value.copy(confirmDeactivateId = deviceId)
    }

    fun cancelConfirm() {
        _state.value = _state.value.copy(confirmDeactivateId = null)
    }

    fun confirmDeactivate(currentUserDeviceId: String?) {
        val id = _state.value.confirmDeactivateId ?: return
        viewModelScope.launch {
            val r = devicesRepository.deactivate(id)
            r.fold(
                onSuccess = {
                    if (id == currentUserDeviceId) {
                        // Trigger global "this device signed out" flow
                        tokenStore.clear()
                        authEventBus.emit(AuthEvent.DeviceDeactivated)
                    } else {
                        // Just refresh the list
                        _state.value = _state.value.copy(confirmDeactivateId = null)
                        load()
                    }
                },
                onFailure = { t ->
                    val msg = when (t) {
                        is AlabaError.CooldownActive -> "Cooldown active. Try again later."
                        is AlabaError.DeviceNotFound -> "Device not found."
                        else -> t.message ?: "Error"
                    }
                    _state.value = _state.value.copy(confirmDeactivateId = null, error = msg)
                },
            )
        }
    }
}
