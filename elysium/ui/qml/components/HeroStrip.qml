import QtQuick

import QtQuick.Controls

import QtQuick.Layouts

import ElysiumTheme 1.0



Item {

    id: root

    property bool darkMode: true

    implicitHeight: heroColumn.implicitHeight

    implicitWidth: parent ? parent.width : 400



    ColumnLayout {

        id: heroColumn

        anchors.horizontalCenter: parent.horizontalCenter

        width: parent.width

        spacing: 4



        Text {

            Layout.alignment: Qt.AlignHCenter

            text: "ELYSIUM"

            font.family: Theme.fontFamily

            font.pixelSize: 24

            font.weight: Font.Bold

            font.letterSpacing: 4

            color: Theme.accent(darkMode)

        }



        Text {

            Layout.alignment: Qt.AlignHCenter

            text: "Made with love from the Advanced Projects Team"

            font.family: Theme.fontFamily

            font.pixelSize: 11

            color: Theme.textSecondary(darkMode)

            horizontalAlignment: Text.AlignHCenter

        }



        Text {

            Layout.alignment: Qt.AlignHCenter

            text: "Protech Automotive Solutions"

            font.family: Theme.fontFamily

            font.pixelSize: 11

            font.weight: Font.DemiBold

            color: Theme.textMuted(darkMode)

            horizontalAlignment: Text.AlignHCenter

        }



        Text {

            Layout.alignment: Qt.AlignHCenter

            Layout.topMargin: 2

            text: "Welcome, " + Elysium.userName

            font.family: Theme.fontFamily

            font.pixelSize: 12

            color: Theme.textSecondary(darkMode)

            opacity: 0.85

        }



        RowLayout {

            Layout.alignment: Qt.AlignHCenter

            Layout.topMargin: 6

            spacing: 10



            Rectangle {

                radius: 12

                color: Theme.surfaceElevated(darkMode)

                border.color: Theme.borderSubtle(darkMode)

                implicitHeight: statsRow.implicitHeight + 10

                implicitWidth: statsRow.implicitWidth + 20



                RowLayout {

                    id: statsRow

                    anchors.centerIn: parent

                    spacing: 6



                    Rectangle {

                        width: 7

                        height: 7

                        radius: 3.5

                        color: "#4ade80"

                        visible: Elysium.readyAppCount > 0

                    }



                    Text {

                        text: Elysium.readyAppCount + " ready"

                        font.family: Theme.fontFamily

                        font.pixelSize: 11

                        color: Theme.textSecondary(darkMode)

                    }



                    Text {

                        visible: Elysium.updatingAppCount > 0

                        text: "\u00B7 " + Elysium.updatingAppCount + " updating"

                        font.family: Theme.fontFamily

                        font.pixelSize: 11

                        color: "#fbbf24"

                    }

                }

            }



            Rectangle {

                radius: 10

                color: Theme.surfaceElevated(darkMode)

                border.color: Theme.borderSubtle(darkMode)

                implicitHeight: versionLabel.implicitHeight + 8

                implicitWidth: versionLabel.implicitWidth + 16



                Text {

                    id: versionLabel

                    anchors.centerIn: parent

                    text: "v" + Elysium.version

                    font.family: Theme.fontFamily

                    font.pixelSize: 11

                    color: Theme.textMuted(darkMode)

                }

            }

        }

    }

}


