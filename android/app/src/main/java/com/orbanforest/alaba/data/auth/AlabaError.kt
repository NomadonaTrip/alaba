package com.orbanforest.alaba.data.auth

import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary

sealed class AlabaError(message: String) : Exception(message) {
    data class NetworkError(val cause: Throwable?) : AlabaError("network_error")
    data object InvalidCode : AlabaError("invalid_code")
    data class InvalidCodeWithAttempts(val attemptsRemaining: Int) : AlabaError("invalid_code")
    data object CodeExpired : AlabaError("code_expired")
    data object AttemptsExhausted : AlabaError("attempts_exhausted")
    data object TooManyOtpRequests : AlabaError("too_many_otp_requests")
    data class DeviceCapReached(
        val activeDevices: List<ActiveDeviceSummary>,
        val verifyTicket: String,
    ) : AlabaError("device_cap_reached")
    data class CooldownActive(val unlockAt: String?) : AlabaError("cooldown_active")
    data object InvalidVerifyTicket : AlabaError("invalid_verify_ticket")
    data object DeviceNotFound : AlabaError("device_not_found")
    data object DeviceDeactivated : AlabaError("device_deactivated")
    data class Unknown(val statusCode: Int, val body: String) : AlabaError("unknown")
}
