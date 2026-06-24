import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0

RowLayout {
    property string label: ""
    property bool darkMode: true
    property Item control: null

    spacing: 12

    Text {
        Layout.fillWidth: true
        text: label
        wrapMode: Text.WordWrap
        font.family: Theme.fontFamily
        font.pixelSize: 14
        color: Theme.textPrimary(darkMode)
    }

    Loader {
        Layout.alignment: Qt.AlignRight
        sourceComponent: control
    }
}
