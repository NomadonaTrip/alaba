package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class OtpVerifyBody(
    val phone: String,
    val code: String? = null,
    @field:com.squareup.moshi.Json(name = "verify_ticket") val verifyTicket: String? = null,
    @field:com.squareup.moshi.Json(name = "device_id") val deviceId: String,
    @field:com.squareup.moshi.Json(name = "display_name") val displayName: String? = null,
    val model: String? = null,
    val platform: String = "android",
    @field:com.squareup.moshi.Json(name = "deactivate_device_id") val deactivateDeviceId: String? = null,
)
