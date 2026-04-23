import SwiftUI
import AVFoundation

struct CameraView: View{
    @StateObject private var cameraManager = CameraManager()
    @StateObject private var networkManager = NetworkManager()
    @State private var isTrackingActive = false
    @State private var selectedPersonID: Int? = nil
    @State private var settingsMenu: Bool = false

    // Check if the selected person is still being detected
    private var isPersonStillTracked: Bool{
        guard let id = selectedPersonID else{
            return true
        }
        return networkManager.detectedPeople.contains(where: { $0.id == id })
    }

    var body: some View{
        ZStack{
            // Camera feed as the background for the app
            CameraPreviewView(previewLayer: cameraManager.previewLayer)
                .ignoresSafeArea()

            // Draw bounding boxes over the camera feed
            GeometryReader{ geometry in
                ForEach(networkManager.detectedPeople){ person in
                    // Only show this box if no one is selected or if this is the selected person
                    if selectedPersonID == nil || selectedPersonID == person.id{
                        let rect = boxRect(person: person, in: geometry.size)
                        let isSelected = selectedPersonID == person.id

                        ZStack(alignment: .topLeading){
                            // Draw the box outline
                            Rectangle()
                                .strokeBorder(isSelected ? Color.blue : Color.green, lineWidth: isSelected ? 3 : 2)
                                .frame(width: rect.width, height: rect.height)

                            // Show the tracking ID above the box
                            Text("ID: \(person.id)")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundColor(.white)
                                .padding(4)
                                .background(isSelected ? Color.blue : Color.green)
                                .cornerRadius(4)
                                .offset(y: -24)
                            
                            // show the distance of who we are tracking above the box
                            if let distance = person.distance{
                                Text("\(String(format: "%.1f", distance))m")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                                    .padding(4)
                                    .background(isSelected ? Color.blue : Color.green)
                                    .cornerRadius(4)
                                    .offset(x: rect.width - 40, y: -24)
                            }

                        }
                        .contentShape(Rectangle())
                        .position(x: rect.midX, y: rect.midY)
                        // Tap a box to lock onto that person
                        .onTapGesture{
                            if selectedPersonID == person.id{
                                selectedPersonID = nil
                                networkManager.move = false
                            }else{
                                selectedPersonID = person.id
                            }
                            networkManager.setTrackedPersonID(isTrackingActive ? selectedPersonID : nil)
                        }
                    }
                }
            }
            .ignoresSafeArea()

            // UI overlay
            VStack{
                // Show who we are currently following
                if let id = selectedPersonID{
                    Text("Following ID: \(id)")
                        .font(.headline)
                        .foregroundColor(.white)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(Color.green.opacity(0.8))
                        .cornerRadius(20)
                        .padding(.top, 20)
                }

                // Show lost track of warning
                if selectedPersonID != nil && !isPersonStillTracked{
                    Text("Lost Track of ID: \(selectedPersonID!)")
                        .font(.headline)
                        .foregroundColor(.white)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(Color.red.opacity(0.8))
                        .cornerRadius(20)
                        .padding(.top, 10)
                }

                Spacer()

                HStack{
                    // Settings button
                    Button(action: {
                        settingsMenu = true
                    }){
                        Image(systemName: "gearshape.fill")
                            .font(.title2)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.black.opacity(0.5))
                            .clipShape(Circle())
                            .offset(x: -5)
                    }
                    .sheet(isPresented: $settingsMenu) {
                        SettingsView(networkManager: networkManager)
                            .presentationDetents([.medium])
                    }
                    Spacer()
                    
                    // Start/Stop tracking button
                    Button(action: {
                        isTrackingActive.toggle()
                        if isTrackingActive{
                            // Start sending frames to the backend
                            networkManager.resetTracker()
                            networkManager.startTracking()
                            networkManager.setTrackedPersonID(selectedPersonID)
                            cameraManager.onFrameCaptured = { pixelBuffer in
                                networkManager.sendFrame(pixelBuffer)
                            }
                        }else{
                            // Stop tracking and clear everything
                            cameraManager.onFrameCaptured = nil
                            networkManager.stopTracking()
                            selectedPersonID = nil
                            networkManager.setTrackedPersonID(nil)
                            networkManager.resetTracker()
                            networkManager.move = false
                        }
                    }){
                        Text(isTrackingActive ? "Stop Tracking" : "Start Tracking")
                            .frame(width: 120)
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding(.horizontal, 30)
                            .padding(.vertical, 15)
                            .background(isTrackingActive ? Color.red : Color.green)
                            .cornerRadius(25)
                    }
                    Spacer()
                    // Button to start moving/stop
                    Button(action: {
                        // Add the logic here for starting / stopping the chair
                        networkManager.move.toggle()
                    }){
                        Text(networkManager.move ? "Stop" : "Move")
                            .frame(width: 35)
                            .font(.caption)
                            .foregroundColor(.white)
                            .padding()
                            .background(networkManager.move ? Color.red : Color.green)
                            .clipShape(Circle())
                            .offset(x: 5)
                    }
                    .disabled(selectedPersonID == nil)
                    .opacity(selectedPersonID == nil ? 0.2 : 1.0)
                    }
                    
                // Padding for the button positions
                .padding(.horizontal, 30)
                .padding(.bottom, 30)
            }
        }
        // Launch the camera when the app is open
        .onAppear{
            cameraManager.setupCamera()
            cameraManager.startSession()
            cameraManager.onDepthCaptured={ depthData in
                networkManager.depthData = depthData
            }
        }
        // If the app is closed shut off the camera
        .onDisappear{
            cameraManager.stopSession()
        }
    }

    // Converts the coordinates from the backend into on screen boxes
    private func boxRect(person: DetectedPerson, in size: CGSize) -> CGRect{
        // Top left corner of the box
        let x = person.x1 * size.width
        let y = person.y1 * size.height
        
        // Dimensions of the box
        let width = (person.x2 - person.x1) * size.width
        let height = (person.y2 - person.y1) * size.height
        return CGRect(x: x, y: y, width: width, height: height)
    }
}

// Bridge between SwiftUI and UIKit for camera
struct CameraPreviewView: UIViewRepresentable{
    let previewLayer: AVCaptureVideoPreviewLayer?

    // Creates a container
    func makeUIView(context: Context) -> UIView{
        let view = UIView(frame: .zero)
        view.backgroundColor = .black
        return view
    }

    // Updates when the camera starts
    func updateUIView(_ uiView: UIView, context: Context){
        
        // Add the new camera layer
        if let previewLayer = previewLayer{
            previewLayer.frame = uiView.bounds
            uiView.layer.addSublayer(previewLayer)
        }
    }
}

#Preview{
    CameraView()
}
