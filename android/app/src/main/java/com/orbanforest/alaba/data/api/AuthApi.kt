package com.orbanforest.alaba.data.api

import com.orbanforest.alaba.data.api.dto.OtpRequestBody
import com.orbanforest.alaba.data.api.dto.OtpRequestResponse
import com.orbanforest.alaba.data.api.dto.OtpVerifyBody
import com.orbanforest.alaba.data.api.dto.OtpVerifyResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApi {
    @POST("/auth/otp/request")
    suspend fun requestOtp(@Body body: OtpRequestBody): Response<OtpRequestResponse>

    @POST("/auth/otp/verify")
    suspend fun verifyOtp(@Body body: OtpVerifyBody): Response<OtpVerifyResponse>
}
