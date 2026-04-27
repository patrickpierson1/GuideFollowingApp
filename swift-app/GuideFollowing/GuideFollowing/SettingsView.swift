import SwiftUI
struct SettingsView: View {
    @ObservedObject var networkManager: NetworkManager
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20){
            HStack{
                Text("Settings")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Spacer()
                
                // X button to close out of the settings menu
                Button(action: { dismiss() }){
                    Image(systemName: "xmark.circle.fill")
                        .font(.title)
                        .foregroundColor(.gray)
                }
            }
            .padding(.top, 20)
            
            HStack{
                Text("Backend Status:")
                    .font(.subheadline)
                Spacer()
                Circle()
                    .fill(networkManager.isConnected ? Color.green : Color.red)
                    .frame(width: 10, height: 10)
            }
            
            VStack(alignment: .leading, spacing: 8){
                Text("IP Address")
                    .font(.subheadline)
                    .foregroundColor(.white)
                TextField("IP", text: $networkManager.baseURL)
                    .padding(10)
                    .background(Color(.gray))
                    .cornerRadius(8)
            }
            
            // Slider so the user can control what distance they want to stop at
            VStack(alignment: .leading, spacing: 8){
                Text("Stopping Distance: \(String(format: "%.1f", networkManager.stoppingDistance))m")
                    .font(.subheadline)
                    .foregroundColor(.white)
                Slider(value: $networkManager.stoppingDistance, in: 2.0...4.0, step: 0.5)
            }
            
            // Slider for speed control
            VStack(alignment: .leading, spacing: 8){
                Text("Speed: \(String(format: "%.1f", networkManager.maxSpeed))")
                    .font(.subheadline)
                    .foregroundColor(.white)
                Slider(value: $networkManager.maxSpeed, in: 0.5...1.5, step: 0.1)
            }
                
            Button("Reset Tracker"){
                networkManager.resetTracker()
            }
            .font(.headline)
            .foregroundColor(.white)
            .padding(.horizontal, 30)
            .padding(.vertical, 15)
            .background(Color.red)
            .cornerRadius(25)
            .frame(maxWidth: .infinity, alignment: .center)
            .padding(.top, 10)
            
            Spacer()
            
        }
        .padding(.horizontal, 20)
    }
}
