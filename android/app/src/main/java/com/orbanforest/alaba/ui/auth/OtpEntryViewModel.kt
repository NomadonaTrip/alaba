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

sealed class OtpEntryUiState {
    data class Ready(val codeInput: String = "", val errorMessage: String? = null) : OtpEntryUiState()
    data object Submitting : OtpEntryUiState()
}

sealed class OtpEntryEvent {
    data object VerifiedSignedIn : OtpEntryEvent()
    data class DeviceCapReached(
        val activeDevices: List<ActiveDeviceSummary>,
        val verifyTicket: String,
    ) : OtpEntryEvent()
}

@HiltViewModel
class OtpEntryViewModel @Inject constructor(
    private val authRepository: AuthRepository,
) : ViewModel() {
    private val _state = MutableStateFlow<OtpEntryUiState>(OtpEntryUiState.Ready())
    val state: StateFlow<OtpEntryUiState> = _state.asStateFlow()

    private val _events = Channel<OtpEntryEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    fun onCodeChanged(s: String) {
        _state.value = OtpEntryUiState.Ready(codeInput = s)
        if (s.length == 6) submit("")
    }

    fun submit(phone: String) {
        val current = (_state.value as? OtpEntryUiState.Ready) ?: return
        if (current.codeInput.length != 6) {
            _state.value = current.copy(errorMessage = "Enter all 6 digits.")
            return
        }
        // The phone is held by the screen and passed in to submit when the
        // automatic 6-digit submission fires. Use the screen-provided phone
        // (PhoneEntry sets it via nav args).
        _state.value = OtpEntryUiState.Submitting
        viewModelScope.launch {
            val result = authRepository.verifyOtp(phone, current.codeInput)
            handleResult(result, current.codeInput)
        }
    }

    private suspend fun handleResult(result: AuthResult, code: String) {
        when (result) {
            is AuthResult.Success -> {
                _events.send(OtpEntryEvent.VerifiedSignedIn)
            }
            is AuthResult.Failure -> when (val err = result.error) {
                is AlabaError.DeviceCapReached -> {
                    _events.send(OtpEntryEvent.DeviceCapReached(err.activeDevices, err.verifyTicket))
                }
                is AlabaError.InvalidCodeWithAttempts -> {
                    _state.value = OtpEntryUiState.Ready(
                        codeInput = code,
                        errorMessage = "Wrong code. ${err.attemptsRemaining} attempts left.",
                    )
                }
                AlabaError.CodeExpired -> {
                    _state.value = OtpEntryUiState.Ready(codeInput = code, errorMessage = "Code expired.")
                }
                AlabaError.AttemptsExhausted -> {
                    _state.value = OtpEntryUiState.Ready(codeInput = code, errorMessage = "Too many attempts. Request a new code.")
                }
                else -> {
                    _state.value = OtpEntryUiState.Ready(codeInput = code, errorMessage = "Something went wrong. Try again.")
                }
            }
        }
    }
}
