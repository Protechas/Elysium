import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0

RowLayout {
    id: root
    property bool darkMode: true
    spacing: 10

    ElysiumButton {
        text: "Update Elysium"
        variant: "primary"
        darkMode: root.darkMode
        Layout.fillWidth: true
        onClicked: Elysium.updateElysium()
    }

    ElysiumButton {
        text: "Settings"
        variant: "ghost"
        darkMode: root.darkMode
        Layout.fillWidth: true
        onClicked: Elysium.openSettings()
    }
}
