import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0

ColumnLayout {
    id: root
    property bool darkMode: true
    spacing: 6

    RowLayout {
        Layout.fillWidth: true
        spacing: 12

        ColumnLayout {
            spacing: 2

            Text {
                text: "ELYSIUM"
                font.family: Theme.fontFamily
                font.pixelSize: 28
                font.weight: Font.Bold
                font.letterSpacing: 4
                color: Theme.accent(darkMode)
            }

            Text {
                text: "Welcome, " + Elysium.userName
                font.family: Theme.fontFamily
                font.pixelSize: 13
                color: Theme.textSecondary(darkMode)
                opacity: 0.92
            }
        }

        Item { Layout.fillWidth: true }

        Rectangle {
            radius: 20
            color: Theme.surfaceElevated(darkMode)
            border.color: Theme.borderSubtle(darkMode)
            implicitHeight: versionLabel.implicitHeight + 10
            implicitWidth: versionLabel.implicitWidth + 22

            Text {
                id: versionLabel
                anchors.centerIn: parent
                text: "v" + Elysium.version
                font.family: Theme.fontFamily
                font.pixelSize: 11
                font.weight: Font.Medium
                color: Theme.textMuted(darkMode)
            }
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: Theme.borderSubtle(darkMode)
        opacity: 0.65
    }
}
