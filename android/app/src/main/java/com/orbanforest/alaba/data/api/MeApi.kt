package com.orbanforest.alaba.data.api

import com.orbanforest.alaba.data.api.dto.MeViewerDto
import retrofit2.Response
import retrofit2.http.GET

interface MeApi {
    @GET("/me")
    suspend fun me(): Response<MeViewerDto>
}
