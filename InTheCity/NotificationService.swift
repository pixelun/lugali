import UIKit
import UserNotifications

@MainActor
protocol NotificationProviding: AnyObject {
    func configure()
    func authorizationStatus() async -> UNAuthorizationStatus
    func requestAuthorization() async -> UNAuthorizationStatus
    func showCityBanner(place: Place) async throws
#if DEBUG
    func scheduleSilentBanner(place: Place, delay: TimeInterval) async throws
#endif
    func cancelPendingAndDelivered()
}

@MainActor
final class NotificationService: NSObject, NotificationProviding, UNUserNotificationCenterDelegate {
    static let shared = NotificationService()

#if DEBUG
    static let simulationRequestID = "simulation-city-change"
#endif
    nonisolated static let cityAlertCategoryID = "city-alert"
    nonisolated static let closeActionID = "close"

    override init() {
        super.init()
    }

    func configure() {
        let center = UNUserNotificationCenter.current()
        center.delegate = self

        let closeAction = UNNotificationAction(
            identifier: Self.closeActionID,
            title: "Fechar",
            options: []
        )
        let category = UNNotificationCategory(
            identifier: Self.cityAlertCategoryID,
            actions: [closeAction],
            intentIdentifiers: []
        )
        center.setNotificationCategories([category])
        // Versões anteriores agendavam um UNTimeIntervalNotificationTrigger repetitivo.
        center.removePendingNotificationRequests(withIdentifiers: ["current-city-reminder"])
    }

    func authorizationStatus() async -> UNAuthorizationStatus {
        await UNUserNotificationCenter.current().notificationSettings().authorizationStatus
    }

    func requestAuthorization() async -> UNAuthorizationStatus {
        let center = UNUserNotificationCenter.current()
        do {
            _ = try await center.requestAuthorization(options: [.alert])
        } catch {
            // Status is read below; the UI treats anything other than authorized as refusal.
        }
        return await authorizationStatus()
    }

    func showCityBanner(place: Place) async throws {
        let content = cityContent(place)

        let request = UNNotificationRequest(
            identifier: "current-city-banner",
            content: content,
            trigger: nil
        )
        try await UNUserNotificationCenter.current().add(request)
    }

#if DEBUG
    func scheduleSilentBanner(place: Place, delay: TimeInterval) async throws {
        let content = UNMutableNotificationContent()
        content.title = place.name
        content.body = "\(place.regionCountryLine) · Simulação"
        content.sound = nil
        content.interruptionLevel = .timeSensitive
        content.categoryIdentifier = Self.cityAlertCategoryID

        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: max(delay, 1), repeats: false)
        let request = UNNotificationRequest(
            identifier: Self.simulationRequestID,
            content: content,
            trigger: trigger
        )
        try await UNUserNotificationCenter.current().add(request)
    }
#endif

    func cancelPendingAndDelivered() {
        let center = UNUserNotificationCenter.current()
#if DEBUG
        let identifiers = [Self.simulationRequestID, "current-city-banner", "current-city-reminder"]
#else
        let identifiers = ["current-city-banner", "current-city-reminder"]
#endif
        center.removePendingNotificationRequests(withIdentifiers: identifiers)
        center.removeDeliveredNotifications(withIdentifiers: identifiers)
    }

    private func cityContent(_ place: Place) -> UNMutableNotificationContent {
        let content = UNMutableNotificationContent()
        content.title = place.name
        content.body = place.notificationBody
        content.sound = nil
        content.interruptionLevel = .timeSensitive
        content.categoryIdentifier = Self.cityAlertCategoryID
        return content
    }

    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .list])
    }

    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        if response.actionIdentifier == Self.closeActionID {
            center.removeDeliveredNotifications(
                withIdentifiers: [response.notification.request.identifier]
            )
        }
        completionHandler()
    }
}
