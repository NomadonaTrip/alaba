package com.orbanforest.alaba.ui.auth

import app.cash.turbine.test
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.data.auth.AlabaError
import com.orbanforest.alaba.data.auth.AuthRepository
import com.orbanforest.alaba.data.auth.AuthResult
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class OtpEntryViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before fun setUp() { Dispatchers.setMain(dispatcher) }
    @After fun tearDown() { Dispatchers.resetMain() }

    @Test fun `successful verify emits VerifiedSignedIn`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        coEvery { repo.verifyOtp(any(), any()) } returns AuthResult.Success("jwt", "ud-1")
        val vm = OtpEntryViewModel(repo)
        vm.onCodeChanged("123456")
        vm.events.test {
            vm.submit("+2348031234567")
            dispatcher.scheduler.advanceUntilIdle()
            val event = awaitItem()
            assertTrue(event is OtpEntryEvent.VerifiedSignedIn)
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test fun `device cap reached emits DeviceCapReached`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        val devices = listOf(ActiveDeviceSummary("d1", "name", "model", "android", "2026-01-01T00:00:00Z", null))
        coEvery { repo.verifyOtp(any(), any()) } returns AuthResult.Failure(
            AlabaError.DeviceCapReached(devices, "ticket-xyz"),
        )
        val vm = OtpEntryViewModel(repo)
        vm.onCodeChanged("123456")
        vm.events.test {
            vm.submit("+2348031234567")
            dispatcher.scheduler.advanceUntilIdle()
            val event = awaitItem()
            assertTrue(event is OtpEntryEvent.DeviceCapReached)
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test fun `wrong code shows attempts remaining`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        coEvery { repo.verifyOtp(any(), any()) } returns AuthResult.Failure(
            AlabaError.InvalidCodeWithAttempts(attemptsRemaining = 3),
        )
        val vm = OtpEntryViewModel(repo)
        vm.onCodeChanged("123456")
        vm.submit("+2348031234567")
        dispatcher.scheduler.advanceUntilIdle()
        val state = vm.state.value
        assertTrue(state is OtpEntryUiState.Ready)
        assertTrue((state as OtpEntryUiState.Ready).errorMessage!!.contains("3"))
    }
}
