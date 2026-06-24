import QtQuick
import QtQuick.Controls
import ElysiumTheme 1.0

ToolButton {
    id: root
    property bool darkMode: true
    property string glyph: ""
    property string toolTipLabel: ""
    property bool active: false

    width: Theme.railWidth - 8
    height: 48

    background: Rectangle {
        radius: 10
        color: root.active || root.hovered
            ? Qt.rgba(Theme.accent(darkMode).r, Theme.accent(darkMode).g, Theme.accent(darkMode).b, root.active ? 0.18 : 0.1)
            : "transparent"
        border.color: root.active ? Theme.accent(darkMode) : "transparent"
        border.width: root.active ? 1 : 0

        Behavior on color { ColorAnimation { duration: Theme.animFast } }
    }

    contentItem: Text {
        text: root.glyph
        font.pixelSize: 18
        color: root.active || root.hovered ? Theme.accent(darkMode) : Theme.textMuted(darkMode)
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    ToolTip.visible: hovered
    ToolTip.text: toolTipLabel
    ToolTip.delay: 400
}
