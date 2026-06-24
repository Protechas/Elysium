import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0

Dialog {
    id: root
    property bool darkMode: true
    modal: true
    anchors.centerIn: parent
    standardButtons: Dialog.Ok
    padding: 24

    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.animNormal }
        NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: Theme.animNormal; easing.type: Easing.OutCubic }
    }

    function openWith(title, message) {
        root.title = title
        bodyText.text = message
        open()
    }

    background: Rectangle {
        radius: Theme.radiusLg
        color: Theme.surfaceElevated(darkMode)
        border.color: Theme.borderSubtle(darkMode)
        border.width: 1

        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 3
            radius: Theme.radiusLg
            color: Theme.accent(darkMode)
            opacity: 0.85
        }
    }

    header: Text {
        text: root.title
        font.family: Theme.fontFamily
        font.pixelSize: 18
        font.weight: Font.Bold
        color: Theme.textPrimary(darkMode)
        topPadding: 8
    }

    contentItem: Text {
        id: bodyText
        wrapMode: Text.WordWrap
        width: 380
        font.family: Theme.fontFamily
        font.pixelSize: 13
        lineHeight: 1.35
        color: Theme.textSecondary(darkMode)
    }
}
