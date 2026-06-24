import QtQuick
import QtQuick.Controls
import ElysiumTheme 1.0
import "."

ScrollView {
    id: root
    property bool darkMode: true

    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    ScrollBar.vertical: ScrollBar {
        implicitWidth: 6
        contentItem: Rectangle {
            radius: 3
            color: Theme.border(darkMode)
            opacity: 0.45
        }
        background: Rectangle { color: "transparent" }
    }

    Flow {
        id: flow
        width: root.availableWidth
        spacing: Theme.gridSpacingH

        property int columns: Math.max(1, Math.floor((width + spacing) / (Theme.cardWidth + spacing)))
        property int cellWidth: columns > 0
            ? Math.floor((width - (columns - 1) * spacing) / columns)
            : Theme.cardWidth

        Repeater {
            model: Elysium.appsModel

            delegate: AppCard {
                width: flow.cellWidth
                height: width
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
