import QtQuick
import QtQuick.Controls
import ElysiumTheme 1.0

ToolButton {
    id: root
    property bool darkMode: true
    property bool active: false

    implicitWidth: Math.max(48, label.implicitWidth + 16)
    implicitHeight: 28

    background: Rectangle {
        radius: 8
        color: root.active
            ? Qt.rgba(Theme.accent(darkMode).r, Theme.accent(darkMode).g, Theme.accent(darkMode).b, 0.15)
            : (root.hovered ? Theme.surfaceHover(darkMode) : "transparent")
        border.color: root.active ? Theme.accent(darkMode) : Theme.borderSubtle(darkMode)
        border.width: root.active ? 1 : 0
    }

    contentItem: Text {
        id: label
        text: root.text
        font.family: Theme.fontFamily
        font.pixelSize: 11
        font.weight: root.active ? Font.DemiBold : Font.Normal
        color: root.active ? Theme.accent(darkMode) : Theme.textMuted(darkMode)
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
