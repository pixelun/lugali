import Foundation

struct Place: Codable, Equatable, Hashable, Identifiable {
    var id: String { "\(name)|\(region)|\(country)" }

    let name: String
    let region: String
    let country: String
    let population: Int?

    var regionCountryLine: String {
        "\(region) · \(country)"
    }

    var populationLine: String? {
        guard let population else { return nil }
        let formatted = Formatters.population.string(from: NSNumber(value: population)) ?? "\(population)"
        return "População: \(formatted) habitantes"
    }

    var notificationBody: String { regionCountryLine }

#if DEBUG
    var fictionalPopulationLine: String? {
        populationLine?.replacingOccurrences(of: "População:", with: "População fictícia:")
    }
#endif
}

struct CityVisit: Codable, Equatable, Identifiable {
    let id: UUID
    let place: Place
    let enteredAt: Date
    let isSimulated: Bool
}

#if DEBUG
struct PendingSimulation: Codable, Equatable {
    let place: Place
    let fireDate: Date
}

enum SimulatedPlaces {
    static let sequence: [Place] = [
        Place(name: "Santa Terezinha de Itaipu", region: "Paraná", country: "Brasil", population: 25_000),
        Place(name: "Foz do Iguaçu", region: "Paraná", country: "Brasil", population: 280_000),
        Place(name: "Puerto Iguazú", region: "Misiones", country: "Argentina", population: 80_000)
    ]

    static func next(after current: Place?) -> Place {
        guard let current, let index = sequence.firstIndex(of: current) else {
            return sequence[0]
        }
        return sequence[(index + 1) % sequence.count]
    }
}
#endif

enum Formatters {
    static let visitDate: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "pt_BR")
        formatter.dateFormat = "dd MMM yyyy · HH:mm"
        return formatter
    }()

    static let population: NumberFormatter = {
        let formatter = NumberFormatter()
        formatter.locale = Locale(identifier: "pt_BR")
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = 0
        return formatter
    }()
}
