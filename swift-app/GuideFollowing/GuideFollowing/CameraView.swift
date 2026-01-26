import SwiftUI
import AVFoundation

struct CameraView: View{
    @StateObject private var cameraManager = CameraManager()    
    @StateObject private var humanDetection = HumanDetection()
    @State private var isTrackingActive = false
    
    var body: some View{
        ZStack{
            // Camera feed as the background for the app
            CameraPreviewView(previewLayer: cameraManager.previewLayer)
                .ignoresSafeArea()
            

            // JUST TEMPORARY FOR TESTING HOW ACCURATE THE HUMAN DETECTION IS
            if isTrackingActive{
                Text("\(humanDetection.peopleCount)")
                    .font(.system(size: 100, weight: .bold))
                    .foregroundColor(.white)
                    .shadow(color: .black, radius: 5)
            }

            // UI overlay
            VStack{
                Spacer()
                
                HStack{
                    // Settings button
                    Button(action: {
                        // IMPLEMENT LATER: actual have the settings button do something
                        print("Settings tapped")
                    }){
                        Image(systemName: "gearshape.fill")
                            .font(.title2)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.black.opacity(0.5))
                            .clipShape(Circle())
                    }
                    
                    Spacer()
                    
                    // Start/stop tracking button
                    Button(action: {
                        isTrackingActive.toggle()
                        if isTrackingActive{
                            // Anytime we receive a frame run the human detection on it
                            cameraManager.onFrameCaptured = { pixelBuffer in
                                humanDetection.detectPeople(in: pixelBuffer)
                            }
                        }else{
                            cameraManager.onFrameCaptured = nil
                            humanDetection.peopleCount = 0
                        }
                    }){
                        Text(isTrackingActive ? "Stop Tracking" :"Start Tracking" )
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding(.horizontal, 30)
                            .padding(.vertical, 15)
                            .background(isTrackingActive ? Color.red : Color.green)
                            .cornerRadius(25)
                    }
                    
                    Spacer()
                    
                    // Camera switch button
                    Button(action: {
                        cameraManager.switchCamera()
                    }){
                        Image(systemName: "camera.rotate.fill")
                            .font(.title2)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.black.opacity(0.5))
                            .clipShape(Circle())
                    }
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
        }
        // If the app is closed shut off the camera
        .onDisappear{
            cameraManager.stopSession()
        }
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
    
    // Updates when the previousLayer changes (when our camera starts or switches)
    func updateUIView(_ uiView: UIView, context: Context){
        // Remove the old camera layers before updating
        uiView.layer.sublayers?.forEach{ $0.removeFromSuperlayer() }
        
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
