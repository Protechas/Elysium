import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0

Item {
    id: root
    property bool darkMode: true
    implicitWidth: grid.implicitWidth
    implicitHeight: grid.implicitHeight

    GridLayout {
        id: grid
        width: parent.width
        columns: Theme.gridColumns
        columnSpacing: Theme.gridSpacingH
        rowSpacing: Theme.gridSpacingV

        Repeater {
            model: Elysium.appsModel

            delegate: AppCard {
                Layout.preferredWidth: Theme.cardWidth
                Layout.preferredHeight: Theme.cardHeight
                darkMode: root.darkMode
                cardIndex: index
                appId: model.appId
                appName: model.name
                appDescription: model.description
                iconPath: model.iconPath
                statusText: model.status
                statusBg: model.statusBg
                statusFg: model.statusFg
            }
        }
    }
}
