import CoreLocation
import SwiftUI

struct HomeView: View {
    @Environment(AppModel.self) private var model
    @State private var showingHistory = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    toggleCard
                    statusBlock
                    historyButton
                    currentLocation
                    legalLinks
#if DEBUG
                    simulationPanel
#endif
                }
                .padding(.horizontal, 20)
                .padding(.top, 8)
                .padding(.bottom, 28)
            }
            .background(Palette.background.ignoresSafeArea())
            .navigationTitle("Lugali")
            .navigationBarTitleDisplayMode(.large)
            .navigationDestination(isPresented: $showingHistory) { HistoryView() }
#if DEBUG
            .onChange(of: model.debugRevealHistory, initial: true) { _, open in
                guard open, !showingHistory else { return }
                var transaction = Transaction()
                transaction.disablesAnimations = true
                withTransaction(transaction) { showingHistory = true }
            }
#endif
        }
    }

    private var toggleCard: some View {
        HStack(alignment: .center, spacing: 15) {
            Text("Avisar a cidade")
                .font(.body)
                .foregroundStyle(Palette.text)
                .frame(maxWidth: .infinity, alignment: .leading)
            Toggle("Avisar a cidade", isOn: Binding(
                get: { model.isMonitoring },
                set: { newValue in Task { await model.setMonitoring(newValue) } }
            ))
            .labelsHidden()
            .tint(Palette.toggle)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 17)
        .background(Palette.card, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private var statusBlock: some View {
        VStack(alignment: .leading, spacing: 10) {
            TimelineView(.periodic(from: .now, by: 1)) { context in
                Text(statusText(at: context.date))
                    .font(.subheadline)
                    .foregroundStyle(Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
#if DEBUG
                    .onChange(of: context.date) { _, date in
                        if let pending = model.pendingSimulation, pending.fireDate <= date {
                            model.commitPendingIfDue()
                        }
                    }
#endif
            }

            if needsSettings {
                Button("Abrir Ajustes") { model.openSystemSettings() }
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Palette.accent)
            }
        }
        .padding(.horizontal, 14)
    }

    private var historyButton: some View {
        Button { showingHistory = true } label: {
            HStack {
                Text("Histórico")
                    .font(.body)
                    .foregroundStyle(Palette.text)
                Spacer()
                Text(historyCountLabel)
                    .font(.subheadline)
                    .foregroundStyle(Palette.secondary)
                Image(systemName: "chevron.right")
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(Palette.secondary)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 16)
            .background(Palette.card, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityHint("Abre as cidades registradas nesta viagem")
    }

    private var currentLocation: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Local atual")
                .font(.subheadline)
                .foregroundStyle(Palette.secondary)

            if let place = model.currentPlace {
                Text(place.name)
                    .font(.title2.weight(.semibold))
                    .foregroundStyle(Palette.text)
                Text(place.regionCountryLine)
                    .font(.body)
                    .foregroundStyle(Palette.text)
            } else {
                Text(model.isMonitoring ? "Obtendo localização…" : "Ative os avisos para localizar.")
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(Palette.text)
            }
        }
        .padding(.horizontal, 14)
        .padding(.top, 18)
    }

    private var legalLinks: some View {
        HStack(spacing: 20) {
            Link("Privacidade", destination: LegalPages.privacy)
            Link("Suporte", destination: LegalPages.support)
        }
        .font(.subheadline.weight(.semibold))
        .foregroundStyle(Palette.accent)
        .padding(.horizontal, 14)
        .padding(.top, 8)
        .accessibilityElement(children: .contain)
    }

#if DEBUG
    private var simulationPanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Simulação")
                .font(.headline)
                .foregroundStyle(Palette.text)
            Text("Ferramenta de desenvolvimento. O GPS real permanece ativo quando os avisos estão ligados.")
                .font(.subheadline)
                .foregroundStyle(Palette.secondary)
                .fixedSize(horizontal: false, vertical: true)

            Button(simulationButtonTitle) { Task { await model.simulateCityChange() } }
                .buttonStyle(SimulationButtonStyle())
                .disabled(!model.isMonitoring || hasPendingSimulation)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(Palette.hairline, style: StrokeStyle(lineWidth: 1, dash: [5, 4]))
        )
        .padding(.top, 12)
    }

    private var hasPendingSimulation: Bool {
        guard let pending = model.pendingSimulation else { return false }
        return pending.fireDate > Date()
    }

    private var simulationButtonTitle: String {
        if !model.isMonitoring { return "Ligue os avisos para simular" }
        if hasPendingSimulation { return "Aguardando o aviso simulado" }
        return "Simular mudança de cidade em 8 s"
    }
#endif

    private var historyCountLabel: String {
        switch model.visits.count {
        case 0: return ""
        case 1: return "1 cidade"
        default: return "\(model.visits.count) cidades"
        }
    }

    private var needsSettings: Bool {
        model.authorizationStatus == .denied
            || model.locationAuthorizationStatus == .denied
            || model.locationAuthorizationStatus == .restricted
    }

    private func statusText(at date: Date) -> String {
        if model.notificationSchedulingFailed {
            return "Não foi possível mostrar o aviso. Verifique as notificações em Ajustes."
        }
        if let error = model.locationError { return error }
#if DEBUG
        if let pending = model.pendingSimulation, pending.fireDate > date {
            let seconds = max(1, Int(ceil(pending.fireDate.timeIntervalSince(date))))
            return "Simulação em \(seconds) s."
        }
#endif
        if !model.isMonitoring { return "Desativado. Sem localização e sem avisos." }
        if model.authorizationStatus == .denied { return "Notificações recusadas. Autorize em Ajustes." }
        if model.locationAuthorizationStatus == .denied || model.locationAuthorizationStatus == .restricted {
            return "Localização recusada. Autorize em Ajustes."
        }
        if model.locationAuthorizationStatus == .notDetermined {
            return "Aguardando autorização de localização."
        }
        if model.currentPlace == nil { return "Buscando uma localização confiável…" }
        return "Ativado. Aviso silencioso quando houver uma localização nova e confiável, com intervalo mínimo de cerca de 10 minutos."
    }
}

private enum LegalPages {
    static let privacy = URL(string: "https://pixelun.github.io/lugali/privacidade.html")!
    static let support = URL(string: "https://pixelun.github.io/lugali/suporte.html")!
}

#if DEBUG
private struct SimulationButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.body.weight(.semibold))
            .foregroundStyle(isEnabled ? Color.white : Palette.secondary)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 13)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(isEnabled ? Palette.accent : Palette.hairline)
            )
            .opacity(configuration.isPressed ? 0.85 : 1)
    }
}
#endif
