import CoreLocation
import Foundation
import Testing
import UserNotifications
@testable import InTheCity

struct VisitStoreTests {
    @Test func desligadoNaoRegistra() {
        let store = VisitStore(defaults: isolatedDefaults())
        store.setMonitoring(false)

        let recorded = store.recordArrival(Self.foz, isSimulated: true)

        #expect(recorded == nil)
        #expect(store.visits.isEmpty)
        #expect(store.currentPlace == nil)
    }

    @Test func historicoPreservaAoDesligar() {
        let store = VisitStore(defaults: isolatedDefaults())
        store.setMonitoring(true)

        #expect(store.recordArrival(Self.foz, isSimulated: true) != nil)
        #expect(store.recordArrival(Self.iguazu, isSimulated: true) != nil)
        #expect(store.visits.count == 2)
        #expect(store.visits.first?.place == Self.iguazu)

        store.setMonitoring(false)

        #expect(store.isMonitoring == false)
        #expect(store.visits.count == 2)
        #expect(store.visits.map(\.place.name) == ["Puerto Iguazú", "Foz do Iguaçu"])
        #expect(store.recordArrival(Self.santa, isSimulated: true) == nil)
        #expect(store.visits.count == 2)
        #expect(store.currentPlace == Self.iguazu)
    }

    @Test func historicoPersisteDepoisDeDesligar() {
        let defaults = isolatedDefaults()
        let store = VisitStore(defaults: defaults)
        store.setMonitoring(true)
        #expect(store.recordArrival(Self.foz, isSimulated: true) != nil)
        store.setMonitoring(false)

        let reloaded = VisitStore(defaults: defaults)
        #expect(reloaded.isMonitoring == false)
        #expect(reloaded.visits.count == 1)
        #expect(reloaded.visits.first?.place == Self.foz)
        #expect(reloaded.visits.first?.isSimulated == true)
        #expect(reloaded.recordArrival(Self.iguazu, isSimulated: true) == nil)
        #expect(reloaded.visits.count == 1)
    }

    @Test func desligarCancelaSimulacaoPendenteSemRegistrar() {
        let store = VisitStore(defaults: isolatedDefaults())
        store.setMonitoring(true)
        store.queueSimulation(Self.iguazu, fireDate: Date().addingTimeInterval(8))
        #expect(store.pendingSimulation?.place == Self.iguazu)

        store.setMonitoring(false)

        #expect(store.pendingSimulation == nil)
        #expect(store.visits.isEmpty)
        #expect(store.commitPendingIfDue() == nil)
    }

    @Test func historicoCorrompidoNaoEhSobrescrito() {
        let defaults = isolatedDefaults()
        let original = Data([0xFF])
        defaults.set(original, forKey: "visits")
        let store = VisitStore(defaults: defaults)

        store.setMonitoring(true)

        #expect(store.persistenceError != nil)
        #expect(defaults.data(forKey: "visits") == original)
    }

    @Test func mesmaCidadeNaoDuplicaHistorico() {
        let store = VisitStore(defaults: isolatedDefaults())
        store.setMonitoring(true)

        #expect(store.recordArrival(Self.foz, isSimulated: false) != nil)
        #expect(store.recordArrival(Self.foz, isSimulated: false) == nil)
        #expect(store.visits.count == 1)
    }

    @Test func limparHistoricoPreservaCidadeEMonitoramento() {
        let store = VisitStore(defaults: isolatedDefaults())
        store.setMonitoring(true)
        _ = store.recordArrival(Self.foz, isSimulated: false)

        store.clearHistory()

        #expect(store.visits.isEmpty)
        #expect(store.currentPlace == Self.foz)
        #expect(store.isMonitoring)
    }

    @Test func avisoRespeitaIntervaloDeDezMinutos() {
        let start = Date(timeIntervalSince1970: 1_000)

        #expect(ReminderPolicy.shouldNotify(lastNotifiedAt: nil, now: start))
        #expect(!ReminderPolicy.shouldNotify(lastNotifiedAt: start, now: start.addingTimeInterval(599)))
        #expect(ReminderPolicy.shouldNotify(lastNotifiedAt: start, now: start.addingTimeInterval(600)))
    }

    @Test func rejeitaLocalizacaoAntigaOuImprecisa() {
        let now = Date(timeIntervalSince1970: 1_000)
        let recent = CLLocation(
            coordinate: CLLocationCoordinate2D(latitude: -25.4, longitude: -49.2),
            altitude: 0,
            horizontalAccuracy: 50,
            verticalAccuracy: 50,
            timestamp: now
        )
        let old = CLLocation(
            coordinate: recent.coordinate,
            altitude: 0,
            horizontalAccuracy: 50,
            verticalAccuracy: 50,
            timestamp: now.addingTimeInterval(-121)
        )
        let inaccurate = CLLocation(
            coordinate: recent.coordinate,
            altitude: 0,
            horizontalAccuracy: 2_001,
            verticalAccuracy: 50,
            timestamp: now
        )

        #expect(LocationPolicy.accepts(recent, now: now))
        #expect(!LocationPolicy.accepts(old, now: now))
        #expect(!LocationPolicy.accepts(inaccurate, now: now))
    }

    @Test @MainActor func desligarVenceAtivacaoPendente() async {
        let notifications = FakeNotifications(blockAuthorization: true)
        let model = AppModel(store: VisitStore(defaults: isolatedDefaults()), notifications: notifications)
        let activation = Task { await model.setMonitoring(true) }
        while !notifications.hasPendingAuthorization { await Task.yield() }

        await model.setMonitoring(false)
        notifications.resolveAuthorization(.authorized)
        await activation.value

        #expect(model.isMonitoring == false)
    }

    @Test @MainActor func falhaAoAgendarNaoCriaHistorico() async {
        let notifications = FakeNotifications(scheduleShouldFail: true)
        let model = AppModel(store: VisitStore(defaults: isolatedDefaults()), notifications: notifications)
        await model.setMonitoring(true)

        await model.simulateCityChange()

        #expect(model.pendingSimulation == nil)
        #expect(model.visits.isEmpty)
        #expect(model.notificationSchedulingFailed)
    }

#if DEBUG
    @Test func demoDeScreenshotFicaMarcadaComoSimulacao() {
        let store = VisitStore(defaults: isolatedDefaults())
        store.installScreenshotDemo()

        #expect(!store.visits.isEmpty)
        let allSimulated = store.visits.allSatisfy(\.isSimulated)
        #expect(allSimulated)
        #expect(store.currentPlace == Self.iguazu)
        #expect(store.visits.map(\.place.name) == ["Puerto Iguazú", "Foz do Iguaçu", "Santa Terezinha de Itaipu"])
    }
#endif

    private func isolatedDefaults() -> UserDefaults {
        let suite = "InTheCityTests.\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suite)!
        defaults.removePersistentDomain(forName: suite)
        return defaults
    }

    private static let santa = SimulatedPlaces.sequence[0]
    private static let foz = SimulatedPlaces.sequence[1]
    private static let iguazu = SimulatedPlaces.sequence[2]
}

@MainActor
private final class FakeNotifications: NotificationProviding {
    private var authorizationContinuation: CheckedContinuation<UNAuthorizationStatus, Never>?
    private let blockAuthorization: Bool
    private let scheduleShouldFail: Bool

    var hasPendingAuthorization: Bool { authorizationContinuation != nil }

    init(blockAuthorization: Bool = false, scheduleShouldFail: Bool = false) {
        self.blockAuthorization = blockAuthorization
        self.scheduleShouldFail = scheduleShouldFail
    }

    func configure() {}
    func authorizationStatus() async -> UNAuthorizationStatus { .authorized }

    func requestAuthorization() async -> UNAuthorizationStatus {
        guard blockAuthorization else { return .authorized }
        return await withCheckedContinuation { authorizationContinuation = $0 }
    }

    func showCityBanner(place: Place) async throws {
        if scheduleShouldFail { throw SchedulingError.failed }
    }

    func resolveAuthorization(_ status: UNAuthorizationStatus) {
        authorizationContinuation?.resume(returning: status)
        authorizationContinuation = nil
    }

    func scheduleSilentBanner(place: Place, delay: TimeInterval) async throws {
        if scheduleShouldFail { throw SchedulingError.failed }
    }

    func cancelPendingAndDelivered() {}

    private enum SchedulingError: Error { case failed }
}
