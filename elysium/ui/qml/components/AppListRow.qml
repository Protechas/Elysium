import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0
import "."

Item {
    id: root
    property bool darkMode: true
    property string appId: ""
    property string appName: ""
    property string appDescription: ""
    property string appTags: ""
    property string iconPath: ""
    property string statusText: "Ready"
    property color statusBg: "#1e293b"
    property color statusFg: "#94a3b8"
    property int rowIndex: 0

    implicitWidth: parent ? parent.width : 400
    implicitHeight: Theme.rowHeight

    opacity: 0
    Component.onCompleted: enterAnim.start()

    SequentialAnimation {
        id: enterAnim
        PauseAnimation { duration: rowIndex * 30 }
        NumberAnimation { target: root; property: "opacity"; to: 1; duration: Theme.animNormal; easing.type: Easing.OutCubic }
    }

    Rectangle {
        id: rowBg
        anchors.fill: parent
        radius: 10
        color: rowArea.containsMouse ? Theme.rowHover(darkMode) : "transparent"
        Behavior on color { ColorAnimation { duration: Theme.animFast } }

        Rectangle {
            width: 3
            height: parent.height - 16
            anchors.left: parent.left
            anchors.leftMargin: 4
            anchors.verticalCenter: parent.verticalCenter
            radius: 2
            color: Theme.accent(darkMode)
            opacity: rowArea.containsMouse ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: Theme.animFast } }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 14
            anchors.rightMargin: 12
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 44
                Layout.preferredHeight: 44
                radius: 11
                color: Theme.surface(darkMode)
                border.color: Theme.borderSubtle(darkMode)

                Image {
                    anchors.centerIn: parent
                    width: 36
                    height: 36
                    source: iconPath
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    visible: iconPath !== ""
                }

                Text {
                    anchors.centerIn: parent
                    visible: iconPath === ""
                    text: appName.length > 0 ? appName.charAt(0).toUpperCase() : "?"
                    font.family: Theme.fontFamily
                    font.pixelSize: 18
                    font.weight: Font.Bold
                    color: Theme.accent(darkMode)
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    Layout.fillWidth: true
                    text: appName
                    font.family: Theme.fontFamily
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    color: Theme.textPrimary(darkMode)
                    elide: Text.ElideRight
                }

                Text {
                    Layout.fillWidth: true
                    text: appDescription || appTags
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    color: Theme.textMuted(darkMode)
                    elide: Text.ElideRight
                }
            }

            StatusBadge {
                darkMode: root.darkMode
                statusText: root.statusText
                statusBg: root.statusBg
                statusFg: root.statusFg
            }

            Row {
                spacing: 4
                visible: rowArea.containsMouse && statusText !== "Needs Node"
                opacity: rowArea.containsMouse ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: Theme.animFast } }

                ToolButton {
                    text: "\u21BB"
                    onClicked: Elysium.updateApp(appId)
                    ToolTip.visible: hovered
                    ToolTip.text: "Update"
                    background: Rectangle { radius: 6; color: Theme.surfaceElevated(darkMode) }
                    contentItem: Text { text: parent.text; color: Theme.textSecondary(darkMode); horizontalAlignment: Text.AlignHCenter; anchors.centerIn: parent }
                }

                ToolButton {
                    text: "\uD83D\uDCC1"
                    onClicked: Elysium.openAppFolder(appId)
                    ToolTip.visible: hovered
                    ToolTip.text: "Open folder"
                    background: Rectangle { radius: 6; color: Theme.surfaceElevated(darkMode) }
                    contentItem: Text { text: "\u2398"; color: Theme.textSecondary(darkMode); horizontalAlignment: Text.AlignHCenter; anchors.centerIn: parent }
                }
            }

            Text {
                text: "\u2192"
                font.pixelSize: 16
                color: rowArea.containsMouse ? Theme.accent(darkMode) : Theme.textMuted(darkMode)
                opacity: rowArea.containsMouse ? 1 : 0.4
                Behavior on color { ColorAnimation { duration: Theme.animFast } }
            }
        }

        MouseArea {
            id: rowArea
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            onClicked: function(mouse) {
                if (mouse.button === Qt.RightButton) {
                    contextMenu.popup()
                } else if (statusText === "Needs Node") {
                    Elysium.openNodeInstallPage()
                } else {
                    Elysium.launchApp(appId)
                }
            }
        }

        Menu {
            id: contextMenu
            MenuItem { text: "Launch"; onTriggered: Elysium.launchApp(appId) }
            MenuItem { text: "Update"; onTriggered: Elysium.updateApp(appId) }
            MenuItem { text: "Open install folder"; onTriggered: Elysium.openAppFolder(appId) }
            MenuItem { text: "Export diagnostics"; onTriggered: Elysium.exportDiagnostics() }
            MenuSeparator {}
            MenuItem {
                text: "Install Node.js"
                visible: statusText === "Needs Node"
                onTriggered: Elysium.openNodeInstallPage()
            }
        }
    }
}
