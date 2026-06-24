import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0
import "."

Item {
    id: root
    property bool darkMode: true
    visible: opacity > 0
    opacity: Elysium.settingsDrawerOpen ? 1 : 0
    z: 100

    Behavior on opacity { NumberAnimation { duration: Theme.animNormal } }

    MouseArea {
        anchors.fill: parent
        visible: Elysium.settingsDrawerOpen
        onClicked: Elysium.closeSettings()
    }

    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: Elysium.settingsDrawerOpen ? 0.45 : 0
        Behavior on opacity { NumberAnimation { duration: Theme.animNormal } }
    }

    Rectangle {
        id: panel
        width: Theme.drawerWidth
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.rightMargin: Elysium.settingsDrawerOpen ? 0 : -width

        Behavior on anchors.rightMargin {
            NumberAnimation { duration: Theme.animNormal; easing.type: Easing.OutCubic }
        }

        color: Theme.surfaceElevated(darkMode)
        border.color: Theme.borderSubtle(darkMode)
        border.width: 1

        Rectangle {
            anchors.left: parent.left
            width: 3
            height: parent.height
            color: Theme.accent(darkMode)
            opacity: 0.6
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 22
            spacing: 16

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: "Settings"
                    font.family: Theme.fontFamily
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    color: Theme.accent(darkMode)
                }

                Item { Layout.fillWidth: true }

                ToolButton {
                    text: "\u2715"
                    onClicked: Elysium.closeSettings()
                    background: Rectangle { radius: 8; color: Theme.surface(darkMode) }
                    contentItem: Text {
                        text: parent.text
                        color: Theme.textSecondary(darkMode)
                        horizontalAlignment: Text.AlignHCenter
                        anchors.centerIn: parent
                    }
                }
            }

            Repeater {
                model: [
                    { label: "Dark theme", type: "theme" },
                    { label: "Check for updates on startup", type: "updates" },
                    { label: "Use isolated Python env for DFR", type: "isolated" },
                    { label: "Use QML interface (restart required)", type: "qml" }
                ]

                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48

                        Text {
                            Layout.fillWidth: true
                            text: modelData.label
                            wrapMode: Text.WordWrap
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            color: Theme.textPrimary(darkMode)
                        }

                        Switch {
                            checked: modelData.type === "theme" ? Elysium.darkMode
                                : modelData.type === "updates" ? Elysium.checkUpdatesOnStartup
                                : modelData.type === "isolated" ? Elysium.useIsolatedEnvs
                                : Elysium.useQmlUi
                            onToggled: {
                                if (modelData.type === "theme") Elysium.setTheme(checked)
                                else if (modelData.type === "updates") Elysium.setCheckUpdatesOnStartup(checked)
                                else if (modelData.type === "isolated") Elysium.setUseIsolatedEnvs(checked)
                                else Elysium.setUseQmlUi(checked)
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        visible: index < 3
                        color: Theme.borderSubtle(darkMode)
                        opacity: 0.55
                    }
                }
            }

            Item { Layout.fillHeight: true }

            ElysiumButton {
                text: "Open logs folder"
                variant: "primary"
                darkMode: root.darkMode
                Layout.fillWidth: true
                onClicked: Elysium.openLogsFolder()
            }

            ElysiumButton {
                text: "Export diagnostics"
                variant: "ghost"
                darkMode: root.darkMode
                Layout.fillWidth: true
                onClicked: Elysium.exportDiagnostics()
            }
        }
    }
}
