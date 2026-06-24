import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0

RowLayout {
    id: root
    property bool darkMode: true
    implicitHeight: 32
    spacing: 12

    Text {
        Layout.fillWidth: true
        text: Elysium.statusMessage
        font.family: Theme.fontFamily
        font.pixelSize: 11
        color: Theme.textMuted(darkMode)
        elide: Text.ElideRight
        opacity: Elysium.statusMessage ? 0.9 : 0
        Behavior on opacity { NumberAnimation { duration: Theme.animFast } }
    }

    Row {
        spacing: 4

        ViewToggle {
            darkMode: root.darkMode
            text: "List"
            active: Elysium.appViewMode === "list"
            onClicked: Elysium.setAppViewMode("list")
        }

        ViewToggle {
            darkMode: root.darkMode
            text: "Grid"
            active: Elysium.appViewMode === "grid"
            onClicked: Elysium.setAppViewMode("grid")
        }
    }
}
