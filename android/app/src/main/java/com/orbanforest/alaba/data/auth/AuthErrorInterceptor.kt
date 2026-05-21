package com.orbanforest.alaba.data.auth

import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthErrorInterceptor @Inject constructor(
    private val authEventBus: AuthEventBus,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val response = chain.proceed(chain.request())
        when (response.code) {
            401 -> authEventBus.emit(AuthEvent.TokenExpired)
            403 -> {
                val body = response.peekBody(4096L).string()
                if (body.contains("\"device_deactivated\"")) {
                    authEventBus.emit(AuthEvent.DeviceDeactivated)
                }
            }
        }
        return response
    }
}
