package com.orbanforest.alaba.data.auth

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import javax.inject.Inject
import javax.inject.Singleton

sealed class AuthEvent {
    data object DeviceDeactivated : AuthEvent()
    data object TokenExpired : AuthEvent()
}

@Singleton
class AuthEventBus @Inject constructor() {
    private val _events = MutableSharedFlow<AuthEvent>(extraBufferCapacity = 1)
    val events: SharedFlow<AuthEvent> = _events

    fun emit(event: AuthEvent) {
        _events.tryEmit(event)
    }
}
