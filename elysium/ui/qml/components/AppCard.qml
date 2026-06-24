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
    property string iconPath: ""
    property string statusText: "Ready"
    property color statusBg: "#1e293b"
    property color statusFg: "#94a3b8"
    property int cardIndex: 0

    implicitWidth: Theme.cardWidth
    implicitHeight: width > 0 ? width : Theme.cardWidth

    opacity: 0
    scale: cardArea.containsMouse ? 1.03 : 1.0

    Behavior on scale { NumberAnimation { duration: Theme.animNormal; easing.type: Easing.OutCubic } }
    Behavior on opacity { NumberAnimation { duration: Theme.animNormal; easing.type: Easing.OutCubic } }

    Component.onCompleted: enterAnim.start()

    SequentialAnimation {
        id: enterAnim
        PauseAnimation { duration: cardIndex * 45 }
        ParallelAnimation {
            NumberAnimation { target: root; property: "opacity"; to: 1; duration: Theme.animSlow; easing.type: Easing.OutCubic }
            NumberAnimation { target: root; property: "scale"; from: 0.94; to: 1; duration: Theme.animSlow; easing.type: Easing.OutBack }
        }
    }

    Rectangle {
        id: cardShadow
        anchors.fill: card
        anchors.topMargin: cardArea.containsMouse ? 6 : 3
        radius: width / 2
        color: "#000000"
        opacity: darkMode ? (cardArea.containsMouse ? 0.35 : 0.22) : (cardArea.containsMouse ? 0.12 : 0.06)
        z: -1

        Behavior on opacity { NumberAnimation { duration: Theme.animNormal } }
        Behavior on anchors.topMargin { NumberAnimation { duration: Theme.animNormal } }
    }

    Rectangle {
        id: card
        anchors.fill: parent
        radius: width / 2
        border.width: cardArea.containsMouse ? 1.5 : 1
        border.color: cardArea.containsMouse ? Theme.accent(darkMode) : Theme.borderSubtle(darkMode)

        gradient: Gradient {
            GradientStop {
                position: 0
                color: cardArea.containsMouse ? Theme.surfaceHover(darkMode) : Theme.cardTop(darkMode)
            }
            GradientStop { position: 1; color: Theme.cardBottom(darkMode) }
        }

        Behavior on border.color { ColorAnimation { duration: Theme.animFast } }

        Rectangle {
            anchors.fill: parent
            radius: width / 2
            visible: cardArea.containsMouse
            color: Theme.accentGlow(darkMode)
            opacity: 0.06
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Theme.cardPadding
            spacing: 6

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: parent.height * 0.38

                Rectangle {
                    anchors.centerIn: parent
                    width: Math.min(parent.width, parent.height) * 0.78
                    height: width
                    radius: width / 2
                    color: "transparent"
                    border.width: 1
                    border.color: cardArea.containsMouse
                        ? Qt.rgba(Theme.accent(darkMode).r, Theme.accent(darkMode).g, Theme.accent(darkMode).b, 0.35)
                        : Theme.borderSubtle(darkMode)

                    Behavior on border.color { ColorAnimation { duration: Theme.animFast } }

                    Image {
                        anchors.centerIn: parent
                        width: parent.width * 0.82
                        height: width
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
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        color: Theme.accent(darkMode)
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                Layout.maximumHeight: 28
                text: appName
                horizontalAlignment: Text.AlignHCenter
                font.family: Theme.fontFamily
                font.pixelSize: 11
                font.weight: Font.DemiBold
                color: Theme.textPrimary(darkMode)
                elide: Text.ElideRight
                maximumLineCount: 2
                wrapMode: Text.WordWrap
            }

            StatusBadge {
                Layout.alignment: Qt.AlignHCenter
                darkMode: root.darkMode
                statusText: root.statusText
                statusBg: root.statusBg
                statusFg: root.statusFg
            }

            Item { Layout.fillHeight: true; visible: statusText === "Needs Node" }

            ElysiumButton {
                Layout.alignment: Qt.AlignHCenter
                Layout.fillWidth: true
                visible: statusText === "Needs Node"
                text: "Install Node"
                variant: "primary"
                darkMode: root.darkMode
                onClicked: Elysium.openNodeInstallPage()
            }
        }

        MouseArea {
            id: cardArea
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            ToolTip.visible: root.visible && containsMouse && appDescription !== ""
            ToolTip.text: appDescription
            ToolTip.delay: 350

            onClicked: function(mouse) {
                if (mouse.button === Qt.RightButton) {
                    contextMenu.popup()
                } else if (statusText === "Needs Node") {
                    Elysium.openNodeInstallPage()
                } else {
                    cardPressAnim.start()
                    Elysium.launchApp(appId)
                }
            }
        }

        SequentialAnimation {
            id: cardPressAnim
            NumberAnimation { target: root; property: "scale"; to: 0.97; duration: 70 }
            NumberAnimation { target: root; property: "scale"; to: cardArea.containsMouse ? 1.03 : 1; duration: 120; easing.type: Easing.OutCubic }
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
