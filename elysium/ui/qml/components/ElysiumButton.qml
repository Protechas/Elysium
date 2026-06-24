import QtQuick
import QtQuick.Controls
import ElysiumTheme 1.0

Button {
    id: root
    property bool darkMode: true
    property string variant: "primary"

    implicitHeight: 40
    hoverEnabled: true

    background: Rectangle {
        id: bg
        radius: 10
        opacity: root.enabled ? 1 : 0.45

        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop {
                position: 0
                color: variant === "primary"
                    ? (root.down || root.hovered ? Theme.accent(darkMode) : Theme.accentMuted(darkMode))
                    : (root.down || root.hovered ? Theme.surfaceHover(darkMode) : Theme.surfaceElevated(darkMode))
            }
            GradientStop {
                position: 1
                color: variant === "primary"
                    ? (root.down || root.hovered ? Theme.accentMuted(darkMode) : Theme.accent(darkMode))
                    : (root.down || root.hovered ? Theme.surfaceElevated(darkMode) : Theme.surfaceHover(darkMode))
            }
        }

        border.width: variant === "ghost" ? 1 : 0
        border.color: root.hovered ? Theme.accent(darkMode) : Theme.border(darkMode)

        Behavior on border.color { ColorAnimation { duration: Theme.animFast } }

        Rectangle {
            anchors.fill: parent
            radius: 10
            visible: variant === "primary" && root.hovered
            color: Theme.accentGlow(darkMode)
            opacity: 0.12
        }
    }

    contentItem: Text {
        text: root.text
        color: variant === "primary" ? "#ffffff" : Theme.textSecondary(darkMode)
        font.family: Theme.fontFamily
        font.pixelSize: 13
        font.weight: variant === "primary" ? Font.DemiBold : Font.Normal
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
