import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0

Item {
    id: root
    property bool darkMode: Elysium.darkMode

    ColumnLayout {
        anchors.fill: parent
        spacing: 28

        Item { Layout.fillHeight: true }

        ColumnLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 10

            Item {
                Layout.alignment: Qt.AlignHCenter
                width: titleGlow.width + 40
                height: titleGlow.height + 24

                Rectangle {
                    id: titleGlow
                    anchors.centerIn: parent
                    width: titleText.width + 48
                    height: titleText.height + 20
                    radius: height / 2
                    color: Theme.accentGlow(darkMode)
                    opacity: 0.12

                    SequentialAnimation on opacity {
                        id: glowPulse
                        running: true
                        loops: Animation.Infinite
                        NumberAnimation { from: 0.08; to: 0.18; duration: 1400; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 0.18; to: 0.08; duration: 1400; easing.type: Easing.InOutSine }
                    }
                }

                Text {
                    id: titleText
                    anchors.centerIn: parent
                    text: "ELYSIUM"
                    font.family: Theme.fontFamily
                    font.pixelSize: 36
                    font.weight: Font.Bold
                    font.letterSpacing: 6
                    color: Theme.accent(darkMode)
                }
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Made with love from the Advanced Projects Team"
                font.family: Theme.fontFamily
                font.pixelSize: 12
                color: Theme.textSecondary(darkMode)
                horizontalAlignment: Text.AlignHCenter
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Protech Automotive Solutions"
                font.family: Theme.fontFamily
                font.pixelSize: 12
                font.weight: Font.DemiBold
                color: Theme.textMuted(darkMode)
                horizontalAlignment: Text.AlignHCenter
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 4
                text: "Preparing your workspace"
                font.family: Theme.fontFamily
                font.pixelSize: 14
                color: Theme.textSecondary(darkMode)
            }
        }

        ColumnLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 300
            spacing: 12

            Item {
                id: progressTrack
                Layout.fillWidth: true
                Layout.preferredHeight: 4
                property real indeterminatePos: 0.35

                Rectangle {
                    anchors.fill: parent
                    radius: 2
                    color: Theme.borderSubtle(darkMode)
                }

                Rectangle {
                    id: progressFill
                    height: parent.height
                    radius: 2
                    width: progressValue > 0
                        ? parent.width * (progressValue / 100)
                        : parent.width * progressTrack.indeterminatePos
                    color: Theme.accent(darkMode)

                    Behavior on width { NumberAnimation { duration: Theme.animNormal; easing.type: Easing.OutCubic } }

                    Rectangle {
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        width: 28
                        height: parent.height + 4
                        radius: 4
                        color: "#ffffff"
                        opacity: 0.35
                        visible: progressValue > 0 && progressValue < 100
                    }
                }

                SequentialAnimation on indeterminatePos {
                    running: progressValue <= 0
                    loops: Animation.Infinite
                    NumberAnimation { from: 0.15; to: 0.85; duration: 1200; easing.type: Easing.InOutQuad }
                    NumberAnimation { from: 0.85; to: 0.15; duration: 1200; easing.type: Easing.InOutQuad }
                }
            }

            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: statusText
                font.family: Theme.fontFamily
                font.pixelSize: 12
                color: Theme.textMuted(darkMode)
                wrapMode: Text.WordWrap
                opacity: 0.9
            }
        }

        Item { Layout.fillHeight: true }
    }

    property int progressValue: 0
    property string statusText: "Starting..."

    Connections {
        target: Elysium
        function onInitProgress(message, percent) {
            statusText = message
            progressValue = percent
        }
    }
}
