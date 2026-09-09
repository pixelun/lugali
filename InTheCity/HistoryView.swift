import SwiftUI

struct HistoryView: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    @State private var confirmingClear = false
    @ScaledMetric(relativeTo: .body) private var lineSpacing = 6.0
    @ScaledMetric(relativeTo: .body) private var rowVerticalPadding = 10.0

    var body: some View {
        List {
            Text("Cidades identificadas durante o monitoramento")
                .font(.footnote)
                .foregroundStyle(Palette.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .listRowBackground(Palette.background)
                .listRowSeparator(.hidden)
                .overlay(alignment: .bottom) { hairline }

            if model.visits.isEmpty {
                Text("Nenhuma cidade registrada.")
                    .font(.body)
                    .foregroundStyle(Palette.secondary)
                    .listRowBackground(Palette.background)
                    .listRowSeparator(.hidden)
            } else {
                ForEach(model.visits) { visit in visitRow(visit) }
            }
        }
        .listStyle(.plain)
        .listSectionSeparator(.hidden)
        .scrollContentBackground(.hidden)
        .background(Palette.background.ignoresSafeArea())
        .navigationTitle("Histórico")
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            if !model.visits.isEmpty {
                Button("Limpar", role: .destructive) { confirmingClear = true }
            }
        }
        .confirmationDialog("Limpar todo o histórico?", isPresented: $confirmingClear) {
            Button("Limpar histórico", role: .destructive) { model.clearHistory() }
            Button("Cancelar", role: .cancel) {}
        } message: {
            Text("A cidade atual e os avisos continuarão ativos.")
        }
    }

    private func visitRow(_ visit: CityVisit) -> some View {
        VStack(alignment: .leading, spacing: lineSpacing) {
            Text(Formatters.visitDate.string(from: visit.enteredAt))
                .font(.caption)
                .foregroundStyle(Palette.secondary)
            Text(visit.place.name)
                .font(.title3.weight(.semibold))
                .foregroundStyle(Palette.text)
            Text(visit.place.regionCountryLine)
                .font(.body)
                .foregroundStyle(Palette.text)
#if DEBUG
            if visit.isSimulated {
                Text("Simulação")
                    .font(.caption)
                    .foregroundStyle(Palette.secondary)
            }
#endif
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, rowVerticalPadding)
        .listRowBackground(Palette.background)
        .listRowSeparator(.hidden)
        .overlay(alignment: .bottom) { hairline }
        .accessibilityElement(children: .combine)
    }

    private var hairline: some View {
        Rectangle()
            .fill(Palette.hairline)
            .frame(height: 1 / max(displayScale, 1))
            .frame(maxWidth: .infinity)
    }
}
