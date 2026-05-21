package com.orbanforest.alaba.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.orbanforest.alaba.data.api.MeApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SignedInState(
    val phone: String? = null,
    val deviceLabel: String? = null,
    val loading: Boolean = true,
)

@HiltViewModel
class SignedInPlaceholderViewModel @Inject constructor(
    private val meApi: MeApi,
) : ViewModel() {
    private val _state = MutableStateFlow(SignedInState())
    val state: StateFlow<SignedInState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            try {
                val r = meApi.me()
                if (r.isSuccessful) {
                    val me = r.body()!!
                    _state.value = SignedInState(
                        phone = me.phone,
                        deviceLabel = me.deviceDisplayName ?: me.deviceModel,
                        loading = false,
                    )
                } else {
                    _state.value = SignedInState(loading = false)
                }
            } catch (t: Throwable) {
                _state.value = SignedInState(loading = false)
            }
        }
    }
}
