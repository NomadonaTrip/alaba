package com.orbanforest.alaba.di

import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

@Module
@InstallIn(SingletonComponent::class)
object AuthModule {
    // TokenStore, DeviceIdStore, AuthEventBus, AuthInterceptor, AuthErrorInterceptor
    // are all @Singleton with @Inject constructors — Hilt provides them automatically.
    // This module exists for future bindings if needed.
}
