import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0
import "../components"

Item {
    id: root
    objectName: "settingsPage"
    property bool darkMode: Elysium.darkMode

    ColumnLayout {
        anchors.fill: parent
        spacing: 16

        RowLayout {
            Layout.fillWidth: true

            Text {
                text: "Settings"
                font.family: Theme.fontFamily
                font.pixelSize: 26
                font.weight: Font.Bold
                font.letterSpacing: 1
                color: Theme.accent(darkMode)
            }

            Item { Layout.fillWidth: true }

            ElysiumButton {
                text: "Back"
                variant: "ghost"
                darkMode: root.darkMode
                implicitWidth: 88
                onClicked: Elysium.closeSettings()
            }
        }

        GlassPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            darkMode: root.darkMode
            panelPadding: 22

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Repeater {
                    model: [
                        { label: "Dark theme", type: "theme" },
                        { label: "Check for updates on startup", type: "updates" },
                        { label: "Use isolated Python env for DFR", type: "isolated" },
                        { label: "Use new QML interface (restart required)", type: "qml" }
                    ]

                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 52

                            Text {
                                Layout.fillWidth: true
                                text: modelData.label
                                font.family: Theme.fontFamily
                                font.pixelSize: 14
                                color: Theme.textPrimary(darkMode)
                                wrapMode: Text.WordWrap
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

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

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
    }
}
