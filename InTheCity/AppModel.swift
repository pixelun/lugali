import CoreLocation
import Foundation
import UIKit
import UserNotifications

@MainActor
@Observable
final class AppModel {
#if DEBUG
    let simulationDelay: TimeInterval = 8
#endif

    private let store: VisitStore
    private let notifications: any NotificationProviding
    private let location: LocationService
    private var monitoringIntent = false
    private var isSchedulingReminder = false

    var isMonitoring = false
    var visits: [CityVisit] = []
    var currentPlace: Place?
    var locationAuthorizationStatus: CLAuthorizationStatus = .notDetermined
    var locationError: String?
    var notificationSchedulingFailed = false
#if DEBUG
    var pendingSimulation: PendingSimulation?
#endif
    var authorizationStatus: UNAuthorizationStatus = .notDetermined
    var permissionDenied = false
#if DEBUG
    var debugRevealHistory = false
#endif

    init(
        store: VisitStore = VisitStore(),
        notifications: (any NotificationProviding)? = nil,
        location: LocationService? = nil
    ) {
        self.store = store
        self.notifications = notifications ?? NotificationService.shared
        let resolvedLocation = location ?? LocationService()
        self.location = resolvedLocation
        syncFromStore()
        monitoringIntent = isMonitoring
        locationAuthorizationStatus = resolvedLocation.authorizationStatus
        resolvedLocation.onAuthorizationChange = { [weak self] status in
            self?.locationAuthorizationStatus = status
        }
        resolvedLocation.onError = { [weak self] message in
            self?.locationError = message
        }
        resolvedLocation.onPlace = { [weak self] place in
            self?.received(place)
        }
#if DEBUG
        applyDebugLaunchArguments()
#endif
    }

    func start() async {
        notifications.configure()
        authorizationStatus = await notifications.authorizationStatus()
#if DEBUG
        _ = store.commitPendingIfDue()
#endif
        syncFromStore()
        if isMonitoring {
            location.start()
        }
    }

    func refreshOnForeground() async {
        authorizationStatus = await notifications.authorizationStatus()
        locationAuthorizationStatus = location.authorizationStatus
#if DEBUG
        _ = store.commitPendingIfDue()
#endif
        syncFromStore()
        switch authorizationStatus {
        case .authorized, .provisional, .ephemeral:
            permissionDenied = false
        case .denied:
            permissionDenied = true
        default:
            break
        }
    }

    func setMonitoring(_ on: Bool) async {
        monitoringIntent = on
        notificationSchedulingFailed = false
        if !on {
            permissionDenied = false
            notifications.cancelPendingAndDelivered()
            location.stop()
            store.setMonitoring(false)
            syncFromStore()
            return
        }

        let status = await notifications.requestAuthorization()
        guard monitoringIntent else { return }
        authorizationStatus = status
        switch status {
        case .authorized, .provisional, .ephemeral:
            permissionDenied = false
            store.setMonitoring(true)
            location.start()
        default:
            permissionDenied = true
            notifications.cancelPendingAndDelivered()
            store.setMonitoring(false)
        }
        syncFromStore()
    }

#if DEBUG
    func simulateCityChange() async {
        guard isMonitoring else { return }
        notifications.cancelPendingAndDelivered()
        let place = SimulatedPlaces.next(after: currentPlace)
        let fireDate = Date().addingTimeInterval(simulationDelay)
        do {
            try await notifications.scheduleSilentBanner(place: place, delay: simulationDelay)
            guard monitoringIntent, isMonitoring else {
                notifications.cancelPendingAndDelivered()
                return
            }
            store.queueSimulation(place, fireDate: fireDate)
            notificationSchedulingFailed = false
            syncFromStore()
        } catch {
            notificationSchedulingFailed = true
        }
    }

    func commitPendingIfDue() {
        _ = store.commitPendingIfDue()
        syncFromStore()
    }
#endif

    func openSystemSettings() {
        guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
        UIApplication.shared.open(url)
    }

    func clearHistory() {
        store.clearHistory()
        syncFromStore()
    }

    private func syncFromStore() {
        isMonitoring = store.isMonitoring
        visits = store.visits
        currentPlace = store.currentPlace
#if DEBUG
        pendingSimulation = store.pendingSimulation
#endif
    }

    private func received(_ place: Place) {
        guard isMonitoring else { return }
        locationError = nil
        _ = store.recordArrival(place, isSimulated: false)
        syncFromStore()

        let now = Date()
        guard ReminderPolicy.shouldNotify(lastNotifiedAt: store.lastNotificationAt, now: now),
              !isSchedulingReminder else { return }
        isSchedulingReminder = true
        Task {
            defer { isSchedulingReminder = false }
            do {
                try await notifications.showCityBanner(place: place)
                guard isMonitoring else { return }
                store.markNotified(at: now)
                notificationSchedulingFailed = false
            } catch {
                notificationSchedulingFailed = true
            }
        }
    }

#if DEBUG
    private func applyDebugLaunchArguments() {
        let arguments = ProcessInfo.processInfo.arguments
        if arguments.contains("-DemoScreenshots") {
            store.installScreenshotDemo()
            syncFromStore()
        }
        debugRevealHistory = arguments.contains("-DemoShowHistory")
    }
#endif
}
