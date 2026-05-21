package com.orbanforest.alaba.data.device

import com.orbanforest.alaba.data.api.DevicesApi
import com.orbanforest.alaba.data.api.dto.DeviceListResponse
import com.orbanforest.alaba.data.auth.AlabaError
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DevicesRepository @Inject constructor(
    private val devicesApi: DevicesApi,
) {
    suspend fun list(): Result<DeviceListResponse> = try {
        val r = devicesApi.listDevices()
        if (r.isSuccessful) Result.success(r.body()!!)
        else Result.failure(AlabaError.Unknown(r.code(), r.errorBody()?.string() ?: ""))
    } catch (t: Throwable) {
        Result.failure(AlabaError.NetworkError(t))
    }

    suspend fun deactivate(deviceId: String): Result<Unit> = try {
        val r = devicesApi.deactivateDevice(deviceId)
        when {
            r.isSuccessful -> Result.success(Unit)
            r.code() == 404 -> Result.failure(AlabaError.DeviceNotFound)
            r.code() == 429 -> Result.failure(AlabaError.CooldownActive(unlockAt = null))
            else -> Result.failure(AlabaError.Unknown(r.code(), r.errorBody()?.string() ?: ""))
        }
    } catch (t: Throwable) {
        Result.failure(AlabaError.NetworkError(t))
    }
}
