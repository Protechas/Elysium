import QtQuick
import QtQuick.Controls
import ElysiumTheme 1.0

Item {
    id: root
    property bool darkMode: true
    property string level: "info"

    implicitWidth: Math.max(260, label.implicitWidth + 40)
    implicitHeight: 44

    y: visible ? 0 : 20
    opacity: visible ? 1 : 0
    visible: opacity > 0

    Behavior on opacity { NumberAnimation { duration: Theme.animNormal; easing.type: Easing.OutCubic } }
    Behavior on y { NumberAnimation { duration: Theme.animNormal; easing.type: Easing.OutCubic } }

    Rectangle {
        anchors.fill: parent
        radius: 22
        color: Theme.surfaceGlass(darkMode)
        border.width: 1
        border.color: level === "success"
            ? "#4ade80"
            : (level === "error" ? "#f87171" : Qt.rgba(Theme.accent(darkMode).r, Theme.accent(darkMode).g, Theme.accent(darkMode).b, 0.45))

        Rectangle {
            anchors.fill: parent
            radius: 22
            color: level === "success"
                ? "#4ade80"
                : (level === "error" ? "#f87171" : Theme.accentGlow(darkMode))
            opacity: 0.08
        }
    }

    Row {
        anchors.centerIn: parent
        spacing: 10
        leftPadding: 16
        rightPadding: 16

        Rectangle {
            width: 6
            height: 6
            radius: 3
            anchors.verticalCenter: parent.verticalCenter
            color: level === "success"
                ? "#4ade80"
                : (level === "error" ? "#f87171" : Theme.accent(darkMode))
        }

        Text {
            id: label
            width: Math.min(400, implicitWidth)
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            font.family: Theme.fontFamily
            font.pixelSize: 13
            color: Theme.textPrimary(darkMode)
        }
    }

    Timer {
        id: hideTimer
        interval: 3400
        onTriggered: root.opacity = 0
    }

    onOpacityChanged: {
        if (opacity === 0)
            visible = false
    }

    function show(message, toastLevel) {
        label.text = message
        level = toastLevel || "info"
        visible = true
        opacity = 1
        y = 0
        hideTimer.restart()
    }
}
