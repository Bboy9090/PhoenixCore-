import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: container
    width: 1920
    height: 1080
    color: "#081426"

    // Background Image
    Image {
        id: bgImage
        source: config.background
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
    }

    // Gradient overlay for storm depth
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(8/255, 20/255, 38/255, 0.4) }
            GradientStop { position: 0.5; color: Qt.rgba(5/255, 7/255, 13/255, 0.72) }
            GradientStop { position: 1.0; color: Qt.rgba(8/255, 20/255, 38/255, 0.88) }
        }
    }

    // Main Center Panel Container
    ColumnLayout {
        anchors.centerIn: parent
        spacing: 24
        width: 420

        // 1. Centered Phoenix Crest Logo
        Image {
            id: logo
            source: config.logo
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 120
            Layout.preferredHeight: 120
            fillMode: Image.PreserveAspectFit
            opacity: 0.95
        }

        // Tagline Typography Feel
        Text {
            text: "FOUR LEGACIES. ONE THRONE."
            font.family: config.fontDisplay
            font.pointSize: 11
            font.bold: true
            font.letterSpacing: 2
            color: "#D4AF37"
            Layout.alignment: Qt.AlignHCenter
        }

        // 2. Login Card Box
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            width: 380
            height: 280
            radius: 12
            color: Qt.rgba(5/255, 7/255, 13/255, 0.88)
            border.color: "#D4AF37"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 20

                // User Avatar Frame with Phoenix Ring
                Item {
                    Layout.alignment: Qt.AlignHCenter
                    width: 72
                    height: 72

                    Image {
                        id: avatarRing
                        source: config.avatarFrame
                        anchors.fill: parent
                    }

                    Image {
                        id: userAvatar
                        source: "assets/user.png"
                        width: 58
                        height: 58
                        anchors.centerIn: parent
                        fillMode: Image.PreserveAspectCrop
                        opacity: 0.9
                    }
                }

                // Username Label
                Text {
                    text: sddm.lastUser
                    font.family: config.fontUI
                    font.pointSize: 12
                    font.bold: true
                    color: "#F7F7FF"
                    Layout.alignment: Qt.AlignHCenter
                }

                // Password input field (Gold Border, Selected Blue Glow)
                TextField {
                    id: passwordField
                    placeholderText: "Enter password"
                    echoMode: TextInput.Password
                    font.family: config.fontUI
                    font.pointSize: 10
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    color: "#F7F7FF"
                    placeholderTextColor: Qt.rgba(247/255, 247/255, 255/255, 0.4)

                    background: Rectangle {
                        radius: 6
                        color: Qt.rgba(8/255, 20/255, 38/255, 0.72)
                        border.color: passwordField.activeFocus ? "#00C3FF" : "#D4AF37"
                        border.width: passwordField.activeFocus ? 2 : 1
                        
                        // Blue glow on active focus
                        layer.enabled: passwordField.activeFocus
                    }

                    onAccepted: sddm.login(sddm.lastUser, text, sessionIndex)
                }

                // Login Trigger Button
                Button {
                    text: "REIGN"
                    font.family: config.fontDisplay
                    font.pointSize: 10
                    font.bold: true
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38

                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        color: "#F7F7FF"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    background: Rectangle {
                        radius: 6
                        color: parent.hovered ? "#00C3FF" : "#1E6BFF"
                        border.color: "#D4AF37"
                        border.width: 1
                    }

                    onClicked: sddm.login(sddm.lastUser, passwordField.text, sessionIndex)
                }
            }
        }
    }

    // 3. Small Shutdown / Restart / Sleep Buttons at bottom corner
    RowLayout {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 24
        spacing: 16

        Button {
            text: "SLEEP"
            font.family: config.fontUI
            font.pointSize: 9
            font.bold: true
            
            contentItem: Text {
                text: parent.text
                font: parent.font
                color: "#C0C6D6"
            }
            background: Rectangle {
                color: "transparent"
            }
            onClicked: sddm.suspend()
        }

        Button {
            text: "REBOOT"
            font.family: config.fontUI
            font.pointSize: 9
            font.bold: true

            contentItem: Text {
                text: parent.text
                font: parent.font
                color: "#C0C6D6"
            }
            background: Rectangle {
                color: "transparent"
            }
            onClicked: sddm.reboot()
        }

        Button {
            text: "SHUTDOWN"
            font.family: config.fontUI
            font.pointSize: 9
            font.bold: true

            contentItem: Text {
                text: parent.text
                font: parent.font
                color: "#E53935"
            }
            background: Rectangle {
                color: "transparent"
            }
            onClicked: sddm.powerOff()
        }
    }
}
