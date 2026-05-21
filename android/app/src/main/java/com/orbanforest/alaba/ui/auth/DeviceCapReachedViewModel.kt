package com.orbanforest.alaba.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.data.auth.AlabaError
import com.orbanforest.alaba.data.auth.AuthRepository
import com.orbanforest.alaba.data.auth.AuthResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DeviceCapState(
    val devices: List<ActiveDeviceSummary>,
    val selectedDeviceId: String? = null,
    val errorMessage: String? = null,
    val submitting: Boolean = false,
)

sealed class DeviceCapEvent {
    data object SignedIn : DeviceCapEvent()
    data object Cancel : DeviceCapEvent()
}

@HiltViewModel
class DeviceCapReachedViewModel @Inject constructor(
    private val authRepository: AuthRepository,
) : ViewModel() {
    private val _state = MutableStateFlow<DeviceCapState?>(null)
    val state: StateFlow<DeviceCapState?> = _state.asStateFlow()

    private val _events = Channel<DeviceCapEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    private var phone: String = ""
    private var ticket: String = ""

    fun initialize(devices: List<ActiveDeviceSummary>, ticket: String, phone: String) {
        this.phone = phone
        this.ticket = ticket
        _state.value = DeviceCapState(devices = devices)
    }

    fun selectDevice(id: String) {
        val current = _state.value ?: return
        _state.value = current.copy(selectedDeviceId = id, errorMessage = null)
    }

    fun confirm() {
        val current = _state.value ?: return
        val deviceId = current.selectedDeviceId ?: return
        _state.value = current.copy(submitting = true)
        viewModelScope.launch {
            val result = authRepository.verifyOtpWithTicket(phone, ticket, deviceId)
            when (result) {
                is AuthResult.Success -> _events.send(DeviceCapEvent.SignedIn)
                is AuthResult.Failure -> {
                    val msg = when (result.error) {
                        is AlabaError.InvalidVerifyTicket -> "Session expired. Request a new code."
                        is AlabaError.CooldownActive -> "You're in a 90-day cooldown. Try again later."
                        is AlabaError.NetworkError -> "Network error. Try again."
                        else -> "Something went wrong. Try again."
                    }
                    _state.value = current.copy(submitting = false, errorMessage = msg)
                }
            }
        }
    }

    fun cancel() {
        viewModelScope.launch { _events.send(DeviceCapEvent.Cancel) }
    }
}
