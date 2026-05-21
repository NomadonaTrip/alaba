package com.orbanforest.alaba.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val AlabaLightColors = lightColorScheme(
    primary = AlabaPrimary,
    onPrimary = AlabaPrimaryContent,
    surface = AlabaSurface,
    surfaceVariant = AlabaSurfaceVariant,
    onSurface = AlabaOnSurface,
    onSurfaceVariant = AlabaMuted,
    outline = AlabaBorder,
    error = AlabaError,
)

@Composable
fun AlabaTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = AlabaLightColors, typography = AlabaTypography, content = content)
}
