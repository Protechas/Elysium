import QtQuick
import ElysiumTheme 1.0

Rectangle {
    id: root
    property bool darkMode: true
    property int panelPadding: 16
    default property alias content: inner.data

    radius: Theme.radiusLg
    color: Theme.surfaceGlass(darkMode)
    border.width: 1
    border.color: Theme.borderSubtle(darkMode)

    gradient: Gradient {
        GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, darkMode ? 0.04 : 0.55) }
        GradientStop { position: 0.08; color: Theme.surfaceElevated(darkMode) }
        GradientStop { position: 1.0; color: Theme.surface(darkMode) }
    }

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: parent.height * 0.45
        radius: Theme.radiusLg
        opacity: darkMode ? 0.35 : 0.2
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, darkMode ? 0.06 : 0.25) }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }

    Item {
        id: inner
        anchors.fill: parent
        anchors.margins: panelPadding
    }
}
