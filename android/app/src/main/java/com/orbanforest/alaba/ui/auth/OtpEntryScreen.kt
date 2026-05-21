package com.orbanforest.alaba.ui.auth

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.ui.components.OtpCodeInput

@Composable
fun OtpEntryScreen(
    phone: String,
    onSignedIn: () -> Unit,
    onDeviceCapReached: (devices: List<ActiveDeviceSummary>, ticket: String, phone: String) -> Unit,
    onBack: () -> Unit,
    viewModel: OtpEntryViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                OtpEntryEvent.VerifiedSignedIn -> onSignedIn()
                is OtpEntryEvent.DeviceCapReached -> onDeviceCapReached(event.activeDevices, event.verifyTicket, phone)
            }
        }
    }

    // Auto-submit when 6 digits entered.
    LaunchedEffect(state) {
        val codeInput = (state as? OtpEntryUiState.Ready)?.codeInput ?: ""
        if (codeInput.length == 6) viewModel.submit(phone)
    }

    Column(modifier = Modifier.fillMaxSize().padding(24.dp)) {
        Spacer(Modifier.height(8.dp))
        TextButton(onClick = onBack) { Text("← Back") }
        Spacer(Modifier.height(16.dp))
        Text("Check your messages", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(6.dp))
        Text(
            "We texted a 6-digit code to $phone.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(32.dp))

        val codeInput = (state as? OtpEntryUiState.Ready)?.codeInput ?: ""
        OtpCodeInput(
            value = codeInput,
            onValueChange = viewModel::onCodeChanged,
            modifier = Modifier.fillMaxWidth(),
        )

        val errorMsg = (state as? OtpEntryUiState.Ready)?.errorMessage
        if (errorMsg != null) {
            Spacer(Modifier.height(8.dp))
            Text(errorMsg, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(24.dp))
        Button(
            onClick = { viewModel.submit(phone) },
            modifier = Modifier.fillMaxWidth(),
            enabled = state is OtpEntryUiState.Ready,
        ) {
            Text(if (state is OtpEntryUiState.Submitting) "Verifying..." else "Verify")
        }
    }
}
