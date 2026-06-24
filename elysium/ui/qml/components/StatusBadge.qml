import QtQuick
import ElysiumTheme 1.0

Rectangle {
    id: root
    property bool darkMode: true
    property string statusText: ""
    property color statusBg: "#1e293b"
    property color statusFg: "#94a3b8"

    radius: 10
    color: statusBg
    border.color: Qt.rgba(statusFg.r, statusFg.g, statusFg.b, 0.25)
    border.width: 1
    implicitHeight: 22
    implicitWidth: label.implicitWidth + 18

    Text {
        id: label
        anchors.centerIn: parent
        text: statusText
        color: statusFg
        font.family: Theme.fontFamily
        font.pixelSize: 10
        font.weight: Font.DemiBold
        font.letterSpacing: 0.3
    }
}
