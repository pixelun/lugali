import CoreLocation
import Foundation

enum LocationPolicy {
    static let maximumAge: TimeInterval = 120
    static let maximumHorizontalAccuracy: CLLocationAccuracy = 2_000

    static func accepts(_ location: CLLocation, now: Date = Date()) -> Bool {
        location.horizontalAccuracy >= 0
            && location.horizontalAccuracy <= maximumHorizontalAccuracy
            && abs(now.timeIntervalSince(location.timestamp)) <= maximumAge
    }
}

enum ReminderPolicy {
    static let interval: TimeInterval = 10 * 60

    static func shouldNotify(lastNotifiedAt: Date?, now: Date) -> Bool {
        guard let lastNotifiedAt else { return true }
        return now.timeIntervalSince(lastNotifiedAt) >= interval
    }
}

@MainActor
final class LocationService: NSObject, @preconcurrency CLLocationManagerDelegate {
    var onPlace: ((Place) -> Void)?
    var onAuthorizationChange: ((CLAuthorizationStatus) -> Void)?
    var onError: ((String) -> Void)?

    private let manager = CLLocationManager()
    private let geocoder = CLGeocoder()
    private var wantsUpdates = false
    private var lastGeocodedLocation: CLLocation?
    private var isGeocoding = false

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
    }

    var authorizationStatus: CLAuthorizationStatus { manager.authorizationStatus }

    func start() {
        wantsUpdates = true
        switch manager.authorizationStatus {
        case .notDetermined:
            manager.requestAlwaysAuthorization()
        case .authorizedAlways, .authorizedWhenInUse:
            beginUpdates()
        default:
            onAuthorizationChange?(manager.authorizationStatus)
        }
    }

    func stop() {
        wantsUpdates = false
        manager.stopMonitoringSignificantLocationChanges()
        geocoder.cancelGeocode()
        isGeocoding = false
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        onAuthorizationChange?(manager.authorizationStatus)
        guard wantsUpdates else { return }
        if manager.authorizationStatus == .authorizedAlways || manager.authorizationStatus == .authorizedWhenInUse {
            beginUpdates()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard wantsUpdates, let location = locations.last, LocationPolicy.accepts(location) else { return }
        let shouldRefresh = lastGeocodedLocation.map {
            location.distance(from: $0) >= 250 || location.timestamp.timeIntervalSince($0.timestamp) >= 60
        } ?? true
        guard shouldRefresh, !isGeocoding else { return }

        isGeocoding = true
        Task {
            defer { isGeocoding = false }
            do {
                let placemark = try await geocoder.reverseGeocodeLocation(
                    location,
                    preferredLocale: Locale(identifier: "pt_BR")
                ).first
                guard
                    let placemark,
                    let city = placemark.locality ?? placemark.subAdministrativeArea,
                    let region = placemark.administrativeArea,
                    let country = placemark.country
                else {
                    onError?("Não foi possível identificar cidade, estado e país nesta posição.")
                    return
                }
                lastGeocodedLocation = location
                onPlace?(Place(name: city, region: region, country: country, population: nil))
            } catch {
                onError?("Não foi possível identificar a cidade agora. Tentaremos novamente.")
            }
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        guard (error as? CLError)?.code != .locationUnknown else { return }
        onError?("Não foi possível obter a localização atual.")
    }

    private func beginUpdates() {
        manager.startMonitoringSignificantLocationChanges()
        manager.requestLocation()
    }
}
