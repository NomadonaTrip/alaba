package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class DeviceDto(
    val id: String,
    @field:com.squareup.moshi.Json(name = "display_name") val displayName: String?,
    val model: String?,
    val platform: String,
    @field:com.squareup.moshi.Json(name = "activated_at") val activatedAt: String,
    @field:com.squareup.moshi.Json(name = "deactivated_at") val deactivatedAt: String?,
    @field:com.squareup.moshi.Json(name = "last_seen_at") val lastSeenAt: String?,
    @field:com.squareup.moshi.Json(name = "is_current") val isCurrent: Boolean,
)

@JsonClass(generateAdapter = true)
data class DeviceListResponse(
    val devices: List<DeviceDto>,
    val cap: Int,
    @field:com.squareup.moshi.Json(name = "active_count") val activeCount: Int,
    @field:com.squareup.moshi.Json(name = "deactivation_cooldown_unlock_at") val cooldownUnlockAt: String?,
)
