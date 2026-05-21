package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class OtpVerifyResponse(
    val jwt: String,
    @field:com.squareup.moshi.Json(name = "user_device_id") val userDeviceId: String,
    @field:com.squareup.moshi.Json(name = "expires_at") val expiresAt: String,
)
