import SwiftUI
import AVFoundation

struct CameraView: View{
    @StateObject private var cameraManager = CameraManager()
    
    var body: some View{
        ZStack{
            // Camera preview as background
            CameraPreviewView(previewLayer: cameraManager.previewLayer)
                .ignoresSafeArea()
            
            // UI Controls overlay
            VStack{
                Spacer()
                
                // Bottom controls
                HStack{
                    // Settings button (left)
                    Button(action: {
                        // TODO: Open settings
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
                    
                    // Start/Stop tracking button (center)
                    Button(action: {
                        // TODO: Toggle tracking
                        print("Tracking toggled")
                    }){
                        Text("Start Tracking")
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding(.horizontal, 30)
                            .padding(.vertical, 15)
                            .background(Color.green)
                            .cornerRadius(25)
                    }
                    
                    Spacer()
                    
                    // Camera switch button (right)
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
                .padding(.horizontal, 30)
                .padding(.bottom, 30)
            }
        }
        .onAppear{
            cameraManager.setupCamera()
            cameraManager.startSession()
        }
        .onDisappear{
            cameraManager.stopSession()
        }
    }
}

// MARK: - Camera Preview View
struct CameraPreviewView: UIViewRepresentable{
    let previewLayer: AVCaptureVideoPreviewLayer?
    
    func makeUIView(context: Context) -> UIView{
        let view = UIView(frame: .zero)
        view.backgroundColor = .black
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context){
        // Remove old layer if exists
        uiView.layer.sublayers?.forEach{ $0.removeFromSuperlayer() }
        
        // Add new preview layer
        if let previewLayer = previewLayer{
            previewLayer.frame = uiView.bounds
            uiView.layer.addSublayer(previewLayer)
        }
    }
}

#Preview{
    CameraView()
}
