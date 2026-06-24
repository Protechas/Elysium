import QtQuick
import ElysiumTheme 1.0

Item {
    id: root
    property bool darkMode: true

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.bgTop(darkMode) }
            GradientStop { position: 0.55; color: Theme.bgBottom(darkMode) }
            GradientStop { position: 1; color: Theme.bgBottom(darkMode) }
        }
    }

    Repeater {
        model: [
            { size: 320, ax: 0.88, ay: -0.08, dx: 40, dy: 30, opMin: 0.04, opMax: 0.11, delay: 0 },
            { size: 260, ax: -0.12, ay: 0.72, dx: 35, dy: -45, opMin: 0.03, opMax: 0.09, delay: 800 },
            { size: 200, ax: 0.15, ay: 0.35, dx: -50, dy: 25, opMin: 0.025, opMax: 0.08, delay: 1600 },
            { size: 180, ax: 0.55, ay: 0.85, dx: 30, dy: -35, opMin: 0.02, opMax: 0.07, delay: 2400 },
            { size: 140, ax: 0.72, ay: 0.42, dx: -25, dy: 40, opMin: 0.03, opMax: 0.1, delay: 1200 },
            { size: 220, ax: 0.02, ay: 0.12, dx: 45, dy: 20, opMin: 0.025, opMax: 0.075, delay: 2000 }
        ]

        delegate: Item {
            id: orbHost
            width: root.width
            height: root.height

            property real baseX: root.width * modelData.ax
            property real baseY: root.height * modelData.ay

            Rectangle {
                id: orb
                width: modelData.size
                height: modelData.size
                radius: width / 2
                x: baseX - width / 2
                y: baseY - height / 2
                color: Theme.accentGlow(darkMode)
                opacity: darkMode ? modelData.opMin : modelData.opMin * 0.6
                scale: 1

                SequentialAnimation on opacity {
                    running: true
                    loops: Animation.Infinite
                    PauseAnimation { duration: modelData.delay }
                    NumberAnimation {
                        from: modelData.opMin
                        to: modelData.opMax
                        duration: Theme.orbPulseDuration
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        from: modelData.opMax
                        to: modelData.opMin
                        duration: Theme.orbPulseDuration
                        easing.type: Easing.InOutSine
                    }
                }

                SequentialAnimation on scale {
                    running: true
                    loops: Animation.Infinite
                    PauseAnimation { duration: modelData.delay + 400 }
                    NumberAnimation { from: 0.92; to: 1.08; duration: Theme.orbPulseDuration * 1.2; easing.type: Easing.InOutSine }
                    NumberAnimation { from: 1.08; to: 0.92; duration: Theme.orbPulseDuration * 1.2; easing.type: Easing.InOutSine }
                }

                SequentialAnimation on x {
                    running: true
                    loops: Animation.Infinite
                    PauseAnimation { duration: modelData.delay }
                    NumberAnimation {
                        from: orb.x
                        to: orb.x + modelData.dx
                        duration: Theme.orbDriftDuration
                        easing.type: Easing.InOutQuad
                    }
                    NumberAnimation {
                        from: orb.x + modelData.dx
                        to: orb.x
                        duration: Theme.orbDriftDuration
                        easing.type: Easing.InOutQuad
                    }
                }

                SequentialAnimation on y {
                    running: true
                    loops: Animation.Infinite
                    PauseAnimation { duration: modelData.delay + 600 }
                    NumberAnimation {
                        from: orb.y
                        to: orb.y + modelData.dy
                        duration: Theme.orbDriftDuration * 1.1
                        easing.type: Easing.InOutQuad
                    }
                    NumberAnimation {
                        from: orb.y + modelData.dy
                        to: orb.y
                        duration: Theme.orbDriftDuration * 1.1
                        easing.type: Easing.InOutQuad
                    }
                }
            }
        }
    }
}
