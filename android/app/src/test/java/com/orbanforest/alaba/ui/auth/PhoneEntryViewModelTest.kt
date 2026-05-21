package com.orbanforest.alaba.ui.auth

import app.cash.turbine.test
import com.orbanforest.alaba.data.auth.AuthRepository
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class PhoneEntryViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before fun setUp() { Dispatchers.setMain(dispatcher) }
    @After fun tearDown() { Dispatchers.resetMain() }

    @Test fun `valid Nigerian phone submits and emits CodeSent`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        coEvery { repo.requestOtp(any()) } returns Result.success(Unit)
        val vm = PhoneEntryViewModel(repo)
        vm.onPhoneChanged("08031234567")
        vm.events.test {
            vm.submit()
            dispatcher.scheduler.advanceUntilIdle()
            val event = awaitItem()
            assertTrue(event is PhoneEntryEvent.CodeSent)
            assertEquals("+2348031234567", (event as PhoneEntryEvent.CodeSent).phone)
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test fun `short phone shows validation error`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        val vm = PhoneEntryViewModel(repo)
        vm.onPhoneChanged("123")
        vm.submit()
        val state = vm.state.value
        assertTrue(state is PhoneEntryUiState.Ready)
        assertTrue((state as PhoneEntryUiState.Ready).errorMessage != null)
    }
}
