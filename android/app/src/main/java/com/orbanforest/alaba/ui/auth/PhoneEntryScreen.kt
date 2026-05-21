package com.orbanforest.alaba.ui.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.compose.foundation.text.KeyboardOptions
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun PhoneEntryScreen(
    onCodeSent: (phone: String) -> Unit,
    viewModel: PhoneEntryViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            if (event is PhoneEntryEvent.CodeSent) onCodeSent(event.phone)
        }
    }
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Top,
    ) {
        Spacer(Modifier.height(48.dp))
        Text("Welcome to Alaba", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        Text(
            "Enter your Nigerian phone number and we'll text you a 6-digit code.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(40.dp))

        Text("Phone number", style = MaterialTheme.typography.labelMedium)
        Spacer(Modifier.height(6.dp))

        val phoneText = (state as? PhoneEntryUiState.Ready)?.phoneInput ?: ""

        OutlinedTextField(
            value = phoneText,
            onValueChange = viewModel::onPhoneChanged,
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            leadingIcon = { Text("🇳🇬 +234", modifier = Modifier.padding(start = 8.dp)) },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
            placeholder = { Text("803 123 4567") },
            enabled = state is PhoneEntryUiState.Ready,
        )

        val errorMsg = (state as? PhoneEntryUiState.Ready)?.errorMessage
        if (errorMsg != null) {
            Spacer(Modifier.height(6.dp))
            Text(errorMsg, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(24.dp))
        Button(
            onClick = viewModel::submit,
            modifier = Modifier.fillMaxWidth(),
            enabled = state is PhoneEntryUiState.Ready,
        ) {
            Text(if (state is PhoneEntryUiState.Submitting) "Sending..." else "Send code")
        }

        Spacer(Modifier.height(24.dp))
        Text(
            "By continuing you agree to our Terms and Privacy Policy.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
    }
}
