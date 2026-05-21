package com.orbanforest.alaba.data.api

import com.orbanforest.alaba.data.api.dto.DeviceListResponse
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface DevicesApi {
    @GET("/devices")
    suspend fun listDevices(): Response<DeviceListResponse>

    @POST("/devices/{id}/deactivate")
    suspend fun deactivateDevice(@Path("id") deviceId: String): Response<Unit>
}
