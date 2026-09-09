import SwiftUI
import UIKit

enum Palette {
    static let background = Color(light: 0xFFFFFF, dark: 0x0B1528)
    static let card = Color(light: 0xF4F6F8, dark: 0x16263E)
    static let text = Color(light: 0x1C1C1E, dark: 0xFFF7E8)
    static let secondary = Color(light: 0x5A554C, dark: 0xA9B6C9)
    static let accent = Color(light: 0x0B57F0, dark: 0x4D8CFF)
    static let hairline = Color(light: 0xE2E5E9, dark: 0x2A3D58)
    static let toggle = Color(hex: 0x0B57F0)
}

extension Color {
    init(hex: UInt32, alpha: Double = 1) {
        self.init(
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: alpha
        )
    }

    init(light: UInt32, dark: UInt32) {
        self.init(
            uiColor: UIColor { trait in
                let hex = trait.userInterfaceStyle == .dark ? dark : light
                return UIColor(
                    red: CGFloat((hex >> 16) & 0xFF) / 255,
                    green: CGFloat((hex >> 8) & 0xFF) / 255,
                    blue: CGFloat(hex & 0xFF) / 255,
                    alpha: 1
                )
            }
        )
    }
}
