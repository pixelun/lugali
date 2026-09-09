import Foundation
import OSLog

final class VisitStore {
    private static let logger = Logger(subsystem: "com.pixelun.Lugali", category: "VisitStore")
    private let defaults: UserDefaults
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder
    private var unreadableKeys: Set<String> = []
    private(set) var persistenceError: String?

    private enum Key {
        static let visits = "visits"
        static let monitoring = "isMonitoring"
        static let current = "currentPlace"
        static let lastNotification = "lastNotificationAt"
#if DEBUG
        static let pending = "pendingSimulation"
#endif
    }

    private(set) var isMonitoring = false
    private(set) var visits: [CityVisit] = []
    private(set) var currentPlace: Place?
    private(set) var lastNotificationAt: Date?
#if DEBUG
    private(set) var pendingSimulation: PendingSimulation?
#endif

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .secondsSince1970
        self.encoder = encoder
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .secondsSince1970
        self.decoder = decoder

        isMonitoring = defaults.bool(forKey: Key.monitoring)
        visits = decode([CityVisit].self, key: Key.visits) ?? []
        visits.sort { $0.enteredAt > $1.enteredAt }
        currentPlace = decode(Place.self, key: Key.current)
        lastNotificationAt = defaults.object(forKey: Key.lastNotification) as? Date
#if DEBUG
        pendingSimulation = decode(PendingSimulation.self, key: Key.pending)
#endif
    }

    func setMonitoring(_ on: Bool) {
        isMonitoring = on
#if DEBUG
        if !on {
            pendingSimulation = nil
        }
#endif
        persist()
    }

#if DEBUG
    func queueSimulation(_ place: Place, fireDate: Date) {
        guard isMonitoring else { return }
        pendingSimulation = PendingSimulation(place: place, fireDate: fireDate)
        persist()
    }

    func cancelPending() {
        pendingSimulation = nil
        persist()
    }

    @discardableResult
    func commitPendingIfDue(now: Date = Date()) -> CityVisit? {
        guard let pending = pendingSimulation, pending.fireDate <= now else { return nil }
        pendingSimulation = nil
        let visit = recordArrival(pending.place, at: pending.fireDate, isSimulated: true)
        persist()
        return visit
    }
#endif

    @discardableResult
    func recordArrival(_ place: Place, at date: Date = Date(), isSimulated: Bool) -> CityVisit? {
        guard isMonitoring else { return nil }
        if currentPlace?.id == place.id {
            currentPlace = place
            persist()
            return nil
        }
        let visit = CityVisit(id: UUID(), place: place, enteredAt: date, isSimulated: isSimulated)
        visits.insert(visit, at: 0)
        visits.sort { $0.enteredAt > $1.enteredAt }
        currentPlace = place
        persist()
        return visit
    }

    func markNotified(at date: Date) {
        lastNotificationAt = date
        persist()
    }

    func clearHistory() {
        visits.removeAll()
        persist()
    }

#if DEBUG
    /// Fixture for Simulator screenshots. Not GPS. Not used in Release.
    func installScreenshotDemo() {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "America/Sao_Paulo") ?? .current
        func at(hour: Int, minute: Int) -> Date {
            var components = DateComponents()
            components.year = 2026
            components.month = 9
            components.day = 6
            components.hour = hour
            components.minute = minute
            return calendar.date(from: components) ?? Date()
        }
        let places = SimulatedPlaces.sequence
        visits = [
            CityVisit(id: UUID(), place: places[2], enteredAt: at(hour: 9, minute: 41), isSimulated: true),
            CityVisit(id: UUID(), place: places[1], enteredAt: at(hour: 8, minute: 50), isSimulated: true),
            CityVisit(id: UUID(), place: places[0], enteredAt: at(hour: 8, minute: 10), isSimulated: true)
        ]
        currentPlace = places[2]
        pendingSimulation = nil
        isMonitoring = true
        persist()
    }
#endif

    private func persist() {
        defaults.set(isMonitoring, forKey: Key.monitoring)
        encode(visits, key: Key.visits)
        if let currentPlace {
            encode(currentPlace, key: Key.current)
        } else {
            defaults.removeObject(forKey: Key.current)
        }
        if let lastNotificationAt {
            defaults.set(lastNotificationAt, forKey: Key.lastNotification)
        } else {
            defaults.removeObject(forKey: Key.lastNotification)
        }
#if DEBUG
        if let pendingSimulation {
            encode(pendingSimulation, key: Key.pending)
        } else {
            defaults.removeObject(forKey: Key.pending)
        }
#endif
    }

    private func encode<T: Encodable>(_ value: T, key: String) {
        guard !unreadableKeys.contains(key) else { return }
        do {
            let data = try encoder.encode(value)
            defaults.set(data, forKey: key)
        } catch {
            persistenceError = "Não foi possível salvar os dados locais."
            Self.logger.error("Falha ao salvar \(key, privacy: .public): \(error.localizedDescription, privacy: .public)")
        }
    }

    private func decode<T: Decodable>(_ type: T.Type, key: String) -> T? {
        guard let data = defaults.data(forKey: key) else { return nil }
        do {
            return try decoder.decode(type, from: data)
        } catch {
            unreadableKeys.insert(key)
            persistenceError = "Os dados locais não puderam ser lidos e foram preservados."
            Self.logger.error("Falha ao ler \(key, privacy: .public); dados preservados: \(error.localizedDescription, privacy: .public)")
            return nil
        }
    }
}
