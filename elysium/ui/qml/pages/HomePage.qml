import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0
import "../components"

Item {
    id: root
    objectName: "homePage"
    property bool darkMode: Elysium.darkMode

    function focusSearch() {
        commandBar.forceFocus()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        HeroStrip {
            Layout.fillWidth: true
            darkMode: root.darkMode
        }

        CommandBar {
            id: commandBar
            Layout.fillWidth: true
            darkMode: root.darkMode
        }

        GlassPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            darkMode: root.darkMode
            panelPadding: 8

            Loader {
                anchors.fill: parent
                sourceComponent: Elysium.appViewMode === "grid" ? gridComponent : listComponent
            }

            Component {
                id: listComponent
                AppListView { anchors.fill: parent; darkMode: root.darkMode }
            }

            Component {
                id: gridComponent
                AppFlowGrid { anchors.fill: parent; darkMode: root.darkMode }
            }
        }

        StatusStrip {
            Layout.fillWidth: true
            darkMode: root.darkMode
        }
    }
}
