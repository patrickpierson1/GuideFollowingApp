import SwiftUI
struct SettingsView: View {
    @ObservedObject var networkManager: NetworkManager
    var body: some View {
        Form{
            Section(header: Text("Connection Type")){
                Picker("Connection", selection: $networkManager.connectionType){
                    Text("WiFi").tag("wifi")
                    Text("USB (Wired)").tag("usb")
                }
                .pickerStyle(.segmented)
                .onChange(of: networkManager.connectionType) { _ in
                    networkManager.updateBaseURL()
                }
            }
            
            Section(header: Text("IP Adress:")){
                TextField("IP", text: $networkManager.baseURL)
           }
       }
    }
}
