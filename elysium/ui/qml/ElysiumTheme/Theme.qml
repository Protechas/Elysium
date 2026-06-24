pragma Singleton
import QtQuick

QtObject {
    readonly property string fontFamily: "Segoe UI"

    readonly property color bgTopDark: "#0b1220"
    readonly property color bgBottomDark: "#040608"
    readonly property color surfaceDark: "#0f1623"
    readonly property color surfaceHoverDark: "#162032"
    readonly property color rowHoverDark: "#131f32"
    readonly property color surfaceElevatedDark: "#131d2e"
    readonly property color surfaceGlassDark: "#141e30"
    readonly property color railDark: "#0a101a"
    readonly property color cardTopDark: "#1a2738"
    readonly property color cardBottomDark: "#111a28"
    readonly property color borderDark: "#243044"
    readonly property color borderSubtleDark: "#1a2535"
    readonly property color accentDark: "#3ee0cf"
    readonly property color accentMutedDark: "#0d9488"
    readonly property color accentGlowDark: "#3ee0cf"
    readonly property color textDark: "#f1f5f9"
    readonly property color textSecondaryDark: "#94a3b8"
    readonly property color textMutedDark: "#64748b"

    readonly property color bgTopLight: "#f8fafc"
    readonly property color bgBottomLight: "#eef2f7"
    readonly property color surfaceLight: "#ffffff"
    readonly property color surfaceHoverLight: "#f8fafc"
    readonly property color rowHoverLight: "#f1f5f9"
    readonly property color surfaceElevatedLight: "#ffffff"
    readonly property color surfaceGlassLight: "#ffffff"
    readonly property color railLight: "#f1f5f9"
    readonly property color cardTopLight: "#ffffff"
    readonly property color cardBottomLight: "#f1f5f9"
    readonly property color borderLight: "#dbe3ee"
    readonly property color borderSubtleLight: "#e8eef5"
    readonly property color accentLight: "#0d9488"
    readonly property color accentMutedLight: "#14b8a6"
    readonly property color accentGlowLight: "#14b8a6"
    readonly property color textLight: "#0f172a"
    readonly property color textSecondaryLight: "#475569"
    readonly property color textMutedLight: "#64748b"

    function bgTop(dark) { return dark ? bgTopDark : bgTopLight }
    function bgBottom(dark) { return dark ? bgBottomDark : bgBottomLight }
    function surface(dark) { return dark ? surfaceDark : surfaceLight }
    function surfaceHover(dark) { return dark ? surfaceHoverDark : surfaceHoverLight }
    function rowHover(dark) { return dark ? rowHoverDark : rowHoverLight }
    function surfaceElevated(dark) { return dark ? surfaceElevatedDark : surfaceElevatedLight }
    function surfaceGlass(dark) { return dark ? surfaceGlassDark : surfaceGlassLight }
    function rail(dark) { return dark ? railDark : railLight }
    function cardTop(dark) { return dark ? cardTopDark : cardTopLight }
    function cardBottom(dark) { return dark ? cardBottomDark : cardBottomLight }
    function border(dark) { return dark ? borderDark : borderLight }
    function borderSubtle(dark) { return dark ? borderSubtleDark : borderSubtleLight }
    function accent(dark) { return dark ? accentDark : accentLight }
    function accentMuted(dark) { return dark ? accentMutedDark : accentMutedLight }
    function accentGlow(dark) { return dark ? accentGlowDark : accentGlowLight }
    function textPrimary(dark) { return dark ? textDark : textLight }
    function textSecondary(dark) { return dark ? textSecondaryDark : textSecondaryLight }
    function textMuted(dark) { return dark ? textMutedDark : textMutedLight }

    readonly property int railWidth: 64
    readonly property int heroHeight: 96
    readonly property int orbDriftDuration: 9000
    readonly property int orbPulseDuration: 4200
    readonly property int bubbleSize: 64
    readonly property int rowHeight: 72
    readonly property int drawerWidth: 360
    readonly property int cardWidth: 148
    readonly property int cardHeight: 148
    readonly property int cardDiameter: cardWidth
    readonly property int gridSpacingH: 16
    readonly property int gridSpacingV: 16
    readonly property int cardPadding: 12
    readonly property int gridMinCellWidth: 140
    readonly property int radius: 14
    readonly property int radiusLg: 16
    readonly property int cardRadius: 14
    readonly property int animFast: 140
    readonly property int animNormal: 260
    readonly property int animSlow: 420
}
