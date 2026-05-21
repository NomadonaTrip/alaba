package com.orbanforest.alaba.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.orbanforest.alaba.data.auth.AlabaError
import com.orbanforest.alaba.data.auth.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class PhoneEntryUiState {
    data class Ready(val phoneInput: String = "", val errorMessage: String? = null) : PhoneEntryUiState()
    data object Submitting : PhoneEntryUiState()
}

sealed class PhoneEntryEvent {
    data class CodeSent(val phone: String) : PhoneEntryEvent()
}

@HiltViewModel
class PhoneEntryViewModel @Inject constructor(
    private val authRepository: AuthRepository,
) : ViewModel() {
    private val _state = MutableStateFlow<PhoneEntryUiState>(PhoneEntryUiState.Ready())
    val state: StateFlow<PhoneEntryUiState> = _state.asStateFlow()

    private val _events = Channel<PhoneEntryEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    fun onPhoneChanged(s: String) {
        _state.value = PhoneEntryUiState.Ready(phoneInput = s.filter { it.isDigit() }.take(11))
    }

    fun submit() {
        val current = (_state.value as? PhoneEntryUiState.Ready) ?: return
        val phone = current.phoneInput
        if (phone.length < 10) {
            _state.value = current.copy(errorMessage = "Enter a valid Nigerian phone number.")
            return
        }
        val fullPhone = "+234" + phone.removePrefix("0")
        _state.value = PhoneEntryUiState.Submitting
        viewModelScope.launch {
            val r = authRepository.requestOtp(fullPhone)
            if (r.isSuccess) {
                _events.send(PhoneEntryEvent.CodeSent(fullPhone))
                _state.value = PhoneEntryUiState.Ready()
            } else {
                val err = r.exceptionOrNull()
                val msg = when (err) {
                    is AlabaError.TooManyOtpRequests -> "Too many requests. Try again in 15 minutes."
                    is AlabaError.NetworkError -> "Network error. Check your connection."
                    else -> "Something went wrong. Try again."
                }
                _state.value = PhoneEntryUiState.Ready(phoneInput = phone, errorMessage = msg)
            }
        }
    }
}
