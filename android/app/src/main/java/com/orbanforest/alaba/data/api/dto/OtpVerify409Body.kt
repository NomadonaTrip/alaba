package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ActiveDeviceSummary(
    val id: String,
    @field:com.squareup.moshi.Json(name = "display_name") val displayName: String?,
    val model: String?,
    val platform: String,
    @field:com.squareup.moshi.Json(name = "activated_at") val activatedAt: String,
    @field:com.squareup.moshi.Json(name = "last_seen_at") val lastSeenAt: String?,
)

@JsonClass(generateAdapter = true)
data class OtpVerify409Body(
    val error: String,
    @field:com.squareup.moshi.Json(name = "active_devices") val activeDevices: List<ActiveDeviceSummary>,
    @field:com.squareup.moshi.Json(name = "verify_ticket") val verifyTicket: String,
)
