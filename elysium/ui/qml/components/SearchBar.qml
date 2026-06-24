import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0

Item {
    id: root
    property bool darkMode: true
    implicitHeight: 42

    function forceFocus() {
        field.forceActiveFocus()
        field.selectAll()
    }

    Rectangle {
        anchors.fill: parent
        radius: 21
        color: Theme.surfaceElevated(darkMode)
        border.color: field.activeFocus
            ? Qt.rgba(Theme.accent(darkMode).r, Theme.accent(darkMode).g, Theme.accent(darkMode).b, 0.55)
            : Theme.borderSubtle(darkMode)
        border.width: field.activeFocus ? 1.5 : 1

        Behavior on border.color { ColorAnimation { duration: Theme.animFast } }

        Rectangle {
            anchors.fill: parent
            radius: 21
            visible: field.activeFocus
            color: Theme.accentGlow(darkMode)
            opacity: 0.05
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 14
            spacing: 10

            Text {
                text: "\u2315"
                font.pixelSize: 16
                color: field.activeFocus ? Theme.accent(darkMode) : Theme.textMuted(darkMode)
                opacity: 0.85
            }

            TextField {
                id: field
                Layout.fillWidth: true
                placeholderText: "Search apps..."
                text: Elysium.searchText
                font.family: Theme.fontFamily
                font.pixelSize: 13
                color: Theme.textPrimary(darkMode)
                placeholderTextColor: Theme.textMuted(darkMode)
                selectByMouse: true
                background: Item {}
                onTextChanged: Elysium.setSearchText(text)
            }

            Text {
                visible: field.text.length === 0
                text: "Ctrl+F"
                font.family: Theme.fontFamily
                font.pixelSize: 10
                color: Theme.textMuted(darkMode)
                opacity: 0.55
            }
        }
    }
}
