import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0
import "."

Rectangle {
    id: root
    property bool darkMode: true

    width: Theme.railWidth
    color: Theme.rail(darkMode)

    Rectangle {
        anchors.right: parent.right
        width: 1
        height: parent.height
        color: Theme.borderSubtle(darkMode)
        opacity: 0.8
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 16
        anchors.bottomMargin: 16
        spacing: 6

        Item {
            Layout.preferredWidth: Theme.railWidth
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter

            Rectangle {
                anchors.centerIn: parent
                width: 36
                height: 36
                radius: 10
                color: Theme.accent(darkMode)
                opacity: 0.15

                Text {
                    anchors.centerIn: parent
                    text: "E"
                    font.family: Theme.fontFamily
                    font.pixelSize: 18
                    font.weight: Font.Bold
                    color: Theme.accent(darkMode)
                }
            }
        }

        RailButton {
            Layout.alignment: Qt.AlignHCenter
            darkMode: root.darkMode
            glyph: "\u2302"
            toolTipLabel: "Home"
            active: true
        }

        RailButton {
            Layout.alignment: Qt.AlignHCenter
            darkMode: root.darkMode
            glyph: "\u2699"
            toolTipLabel: "Settings"
            onClicked: Elysium.openSettings()
        }

        Item { Layout.preferredHeight: 8 }

        RailButton {
            Layout.alignment: Qt.AlignHCenter
            darkMode: root.darkMode
            glyph: "\u21BB"
            toolTipLabel: "Update Elysium"
            onClicked: Elysium.updateElysium()
        }

        RailButton {
            Layout.alignment: Qt.AlignHCenter
            darkMode: root.darkMode
            glyph: "\u2912"
            toolTipLabel: "Export diagnostics"
            onClicked: Elysium.exportDiagnostics()
        }

        RailButton {
            Layout.alignment: Qt.AlignHCenter
            darkMode: root.darkMode
            glyph: "\u25CB"
            toolTipLabel: "Minimize to bubble"
            onClicked: Elysium.requestBubbleMinimize()
        }

        Item { Layout.fillHeight: true }

        RailButton {
            Layout.alignment: Qt.AlignHCenter
            darkMode: root.darkMode
            glyph: Elysium.darkMode ? "\u2600" : "\u263E"
            toolTipLabel: Elysium.darkMode ? "Light mode" : "Dark mode"
            onClicked: Elysium.setTheme(!Elysium.darkMode)
        }
    }
}
