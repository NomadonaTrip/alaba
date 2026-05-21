package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class MeViewerDto(
    val role: String,
    @field:com.squareup.moshi.Json(name = "user_id") val userId: String,
    val phone: String,
    @field:com.squareup.moshi.Json(name = "user_device_id") val userDeviceId: String,
    @field:com.squareup.moshi.Json(name = "user_device_display_name") val deviceDisplayName: String?,
    @field:com.squareup.moshi.Json(name = "user_device_model") val deviceModel: String?,
    @field:com.squareup.moshi.Json(name = "user_device_last_seen_at") val deviceLastSeenAt: String?,
)
