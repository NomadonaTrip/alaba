package com.orbanforest.alaba.data.auth

import android.os.Build
import com.orbanforest.alaba.data.api.AuthApi
import com.orbanforest.alaba.data.api.dto.OtpRequestBody
import com.orbanforest.alaba.data.api.dto.OtpVerify409Body
import com.orbanforest.alaba.data.api.dto.OtpVerifyBody
import com.orbanforest.alaba.data.api.dto.OtpVerifyResponse
import com.squareup.moshi.Moshi
import javax.inject.Inject
import javax.inject.Singleton

sealed class AuthResult {
    data class Success(val jwt: String, val userDeviceId: String) : AuthResult()
    data class Failure(val error: AlabaError) : AuthResult()
}

@Singleton
class AuthRepository @Inject constructor(
    private val authApi: AuthApi,
    private val tokenStore: TokenStore,
    private val deviceIdStore: DeviceIdStore,
    private val moshi: Moshi,
) {
    suspend fun requestOtp(phone: String): Result<Unit> = try {
        val r = authApi.requestOtp(OtpRequestBody(phone))
        if (r.isSuccessful) Result.success(Unit)
        else Result.failure(mapError(r.code(), r.errorBody()?.string()))
    } catch (t: Throwable) {
        Result.failure(AlabaError.NetworkError(t))
    }

    suspend fun verifyOtp(phone: String, code: String): AuthResult {
        val body = OtpVerifyBody(
            phone = phone,
            code = code,
            deviceId = deviceIdStore.getOrCreate(),
            displayName = defaultDisplayName(),
            model = Build.MODEL,
        )
        return verifyOtpCommon(body)
    }

    suspend fun verifyOtpWithTicket(
        phone: String,
        verifyTicket: String,
        deactivateDeviceId: String,
    ): AuthResult {
        val body = OtpVerifyBody(
            phone = phone,
            verifyTicket = verifyTicket,
            deviceId = deviceIdStore.getOrCreate(),
            displayName = defaultDisplayName(),
            model = Build.MODEL,
            deactivateDeviceId = deactivateDeviceId,
        )
        return verifyOtpCommon(body)
    }

    private suspend fun verifyOtpCommon(body: OtpVerifyBody): AuthResult = try {
        val r = authApi.verifyOtp(body)
        if (r.isSuccessful) {
            val resp: OtpVerifyResponse = r.body()!!
            tokenStore.saveJwt(resp.jwt, resp.userDeviceId)
            AuthResult.Success(resp.jwt, resp.userDeviceId)
        } else {
            AuthResult.Failure(mapError(r.code(), r.errorBody()?.string()))
        }
    } catch (t: Throwable) {
        AuthResult.Failure(AlabaError.NetworkError(t))
    }

    private fun mapError(code: Int, body: String?): AlabaError {
        val detail = body?.let { parseDetail(it) }
        return when {
            code == 409 && detail?.error == "device_cap_reached" -> {
                val parsed = body?.let { parse409(it) }
                if (parsed != null) {
                    AlabaError.DeviceCapReached(parsed.activeDevices, parsed.verifyTicket)
                } else {
                    AlabaError.Unknown(code, body ?: "")
                }
            }
            code == 429 && detail?.error == "too_many_otp_requests" -> AlabaError.TooManyOtpRequests
            code == 429 && detail?.error == "attempts_exhausted" -> AlabaError.AttemptsExhausted
            code == 429 && detail?.error == "cooldown_active" -> AlabaError.CooldownActive(detail.unlockAt)
            code == 401 && detail?.error == "code_expired" -> AlabaError.CodeExpired
            code == 401 && detail?.error == "invalid_code" -> {
                val attempts = detail.attemptsRemaining
                if (attempts != null) AlabaError.InvalidCodeWithAttempts(attempts)
                else AlabaError.InvalidCode
            }
            code == 401 && detail?.error == "invalid_verify_ticket" -> AlabaError.InvalidVerifyTicket
            code == 404 && detail?.error?.startsWith("device_not_found") == true -> AlabaError.DeviceNotFound
            code == 403 && detail?.reason == "device_deactivated" -> AlabaError.DeviceDeactivated
            else -> AlabaError.Unknown(code, body ?: "")
        }
    }

    private fun parseDetail(body: String): com.orbanforest.alaba.data.api.dto.ErrorDetail? {
        return try {
            val adapter = moshi.adapter(com.orbanforest.alaba.data.api.dto.ErrorResponse::class.java)
            adapter.fromJson(body)?.detail
        } catch (t: Throwable) {
            null
        }
    }

    private fun parse409(body: String): OtpVerify409Body? {
        return try {
            // 409 wraps the same body inside "detail"
            val adapter = moshi.adapter(Map::class.java)
            val outer = adapter.fromJson(body) ?: return null
            val detail = outer["detail"] ?: return null
            val detailJson = moshi.adapter(Any::class.java).toJson(detail)
            val parser = moshi.adapter(OtpVerify409Body::class.java)
            parser.fromJson(detailJson)
        } catch (t: Throwable) {
            null
        }
    }

    private fun defaultDisplayName(): String = "${Build.BRAND} ${Build.MODEL}".trim()
}
