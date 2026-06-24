import QtQuick
import QtQuick.Controls
import ElysiumTheme 1.0

Item {
    id: root
    property var window
    property bool darkMode: true
    property bool restoring: false

    signal restoreRequested()

    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: Theme.rail(darkMode)
        border.width: 2
        border.color: Theme.accent(darkMode)

        SequentialAnimation on border.width {
            running: root.visible
            loops: Animation.Infinite
            NumberAnimation { from: 2; to: 3; duration: 1200; easing.type: Easing.InOutSine }
            NumberAnimation { from: 3; to: 2; duration: 1200; easing.type: Easing.InOutSine }
        }

        Rectangle {
            anchors.centerIn: parent
            width: parent.width - 12
            height: parent.height - 12
            radius: width / 2
            color: Theme.accent(darkMode)
            opacity: 0.15

            SequentialAnimation on opacity {
                running: root.visible
                loops: Animation.Infinite
                NumberAnimation { from: 0.1; to: 0.22; duration: 1400; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.22; to: 0.1; duration: 1400; easing.type: Easing.InOutSine }
            }
        }

        Text {
            anchors.centerIn: parent
            text: "E"
            font.family: Theme.fontFamily
            font.pixelSize: 22
            font.weight: Font.Bold
            color: Theme.accent(darkMode)
        }
    }

    MouseArea {
        id: dragArea
        anchors.fill: parent
        enabled: root.visible && !root.restoring
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        property real pressX: 0
        property real pressY: 0
        property real winX: 0
        property real winY: 0
        property bool moved: false

        onPressed: function(mouse) {
            if (!window)
                return
            moved = false
            pressX = mouse.x
            pressY = mouse.y
            winX = window.x
            winY = window.y
        }

        onPositionChanged: function(mouse) {
            if (!window || !pressed)
                return
            var dx = mouse.x - pressX
            var dy = mouse.y - pressY
            if (Math.abs(dx) > 4 || Math.abs(dy) > 4)
                moved = true
            window.x = winX + dx
            window.y = winY + dy
        }

        onReleased: function(mouse) {
            if (!moved && !root.restoring)
                root.restoreRequested()
        }
    }
}
